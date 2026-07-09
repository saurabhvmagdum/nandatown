# SPDX-License-Identifier: Apache-2.0
"""BFT quorum consensus scenario factory — quorum-aware leader/follower agents.

Creates agents that use the NandaQuorum BFT protocol for group consensus.
Supports Byzantine fault tolerance: a configurable fraction of followers
act as Byzantine agents, sending equivocating or conflicting votes.

Agents emit trace messages in the format expected by the built-in
consensus validators:

- ``propose:{round}:{value}``     — leader proposes a value
- ``vote:{round}:accept|reject``  — follower votes
- ``result:{round}:committed|aborted:{accepts}/{total}``  — leader announces
- ``result:{round}:committed:{accepts}/{total}:{value}``  — with value for validity check

All randomness uses the seeded ``ctx.rng`` — no ``time.time()``,
``uuid.uuid4()``, or ``random.random()`` calls.  The scenario is
fully deterministic under identical seeds.

Example::

    agents = quorum_consensus_factory(config, plugins)
"""

from __future__ import annotations

from typing import Any

from nest_core.scenario import ScenarioConfig
from nest_core.sim.agent import AgentContext, StateMachineAgent
from nest_core.types import AgentId
from nest_plugins_reference.coordination.quorum import Quorum


class QuorumLeaderAgent(StateMachineAgent):
    """Leader that proposes values and collects votes using BFT 2f+1 quorum.

    On start, the leader proposes a random value to all followers.
    Votes are collected; if a BFT quorum (``2f+1``) of accept votes
    is reached (excluding equivocating voters), the value is committed.
    Otherwise, the leader re-proposes in the next round (up to
    ``max_rounds``).

    Example::

        leader = QuorumLeaderAgent(AgentId("leader-0"), 6, rounds=5)
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
        self._votes: dict[str, list[tuple[str, str]]] = {}  # round -> [(voter, vote)]
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
        """Collect votes; when all followers have voted, check BFT quorum.

        Detects equivocation (same voter sending conflicting votes) and
        excludes equivocating voters from the quorum count.
        """
        msg = payload.decode("utf-8", errors="replace")
        if not msg.startswith("vote:"):
            return
        parts = msg.split(":")
        if len(parts) < 3:
            return
        rnd, vote = parts[1], parts[2]
        voter_id = str(sender)

        self._votes.setdefault(rnd, []).append((voter_id, vote))

        # Wait for all followers to vote (or as many as we'll get)
        if len(self._votes[rnd]) < self._num_followers:
            return
        if rnd in self._decided:
            return
        self._decided.add(rnd)

        # Detect equivocation: voters who sent multiple different votes
        voter_values: dict[str, set[str]] = {}
        for vid, v in self._votes[rnd]:
            voter_values.setdefault(vid, set()).add(v)
        equivocators = {vid for vid, vals in voter_values.items() if len(vals) > 1}

        # Count genuine (non-equivocating) accept votes
        genuine_accepts = 0
        genuine_total = 0
        seen_voters: set[str] = set()
        for vid, v in self._votes[rnd]:
            if vid in equivocators or vid in seen_voters:
                continue
            seen_voters.add(vid)
            genuine_total += 1
            if v == "accept":
                genuine_accepts += 1

        # BFT quorum: need 2f+1 accepts (leader counts as an accept vote too)
        total_nodes = genuine_total + 1  # genuine followers + leader
        threshold = Quorum.threshold(total_nodes + len(equivocators))
        effective_accepts = genuine_accepts + 1  # leader's own vote
        reached = effective_accepts >= threshold

        result = "committed" if reached else "aborted"
        value = self._proposed_values.get(rnd, 0)

        # Broadcast result to all followers
        for i in range(self._num_followers):
            follower = AgentId(f"follower-{i}")
            await ctx.send(
                follower,
                f"result:{rnd}:{result}:{genuine_accepts}/{genuine_total}:{value}".encode(),
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
    """Honest follower that votes on proposals from the leader.

    Votes ``"accept"`` with ~70% probability (randomly via ``ctx.rng``),
    simulating agents that may disagree.  The accept probability is
    designed to make quorum reachable in most rounds but create
    interesting failure dynamics under message drops.

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
        """Receive a proposal and respond with a single consistent vote."""
        msg = payload.decode("utf-8", errors="replace")
        if not msg.startswith("propose:"):
            return
        parts = msg.split(":")
        if len(parts) < 3:
            return
        rnd = parts[1]
        vote = "accept" if ctx.rng.random() < self._accept_probability else "reject"
        await ctx.send(self._leader, f"vote:{rnd}:{vote}".encode())


class ByzantineFollowerAgent(StateMachineAgent):
    """Byzantine follower that equivocates — sends conflicting votes.

    This agent simulates Byzantine behavior by sending *two* votes
    for each proposal: one ``"accept"`` and one ``"reject"``.  An honest
    leader should detect the equivocation and exclude this voter from
    the quorum count.

    The agent uses ``ctx.rng`` for any randomness, keeping traces
    deterministic.

    Example::

        byz = ByzantineFollowerAgent(AgentId("follower-3"), AgentId("leader-0"))
    """

    def __init__(
        self,
        agent_id: AgentId,
        leader: AgentId,
    ) -> None:
        self._id = agent_id
        self._leader = leader

    async def on_message(
        self, ctx: AgentContext, sender: AgentId, payload: bytes
    ) -> None:
        """Receive a proposal and send conflicting votes (equivocation)."""
        msg = payload.decode("utf-8", errors="replace")
        if not msg.startswith("propose:"):
            return
        parts = msg.split(":")
        if len(parts) < 3:
            return
        rnd = parts[1]
        # Equivocation: send both accept and reject
        await ctx.send(self._leader, f"vote:{rnd}:accept".encode())
        await ctx.send(self._leader, f"vote:{rnd}:reject".encode())


def quorum_consensus_factory(
    config: ScenarioConfig,
    plugins: dict[str, Any],
) -> dict[AgentId, StateMachineAgent]:
    """Create BFT quorum consensus leader and follower agents.

    Reads ``task.config.rounds``, ``task.config.quorum``,
    ``task.config.accept_probability``, and
    ``failures.byzantine_agents`` from the scenario config.

    Byzantine followers are selected from the end of the follower list
    (deterministic selection based on the ``byzantine_agents`` fraction).

    Example::

        agents = quorum_consensus_factory(config, plugins)
    """
    task_config = config.task.config
    rounds = task_config.get("rounds", 5)
    quorum = task_config.get("quorum", 2 / 3)
    accept_prob = task_config.get("accept_probability", 0.7)

    # Determine byzantine fraction from failures config
    byzantine_fraction = config.failures.byzantine_agents or task_config.get(
        "byzantine_fraction", 0.0
    )

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

    # Determine how many followers are Byzantine
    byzantine_count = int(follower_count * byzantine_fraction)

    # Honest followers first, Byzantine at the end
    honest_count = follower_count - byzantine_count

    for i in range(honest_count):
        aid = AgentId(f"follower-{i}")
        agents[aid] = QuorumFollowerAgent(
            aid,
            leader=leader_id,
            accept_probability=accept_prob,
        )

    for i in range(honest_count, follower_count):
        aid = AgentId(f"follower-{i}")
        agents[aid] = ByzantineFollowerAgent(
            aid,
            leader=leader_id,
        )

    return agents
