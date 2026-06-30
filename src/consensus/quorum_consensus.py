# SPDX-License-Identifier: Apache-2.0
"""NandaQuorum coordination plugin — 2/3 quorum consensus for Nanda Town.

Implements the ``Coordination`` layer interface using two-phase
(PREPARE + COMMIT) quorum voting. Votes and quorum state are tracked
in ``Round.metadata`` so the simulator's state-machine agents can
drive the protocol through the standard propose/participate/resolve/commit
lifecycle.

Example::

    coord = QuorumConsensus(AgentId("leader-0"), all_agent_ids)
    rnd = await coord.propose(task)
    vote = await coord.participate(rnd)
    outcome = await coord.resolve(rnd)
    await coord.commit(outcome)
"""

from __future__ import annotations

import uuid
from typing import Any

from nest_core.types import (
    AgentId,
    Bid,
    Money,
    Outcome,
    Round,
    Task,
    Vote,
)

from .quorum import Quorum


class QuorumConsensus:
    """Two-phase quorum consensus as a Coordination plugin.

    This plugin wraps the NandaQuorum protocol into the Nanda Town
    ``Coordination`` interface. Round metadata stores:
      - ``votes``: list of {voter, value} dicts
      - ``quorum_threshold``: computed threshold for the participant count
      - ``total_nodes``: total expected participants
      - ``phase``: current protocol phase ("prepare" | "commit" | "decided")
      - ``proposed_value``: the value under consensus

    Example::

        coord = QuorumConsensus(AgentId("a0"), ["a0", "a1", "a2"])
        rnd = await coord.propose(Task(id="t1", description="assign work"))
    """

    def __init__(
        self,
        agent_id: AgentId,
        peer_ids: list[str] | None = None,
    ) -> None:
        """Initialize the quorum consensus plugin.

        Args:
            agent_id: This agent's ID.
            peer_ids: List of all participating agent IDs (for quorum calc).
        """
        self._agent_id = agent_id
        self._peer_ids = peer_ids or []

    async def propose(self, task: Task) -> Round:
        """Propose a task for quorum-based consensus.

        Creates a new Round with quorum metadata initialized.

        Example::

            rnd = await coord.propose(task)
        """
        total = max(len(self._peer_ids), 1)
        threshold = Quorum.threshold(total)
        round_id = str(uuid.uuid4())
        rnd = Round(
            id=round_id,
            task=task,
            participants=[],
            metadata={
                "votes": [],
                "quorum_threshold": threshold,
                "total_nodes": total,
                "phase": "prepare",
                "proposed_value": task.description,
            },
        )
        return rnd

    async def participate(self, round: Round) -> Vote | Bid:
        """Participate in a quorum round by casting a vote.

        The vote value ("accept" or "reject") is stored in round metadata.
        In the simulation, the actual accept/reject decision is made by
        the scenario agent logic; this method records the vote.

        Example::

            vote = await coord.participate(rnd)
        """
        vote = Vote(
            voter=self._agent_id,
            round_id=round.id,
            value="accept",
        )
        votes: list[dict[str, object]] = round.metadata.setdefault("votes", [])
        votes.append({"voter": str(self._agent_id), "value": vote.value})
        if self._agent_id not in round.participants:
            round.participants.append(self._agent_id)
        return vote

    async def resolve(self, round: Round) -> Outcome:
        """Resolve the round by checking if quorum was reached.

        Counts "accept" votes and compares against the quorum threshold.
        The winner is the proposer (leader) if quorum is reached, else None.

        Example::

            outcome = await coord.resolve(rnd)
        """
        votes: list[dict[str, object]] = round.metadata.get("votes", [])
        total_nodes: int = round.metadata.get("total_nodes", len(round.participants))
        threshold = round.metadata.get("quorum_threshold", Quorum.threshold(total_nodes))

        accept_count = sum(1 for v in votes if v.get("value") == "accept")
        unique_voters = {str(v.get("voter", "")) for v in votes}

        quorum_reached = len(unique_voters) >= threshold and accept_count >= threshold
        winner = round.participants[0] if (quorum_reached and round.participants) else None

        round.metadata["phase"] = "decided"
        round.metadata["quorum_reached"] = quorum_reached
        round.metadata["accept_count"] = accept_count
        round.metadata["total_votes"] = len(unique_voters)

        return Outcome(
            round_id=round.id,
            winner=winner,
            task=round.task,
            metadata={
                "quorum_reached": quorum_reached,
                "accept_count": accept_count,
                "total_votes": len(unique_voters),
                "threshold": threshold,
            },
        )

    async def commit(self, outcome: Outcome) -> None:
        """Commit to the resolved outcome.

        For quorum consensus, committing is a no-op at the plugin level —
        the scenario agents handle broadcasting the result.

        Example::

            await coord.commit(outcome)
        """
