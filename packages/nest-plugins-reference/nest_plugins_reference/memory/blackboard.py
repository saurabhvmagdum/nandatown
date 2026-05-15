# SPDX-License-Identifier: Apache-2.0
"""Blackboard memory plugin — shared key-value store.

Example::

    mem = Blackboard()
    await mem.write("key", b"value")
    val = await mem.read("key")
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator


class Blackboard:
    """Shared key-value blackboard for agent state.

    Example::

        bb = Blackboard()
        await bb.write("counter", b"42")
        val = await bb.read("counter")
    """

    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}
        self._subscribers: dict[str, list[asyncio.Queue[bytes]]] = {}

    async def read(self, key: str) -> bytes | None:
        """Read a value by key.

        Example::

            val = await bb.read("counter")
        """
        return self._store.get(key)

    async def write(self, key: str, value: bytes) -> None:
        """Write a value for a key, notifying subscribers.

        Example::

            await bb.write("counter", b"42")
        """
        self._store[key] = value
        for q in self._subscribers.get(key, []):
            await q.put(value)

    async def subscribe(self, key: str) -> AsyncIterator[bytes]:
        """Subscribe to changes for a key.

        Example::

            async for val in bb.subscribe("counter"):
                print(val)
        """
        q: asyncio.Queue[bytes] = asyncio.Queue()
        self._subscribers.setdefault(key, []).append(q)
        try:
            while True:
                yield await q.get()
        finally:
            self._subscribers[key].remove(q)

    async def cas(self, key: str, expected: bytes, new: bytes) -> bool:
        """Compare-and-swap: update only if current value matches expected.

        Example::

            ok = await bb.cas("counter", b"42", b"43")
        """
        current = self._store.get(key)
        if current == expected:
            self._store[key] = new
            for q in self._subscribers.get(key, []):
                await q.put(new)
            return True
        return False
