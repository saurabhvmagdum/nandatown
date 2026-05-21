# Memory layer

**What it does.** Shared key-value store with subscribe and
compare-and-swap.

## Interface

```python
class Memory(Protocol):
    async def read(self, key: str) -> bytes | None: ...
    async def write(self, key: str, value: bytes) -> None: ...
    async def subscribe(self, key: str) -> AsyncIterator[bytes]: ...
    async def cas(self, key: str, expected: bytes, new: bytes) -> bool: ...
```

Full definition: [`nest_core/layers/memory.py`](../../packages/nest-core/nest_core/layers/memory.py).

## Default plugin

`blackboard` — shared in-process dict with subscribe + CAS.

Source: [`nest_plugins_reference/memory/blackboard.py`](../../packages/nest-plugins-reference/nest_plugins_reference/memory/blackboard.py).

## Writing your own

See [`writing-a-plugin.md`](../writing-a-plugin.md). Register under
entry point group `nest.plugins.memory`.

Good fits to test here: CRDTs (LWW-Register, OR-Set), tuple spaces,
eventually-consistent stores, snapshot isolation.
