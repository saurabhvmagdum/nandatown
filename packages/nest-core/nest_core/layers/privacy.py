# SPDX-License-Identifier: Apache-2.0
"""Privacy layer interface: encryption and zero-knowledge proofs.

Example::

    class MyPrivacy(Privacy):
        async def encrypt(self, data, audience):
            return data  # noop
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from nest_core.types import AgentId, Proof, Statement, Witness


@runtime_checkable
class Privacy(Protocol):
    """Privacy primitives: encryption and zero-knowledge proofs.

    Example::

        priv: Privacy = NoopPrivacy()
        encrypted = await priv.encrypt(b"secret", [AgentId("a2")])
    """

    async def encrypt(self, data: bytes, audience: list[AgentId]) -> bytes:
        """Encrypt data so only the audience can read it.

        Example::

            ct = await priv.encrypt(b"secret", [AgentId("a2")])
        """
        ...

    async def decrypt(self, data: bytes) -> bytes:
        """Decrypt data intended for this agent.

        Example::

            pt = await priv.decrypt(ct)
        """
        ...

    async def prove(self, statement: Statement, witness: Witness) -> Proof:
        """Generate a zero-knowledge proof.

        Example::

            proof = await priv.prove(stmt, witness)
        """
        ...

    async def verify_proof(self, statement: Statement, proof: Proof) -> bool:
        """Verify a zero-knowledge proof.

        Example::

            ok = await priv.verify_proof(stmt, proof)
        """
        ...
