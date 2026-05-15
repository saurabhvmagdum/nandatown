# SPDX-License-Identifier: Apache-2.0
"""Nest-native communication plugin — minimal JSON envelope.

Example::

    comms = NestNativeComms(AgentId("a1"), transport, registry)
    raw = comms.serialize(msg)
    msg2 = comms.deserialize(raw)
"""

from __future__ import annotations

import base64
import json
from typing import Any

from nest_core.types import (
    AgentCard,
    AgentId,
    Message,
    MessageId,
    Query,
    Response,
)


class NestNativeComms:
    """Minimal JSON-based communication protocol.

    Example::

        comms = NestNativeComms(AgentId("a1"), transport=t, registry=r)
        resp = await comms.send(AgentId("a2"), msg)
    """

    def __init__(
        self,
        agent_id: AgentId,
        transport: Any = None,
        registry: Any = None,
    ) -> None:
        self._agent_id = agent_id
        self._transport = transport
        self._registry = registry

    def serialize(self, msg: Message) -> bytes:
        """Serialize a Message to JSON bytes.

        Example::

            raw = comms.serialize(msg)
        """
        data = {
            "id": str(msg.id),
            "sender": str(msg.sender),
            "receiver": str(msg.receiver),
            "payload": base64.b64encode(msg.payload).decode("ascii"),
            "correlation_id": str(msg.correlation_id) if msg.correlation_id else None,
            "timestamp": msg.timestamp,
            "metadata": msg.metadata,
        }
        return json.dumps(data, sort_keys=True).encode("utf-8")

    def deserialize(self, raw: bytes) -> Message:
        """Deserialize JSON bytes back to a Message.

        Example::

            msg = comms.deserialize(raw)
        """
        data = json.loads(raw)
        return Message(
            id=MessageId(data["id"]),
            sender=AgentId(data["sender"]),
            receiver=AgentId(data["receiver"]),
            payload=base64.b64decode(data["payload"]),
            correlation_id=data.get("correlation_id"),
            timestamp=data.get("timestamp"),
            metadata=data.get("metadata", {}),
        )

    async def send(self, to: AgentId, msg: Message) -> Response:
        """Send a message via the transport layer.

        Example::

            resp = await comms.send(AgentId("a2"), msg)
        """
        raw = self.serialize(msg)
        if self._transport is not None:
            await self._transport.send(to, raw)
        return Response(success=True)

    async def advertise(self, card: AgentCard) -> None:
        """Advertise an agent card to the registry.

        Example::

            await comms.advertise(my_card)
        """
        if self._registry is not None:
            await self._registry.register(card)

    async def discover(self, query: Query) -> list[AgentCard]:
        """Discover agents via the registry.

        Example::

            cards = await comms.discover(Query(capabilities=["sell"]))
        """
        if self._registry is not None:
            result: list[AgentCard] = await self._registry.lookup(query)
            return result
        return []
