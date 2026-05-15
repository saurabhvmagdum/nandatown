# SPDX-License-Identifier: Apache-2.0
"""Identity layer interface: who is this agent, and how do I verify them?

Example::

    class MyIdentity(Identity):
        def sign(self, payload):
            return Signature(signer=self.agent_id, value=do_sign(payload))
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from nest_core.types import AgentId, AgentIdentity, Signature


@runtime_checkable
class Identity(Protocol):
    """Agent identity, signing, and verification.

    Example::

        identity: Identity = DidKeyIdentity(agent_id)
        sig = identity.sign(b"data")
    """

    def sign(self, payload: bytes) -> Signature:
        """Sign a payload with this agent's private key.

        Example::

            sig = identity.sign(b"important data")
        """
        ...

    def verify(self, payload: bytes, sig: Signature, agent: AgentId) -> bool:
        """Verify a signature from a given agent.

        Example::

            ok = identity.verify(b"data", sig, AgentId("a2"))
        """
        ...

    async def resolve(self, agent: AgentId) -> AgentIdentity:
        """Resolve an agent ID to its full identity record.

        Example::

            info = await identity.resolve(AgentId("a2"))
        """
        ...
