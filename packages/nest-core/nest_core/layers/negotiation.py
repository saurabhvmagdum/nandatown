# SPDX-License-Identifier: Apache-2.0
"""Negotiation layer interface: bargaining between agents over terms.

Example::

    class MyNegotiation(Negotiation):
        async def open(self, partner, terms):
            return NegotiationSession(id="n1", initiator=self._me, partner=partner)
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from nest_core.types import (
    AgentId,
    Agreement,
    NegotiationResponse,
    NegotiationSession,
    Terms,
)


@runtime_checkable
class Negotiation(Protocol):
    """Bargaining protocol between two or more agents.

    Example::

        neg: Negotiation = AlternatingOffers(agent_id)
        session = await neg.open(AgentId("a2"), Terms(price=Money(amount=100)))
    """

    async def open(self, partner: AgentId, terms: Terms) -> NegotiationSession:
        """Open a negotiation session with initial terms.

        Example::

            session = await neg.open(AgentId("a2"), terms)
        """
        ...

    async def offer(self, session: NegotiationSession, terms: Terms) -> None:
        """Make an offer in an ongoing negotiation.

        Example::

            await neg.offer(session, Terms(price=Money(amount=80)))
        """
        ...

    async def respond(self, session: NegotiationSession) -> NegotiationResponse:
        """Respond to the latest offer in a negotiation.

        Example::

            resp = await neg.respond(session)
        """
        ...

    async def close(self, session: NegotiationSession) -> Agreement | None:
        """Close a negotiation session, returning an agreement if reached.

        Example::

            agreement = await neg.close(session)
        """
        ...
