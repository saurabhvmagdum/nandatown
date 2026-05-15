# SPDX-License-Identifier: Apache-2.0
"""Communication layer interface: message format, request/response, discovery.

Example::

    class MyComms(CommsProtocol):
        def serialize(self, msg):
            return json.dumps(msg.model_dump()).encode()
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from nest_core.types import AgentCard, AgentId, Message, Query, Response


@runtime_checkable
class CommsProtocol(Protocol):
    """Wire protocol for agent communication.

    Example::

        comms: CommsProtocol = NestNativeComms()
        raw = comms.serialize(msg)
    """

    def serialize(self, msg: Message) -> bytes:
        """Serialize a Message into bytes for transport.

        Example::

            raw = comms.serialize(msg)
        """
        ...

    def deserialize(self, raw: bytes) -> Message:
        """Deserialize bytes back into a Message.

        Example::

            msg = comms.deserialize(raw)
        """
        ...

    async def send(self, to: AgentId, msg: Message) -> Response:
        """Send a message and wait for a response.

        Example::

            resp = await comms.send(AgentId("a2"), msg)
        """
        ...

    async def advertise(self, card: AgentCard) -> None:
        """Advertise this agent's capabilities.

        Example::

            await comms.advertise(my_card)
        """
        ...

    async def discover(self, query: Query) -> list[AgentCard]:
        """Discover agents matching a query.

        Example::

            cards = await comms.discover(Query(capabilities=["sell_data"]))
        """
        ...
