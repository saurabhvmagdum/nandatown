# SPDX-License-Identifier: Apache-2.0
"""In-memory transport plugin — standalone version for non-simulator use.

Example::

    transport = StandaloneInMemoryTransport(AgentId("a1"), network)
    await transport.send(AgentId("a2"), b"hello")
"""

from __future__ import annotations

import asyncio

from nest_core.types import AgentId, TransportCapabilities


class InMemoryNetwork:
    """Shared network that routes messages between in-memory transports.

    Example::

        network = InMemoryNetwork()
        t1 = StandaloneInMemoryTransport(AgentId("a1"), network)
    """

    def __init__(self) -> None:
        self._queues: dict[AgentId, asyncio.Queue[tuple[AgentId, bytes]]] = {}
        self._agents: list[AgentId] = []

    def register(self, agent_id: AgentId) -> asyncio.Queue[tuple[AgentId, bytes]]:
        """Register an agent and return its message queue.

        Example::

            queue = network.register(AgentId("a1"))
        """
        q: asyncio.Queue[tuple[AgentId, bytes]] = asyncio.Queue()
        self._queues[agent_id] = q
        self._agents.append(agent_id)
        return q

    def get_agents(self) -> list[AgentId]:
        """Return all registered agent IDs.

        Example::

            agents = network.get_agents()
        """
        return list(self._agents)

    async def deliver(self, sender: AgentId, to: AgentId, payload: bytes) -> None:
        """Deliver a message to the target agent's queue.

        Example::

            await network.deliver(AgentId("a1"), AgentId("a2"), b"hi")
        """
        q = self._queues.get(to)
        if q is not None:
            await q.put((sender, payload))


class StandaloneInMemoryTransport:
    """In-memory transport for use outside the simulator (e.g., Tier 2).

    Example::

        network = InMemoryNetwork()
        transport = StandaloneInMemoryTransport(AgentId("a1"), network)
        await transport.send(AgentId("a2"), b"hello")
    """

    capabilities = TransportCapabilities(
        supports_streaming=False,
        ordered=True,
        reliable=True,
    )

    def __init__(self, agent_id: AgentId, network: InMemoryNetwork) -> None:
        self._agent_id = agent_id
        self._network = network
        self._queue = network.register(agent_id)

    async def send(self, to: AgentId, payload: bytes) -> None:
        """Send a payload to a specific agent.

        Example::

            await transport.send(AgentId("a2"), b"hello")
        """
        await self._network.deliver(self._agent_id, to, payload)

    async def receive(self) -> tuple[AgentId, bytes]:
        """Wait for the next message and return (sender, payload).

        Example::

            sender, data = await transport.receive()
        """
        return await self._queue.get()

    async def broadcast(self, payload: bytes) -> None:
        """Broadcast to all agents on the network.

        Example::

            await transport.broadcast(b"announcement")
        """
        for aid in self._network.get_agents():
            if aid != self._agent_id:
                await self.send(aid, payload)
