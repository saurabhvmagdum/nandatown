"""Asynchronous message transport layer for NandaQuorum.

Provides in-process message passing between consensus nodes using asyncio.
In a production deployment this would be replaced with HTTP/gRPC transport,
but for hackathon evaluation the in-memory approach allows deterministic
testing and avoids network setup overhead.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .node import Node
    from .messages import Message

logger = logging.getLogger(__name__)


class Network:
    """Asynchronous in-memory message transport between consensus nodes.

    Nodes register themselves by ID. Messages are dispatched asynchronously
    via asyncio to simulate network communication with realistic concurrency
    semantics.

    Attributes:
        nodes: Registry mapping node IDs to Node instances.
        message_count: Running total of messages sent through the network.
        latency_ms: Simulated network latency in milliseconds (0 = instant).
    """

    def __init__(self, latency_ms: float = 0.0) -> None:
        """Initialize the network transport.

        Args:
            latency_ms: Optional simulated network latency in milliseconds.
        """
        self.nodes: dict[str, Node] = {}
        self.message_count: int = 0
        self.latency_ms: float = latency_ms

    def register(self, node_id: str, node: Node) -> None:
        """Register a node with the network.

        Args:
            node_id: Unique identifier for the node.
            node: The Node instance to register.
        """
        self.nodes[node_id] = node
        logger.info("Registered node %s with network", node_id)

    def unregister(self, node_id: str) -> None:
        """Remove a node from the network (simulates crash).

        Args:
            node_id: The node to remove.
        """
        if node_id in self.nodes:
            del self.nodes[node_id]
            logger.info("Unregistered node %s from network (crash simulation)", node_id)

    async def broadcast(self, sender: str, msg: Message) -> None:
        """Send a message to all registered peers except the sender.

        Messages are dispatched concurrently using asyncio.gather.

        Args:
            sender: Node ID of the sender (excluded from broadcast).
            msg: The Message to broadcast.
        """
        tasks = []
        for node_id, node in self.nodes.items():
            if node_id != sender:
                tasks.append(self._deliver(node, msg))
        if tasks:
            await asyncio.gather(*tasks)

    async def send(self, sender: str, target: str, msg: Message) -> None:
        """Send a message to a specific target node.

        Args:
            sender: Node ID of the sender.
            target: Node ID of the target.
            msg: The Message to send.

        Raises:
            KeyError: If the target node is not registered.
        """
        if target not in self.nodes:
            logger.warning(
                "Target node %s not found (may have crashed). "
                "Message from %s dropped.",
                target,
                sender,
            )
            return
        await self._deliver(self.nodes[target], msg)

    async def _deliver(self, node: Node, msg: Message) -> None:
        """Deliver a message to a node, optionally with simulated latency.

        Args:
            node: The target Node instance.
            msg: The Message to deliver.
        """
        self.message_count += 1
        if self.latency_ms > 0:
            await asyncio.sleep(self.latency_ms / 1000.0)
        await node.receive_message(msg)
