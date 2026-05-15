# SPDX-License-Identifier: Apache-2.0
"""Contract Net coordination plugin — classic FIPA Contract Net Protocol.

The Round object is shared between manager and workers. Bids are stored
in the round's metadata so any party can resolve them.

Example::

    coord = ContractNet(AgentId("manager"))
    rnd = await coord.propose(task)
    bid = await coord.participate(rnd)
"""

from __future__ import annotations

import uuid

from nest_core.types import (
    AgentId,
    Bid,
    Money,
    Outcome,
    Round,
    Task,
    Vote,
)


class ContractNet:
    """FIPA Contract Net Protocol implementation.

    Example::

        coord = ContractNet(AgentId("a1"))
        rnd = await coord.propose(Task(id="t1", description="work"))
    """

    def __init__(self, agent_id: AgentId) -> None:
        self._agent_id = agent_id

    async def propose(self, task: Task) -> Round:
        """Propose a task for bidding.

        Example::

            rnd = await coord.propose(task)
        """
        round_id = str(uuid.uuid4())
        rnd = Round(
            id=round_id,
            task=task,
            participants=[],
            metadata={"bids": []},
        )
        return rnd

    async def participate(self, round: Round) -> Vote | Bid:
        """Submit a bid for a round.

        Example::

            bid = await coord.participate(rnd)
        """
        bid = Bid(
            bidder=self._agent_id,
            round_id=round.id,
            amount=Money(amount=1),
        )
        bids: list[dict[str, object]] = round.metadata.setdefault("bids", [])
        bids.append({"bidder": str(bid.bidder), "amount": bid.amount.amount})
        if self._agent_id not in round.participants:
            round.participants.append(self._agent_id)
        return bid

    async def resolve(self, round: Round) -> Outcome:
        """Resolve a round by selecting the lowest bidder.

        Example::

            outcome = await coord.resolve(rnd)
        """
        bids: list[dict[str, object]] = round.metadata.get("bids", [])
        winner: AgentId | None = None
        if bids:
            best = min(bids, key=lambda b: int(str(b["amount"])))
            winner = AgentId(str(best["bidder"]))
        return Outcome(round_id=round.id, winner=winner, task=round.task)

    async def commit(self, outcome: Outcome) -> None:
        """Commit to an outcome.

        Example::

            await coord.commit(outcome)
        """
