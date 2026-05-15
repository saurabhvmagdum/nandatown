# SPDX-License-Identifier: Apache-2.0
"""Trust layer interface: reputation and attestation.

Example::

    class MyTrust(Trust):
        async def score(self, agent):
            return ReputationScore(agent_id=agent, score=0.85)
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from nest_core.types import AgentId, Attestation, Claim, Evidence, ReputationScore


@runtime_checkable
class Trust(Protocol):
    """Trust, reputation, and attestation for agents.

    Example::

        trust: Trust = ScoreAverageTrust()
        rep = await trust.score(AgentId("a1"))
    """

    async def score(self, agent: AgentId) -> ReputationScore:
        """Get the reputation score for an agent.

        Example::

            rep = await trust.score(AgentId("a1"))
        """
        ...

    async def attest(self, agent: AgentId, claim: Claim) -> Attestation:
        """Create an attestation about an agent.

        Example::

            att = await trust.attest(AgentId("a1"), claim)
        """
        ...

    async def report(self, agent: AgentId, evidence: Evidence) -> None:
        """Report evidence of misbehavior.

        Example::

            await trust.report(AgentId("a1"), evidence)
        """
        ...

    async def stake(self, agent: AgentId, amount: int) -> None:
        """Stake reputation on an agent's good behavior.

        Example::

            await trust.stake(AgentId("a1"), 100)
        """
        ...
