# SPDX-License-Identifier: Apache-2.0
"""Payments layer interface: how value moves between agents.

Example::

    class MyPayments(Payments):
        async def pay(self, to, amount, ref):
            self._ledger[to] += amount.amount
            return Receipt(ref=ref, payer=self._me, payee=to, amount=amount)
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from nest_core.types import AgentId, Money, PaymentRef, PaymentStatus, Quote, Receipt, ServiceRef


@runtime_checkable
class Payments(Protocol):
    """Payment processing between agents.

    Example::

        payments: Payments = PrepaidCredits(agent_id, initial=1000)
        receipt = await payments.pay(AgentId("a2"), Money(amount=50), PaymentRef("p1"))
    """

    async def quote(self, service: ServiceRef) -> Quote:
        """Get a price quote for a service.

        Example::

            q = await payments.quote(ServiceRef("data-cleaning"))
        """
        ...

    async def pay(self, to: AgentId, amount: Money, ref: PaymentRef) -> Receipt:
        """Execute a payment to another agent.

        Example::

            receipt = await payments.pay(AgentId("a2"), Money(amount=50), PaymentRef("p1"))
        """
        ...

    async def verify_payment(self, ref: PaymentRef) -> PaymentStatus:
        """Verify the status of a payment.

        Example::

            status = await payments.verify_payment(PaymentRef("p1"))
        """
        ...

    async def refund(self, ref: PaymentRef) -> None:
        """Refund a payment.

        Example::

            await payments.refund(PaymentRef("p1"))
        """
        ...
