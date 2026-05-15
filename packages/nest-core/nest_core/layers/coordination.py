# SPDX-License-Identifier: Apache-2.0
"""Coordination layer interface: how groups decide.

Example::

    class MyCoordination(Coordination):
        async def propose(self, task):
            return Round(id="r1", task=task)
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from nest_core.types import Bid, Outcome, Round, Task, Vote


@runtime_checkable
class Coordination(Protocol):
    """Group decision-making protocol.

    Example::

        coord: Coordination = ContractNet()
        rnd = await coord.propose(task)
    """

    async def propose(self, task: Task) -> Round:
        """Propose a task for group coordination.

        Example::

            rnd = await coord.propose(Task(id="t1", description="process data"))
        """
        ...

    async def participate(self, round: Round) -> Vote | Bid:
        """Participate in a coordination round with a vote or bid.

        Example::

            bid = await coord.participate(rnd)
        """
        ...

    async def resolve(self, round: Round) -> Outcome:
        """Resolve a coordination round to an outcome.

        Example::

            outcome = await coord.resolve(rnd)
        """
        ...

    async def commit(self, outcome: Outcome) -> None:
        """Commit to a resolved outcome.

        Example::

            await coord.commit(outcome)
        """
        ...
