# SPDX-License-Identifier: Apache-2.0
"""Transport layer interface: how bytes move between agents.

Example::

    class MyTransport(Transport):
        async def send(self, to, payload):
            ...
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from nest_core.types import AgentId, TransportCapabilities


@runtime_checkable
class Transport(Protocol):
    """How bytes move between agents.

    Example::

        transport: Transport = InMemoryTransport()
        await transport.send(AgentId("a2"), b"hello")
    """

    capabilities: TransportCapabilities

    async def send(self, to: AgentId, payload: bytes) -> None:
        """Send a payload to a specific agent.

        Example::

            await transport.send(AgentId("a2"), b"hello")
        """
        ...

    async def receive(self) -> tuple[AgentId, bytes]:
        """Block until a message arrives; return (sender, payload).

        Example::

            sender, data = await transport.receive()
        """
        ...

    async def broadcast(self, payload: bytes) -> None:
        """Send a payload to all reachable agents.

        Example::

            await transport.broadcast(b"announcement")
        """
        ...
