# SPDX-License-Identifier: Apache-2.0
"""Memory layer interface: shared state between agents.

Example::

    class MyMemory(Memory):
        async def read(self, key):
            return self._store.get(key)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable


@runtime_checkable
class Memory(Protocol):
    """Shared key-value state accessible to agents.

    Example::

        mem: Memory = Blackboard()
        await mem.write("counter", b"42")
    """

    async def read(self, key: str) -> bytes | None:
        """Read a value by key, returning None if absent.

        Example::

            val = await mem.read("counter")
        """
        ...

    async def write(self, key: str, value: bytes) -> None:
        """Write a value for a key.

        Example::

            await mem.write("counter", b"42")
        """
        ...

    async def subscribe(self, key: str) -> AsyncIterator[bytes]:
        """Subscribe to changes for a key.

        Example::

            async for val in mem.subscribe("counter"):
                print(val)
        """
        ...

    async def cas(self, key: str, expected: bytes, new: bytes) -> bool:
        """Compare-and-swap: update only if the current value matches expected.

        Example::

            ok = await mem.cas("counter", b"42", b"43")
        """
        ...
