# SPDX-License-Identifier: Apache-2.0
"""Quorum consensus scenario factory — quorum-aware leader/follower agents.

Creates agents that use the NandaQuorum protocol for group consensus.
Agents emit trace messages in the format expected by the built-in
consensus validators:
  - ``propose:{round}:{value}``     — leader proposes a value
  - ``vote:{round}:accept|reject``  — follower votes
  - ``result:{round}:committed|aborted:{accepts}/{total}``  — leader announces
  - ``result:{round}:committed:{accepts}/{total}:{value}``  — with value for validity check

Example::

    agents = quorum_consensus_factory(config, plugins)
"""

from __future__ import annotations

from typing import Any

from nest_core.scenario import ScenarioConfig
from nest_core.sim.agent import AgentContext, StateMachineAgent
from nest_core.types import AgentId

from .quorum import Quorum


class QuorumLeaderAgent(StateMachineAgent):
    """Leader that proposes values and collects votes using 2/3 quorum.

    On start, the leader proposes a random value to all followers.
    Votes are collected; if 2/3 quorum of accept votes is reached,
    the value is committed. Otherwise, the leader re-proposes in
    the next round (up to max_rounds).

    Example::

        leader = QuorumLeaderAgent(AgentId("leader-0"), 19, rounds=5, quorum=2/3)
    """

    def __init__(
        self,
        agent_id: AgentId,
        num_followers: int,
        rounds: int = 5,
        quorum: float = 2 / 3,
    ) -> None:
        self._id = agent_id
        self._num_followers = num_followers
        self._rounds = rounds
        self._quorum = quorum
        self._round = 0
        self._votes: dict[str, list[str]] = {}
        self._decided: set[str] = set()
        self._proposed_values: dict[str, int] = {}

    async def on_start(self, ctx: AgentContext) -> None:
        """Propose the first value to all followers."""
        self._round = 1
        value = ctx.rng.randint(1, 100)
        rnd_str = str(self._round)
        self._proposed_values[rnd_str] = value
        for i in range(self._num_followers):
            follower = AgentId(f"follower-{i}")
            await ctx.send(follower, f"propose:{rnd_str}:{value}".encode())

    async def on_message(
        self, ctx: AgentContext, sender: AgentId, payload: bytes
    ) -> None:
        """Collect votes; when all followers have voted, check quorum."""
        msg = payload.decode("utf-8", errors="replace")
        if not msg.startswith("vote:"):
            return
        parts = msg.split(":")
        if len(parts) < 3:
            return
        rnd, vote = parts[1], parts[2]
        self._votes.setdefault(rnd, []).append(vote)

        # Wait for all followers to vote (or as many as we'll get)
        if len(self._votes[rnd]) < self._num_followers:
            return
        if rnd in self._decided:
            return
        self._decided.add(rnd)

        # Use proper 2/3 quorum check
        accepts = sum(1 for v in self._votes[rnd] if v == "accept")
        total = len(self._votes[rnd])
        total_nodes = total + 1  # followers + leader

        # Quorum: need at least threshold accepts out of total votes
        threshold = Quorum.threshold(total_nodes)
        # Leader counts as an accept vote too
        effective_accepts = accepts + 1
        reached = effective_accepts >= threshold

        result = "committed" if reached else "aborted"
        value = self._proposed_values.get(rnd, 0)

        # Broadcast result to all followers
        for i in range(self._num_followers):
            follower = AgentId(f"follower-{i}")
            await ctx.send(
                follower,
                f"result:{rnd}:{result}:{accepts}/{total}:{value}".encode(),
            )

        # If not committed and rounds remain, propose again
        self._round += 1
        if self._round <= self._rounds and not reached:
            new_value = ctx.rng.randint(1, 100)
            new_rnd = str(self._round)
            self._proposed_values[new_rnd] = new_value
            for i in range(self._num_followers):
                follower = AgentId(f"follower-{i}")
                await ctx.send(
                    follower, f"propose:{new_rnd}:{new_value}".encode()
                )


class QuorumFollowerAgent(StateMachineAgent):
    """Follower that votes on proposals from the leader.

    Votes "accept" with ~70% probability (randomly), simulating
    agents that may disagree. The accept probability is designed to
    make quorum reachable in most rounds but create interesting
    failure dynamics under message drops.

    Example::

        follower = QuorumFollowerAgent(AgentId("follower-0"), AgentId("leader-0"))
    """

    def __init__(
        self,
        agent_id: AgentId,
        leader: AgentId,
        accept_probability: float = 0.7,
    ) -> None:
        self._id = agent_id
        self._leader = leader
        self._accept_probability = accept_probability

    async def on_message(
        self, ctx: AgentContext, sender: AgentId, payload: bytes
    ) -> None:
        """Receive a proposal and respond with a vote."""
        msg = payload.decode("utf-8", errors="replace")
        if not msg.startswith("propose:"):
            return
        parts = msg.split(":")
        if len(parts) < 3:
            return
        rnd = parts[1]
        vote = "accept" if ctx.rng.random() < self._accept_probability else "reject"
        await ctx.send(self._leader, f"vote:{rnd}:{vote}".encode())


def quorum_consensus_factory(
    config: ScenarioConfig,
    plugins: dict[str, Any],
) -> dict[AgentId, StateMachineAgent]:
    """Create quorum consensus leader and follower agents.

    Reads ``task.config.rounds``, ``task.config.quorum``, and
    ``task.config.accept_probability`` from the scenario config.

    Example::

        agents = quorum_consensus_factory(config, plugins)
    """
    task_config = config.task.config
    rounds = task_config.get("rounds", 5)
    quorum = task_config.get("quorum", 2 / 3)
    accept_prob = task_config.get("accept_probability", 0.7)

    agents: dict[AgentId, StateMachineAgent] = {}

    # Determine follower count from roles or total agent count
    if config.agents.roles:
        follower_count = 0
        for role in config.agents.roles:
            if role.name == "follower":
                follower_count = role.count
        if follower_count == 0:
            follower_count = config.agents.count - 1
    else:
        follower_count = config.agents.count - 1

    leader_id = AgentId("leader-0")
    agents[leader_id] = QuorumLeaderAgent(
        leader_id,
        num_followers=follower_count,
        rounds=rounds,
        quorum=quorum,
    )

    for i in range(follower_count):
        aid = AgentId(f"follower-{i}")
        agents[aid] = QuorumFollowerAgent(
            aid,
            leader=leader_id,
            accept_probability=accept_prob,
        )

    return agents
