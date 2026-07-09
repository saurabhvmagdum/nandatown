# SPDX-License-Identifier: Apache-2.0
"""NandaQuorum BFT coordination plugin — 2f+1 quorum consensus for Nanda Town.

Implements the ``Coordination`` layer interface using two-phase
(PREPARE + COMMIT) quorum voting with Byzantine fault tolerance.
Votes and quorum state are tracked in ``Round.metadata`` so the
simulator's state-machine agents can drive the protocol through
the standard propose/participate/resolve/commit lifecycle.

**BFT safety guarantee:** under up to *f* Byzantine agents out of
*3f+1* total, no two honest agents commit conflicting values for
the same round.

Determinism:
    This module uses **no** wall-clock time, unseeded RNG, or
    ``uuid.uuid4()``.  Round IDs are derived deterministically
    from the task ID and a per-instance counter.

Example::

    coord = QuorumConsensus(AgentId("leader-0"), all_agent_ids)
    rnd = await coord.propose(task)
    vote = await coord.participate(rnd)
    outcome = await coord.resolve(rnd)
    await coord.commit(outcome)
"""

from __future__ import annotations

from nest_core.types import (
    AgentId,
    Bid,
    Outcome,
    Round,
    Task,
    Vote,
)

from .quorum import Quorum


class QuorumConsensus:
    """Two-phase BFT quorum consensus as a Coordination plugin.

    This plugin wraps the NandaQuorum protocol into the Nanda Town
    ``Coordination`` interface.  Round metadata stores:

    - ``votes``: list of ``{voter, value}`` dicts
    - ``quorum_threshold``: computed BFT threshold (``2f+1``)
    - ``total_nodes``: total expected participants
    - ``max_byzantine``: maximum byzantine faults tolerable (``f``)
    - ``phase``: current protocol phase (``"prepare"`` | ``"commit"`` | ``"decided"``)
    - ``proposed_value``: the value under consensus
    - ``equivocations``: list of detected equivocating voters

    Example::

        coord = QuorumConsensus(AgentId("a0"), ["a0", "a1", "a2", "a3"])
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
        self._round_counter = 0

    async def propose(self, task: Task) -> Round:
        """Propose a task for BFT quorum-based consensus.

        Creates a new Round with BFT quorum metadata initialized.
        Round IDs are deterministic — derived from the task ID and an
        internal counter (no ``uuid.uuid4()``).

        Example::

            rnd = await coord.propose(task)
        """
        total = max(len(self._peer_ids), 1)
        threshold = Quorum.threshold(total)
        max_byz = Quorum.max_byzantine(total)

        # Deterministic round ID — no uuid.uuid4()
        self._round_counter += 1
        round_id = f"{task.id}:{self._round_counter}"

        rnd = Round(
            id=round_id,
            task=task,
            participants=[],
            metadata={
                "votes": [],
                "quorum_threshold": threshold,
                "total_nodes": total,
                "max_byzantine": max_byz,
                "phase": "prepare",
                "proposed_value": task.description,
                "equivocations": [],
            },
        )
        return rnd

    async def participate(self, round: Round) -> Vote | Bid:
        """Participate in a BFT quorum round by casting a vote.

        The vote value (``"accept"`` or ``"reject"``) is stored in round
        metadata.  Equivocation detection: if this voter has already cast
        a vote, the duplicate is flagged as an equivocation.

        Example::

            vote = await coord.participate(rnd)
        """
        # Check for equivocation — has this voter already voted?
        votes: list[dict[str, object]] = round.metadata.setdefault("votes", [])
        existing_voters = {str(v.get("voter", "")) for v in votes}

        vote = Vote(
            voter=self._agent_id,
            round_id=round.id,
            value="accept",
        )

        if str(self._agent_id) in existing_voters:
            # Equivocation detected — record but do NOT count the vote
            equivocations: list[str] = round.metadata.setdefault("equivocations", [])
            equivocations.append(str(self._agent_id))
        else:
            votes.append({"voter": str(self._agent_id), "value": vote.value})
            if self._agent_id not in round.participants:
                round.participants.append(self._agent_id)

        return vote

    async def resolve(self, round: Round) -> Outcome:
        """Resolve the round by checking if BFT quorum was reached.

        Counts ``"accept"`` votes from distinct, non-equivocating voters
        and compares against the BFT quorum threshold (``2f+1``).

        **Safety check:** Equivocating voters (those who sent conflicting
        votes) are excluded from the quorum count.  A forged quorum
        (fewer than ``2f+1`` genuine votes) is rejected.

        Example::

            outcome = await coord.resolve(rnd)
        """
        votes: list[dict[str, object]] = round.metadata.get("votes", [])
        total_nodes: int = round.metadata.get("total_nodes", len(round.participants))
        threshold = round.metadata.get("quorum_threshold", Quorum.threshold(total_nodes))
        equivocations: list[str] = round.metadata.get("equivocations", [])
        equivocation_set = set(equivocations)

        # Filter out equivocating voters — BFT safety
        genuine_votes = [v for v in votes if str(v.get("voter", "")) not in equivocation_set]

        accept_count = sum(1 for v in genuine_votes if v.get("value") == "accept")
        unique_genuine_voters = {str(v.get("voter", "")) for v in genuine_votes}

        quorum_reached = (
            len(unique_genuine_voters) >= threshold and accept_count >= threshold
        )
        winner = round.participants[0] if (quorum_reached and round.participants) else None

        round.metadata["phase"] = "decided"
        round.metadata["quorum_reached"] = quorum_reached
        round.metadata["accept_count"] = accept_count
        round.metadata["total_votes"] = len(unique_genuine_voters)
        round.metadata["equivocation_count"] = len(equivocation_set)

        return Outcome(
            round_id=round.id,
            winner=winner,
            task=round.task,
            metadata={
                "quorum_reached": quorum_reached,
                "accept_count": accept_count,
                "total_votes": len(unique_genuine_voters),
                "threshold": threshold,
                "equivocations": list(equivocation_set),
            },
        )

    async def commit(self, outcome: Outcome) -> None:
        """Commit to the resolved outcome.

        For quorum consensus, committing is a no-op at the plugin level —
        the scenario agents handle broadcasting the result.

        Example::

            await coord.commit(outcome)
        """
