# Privacy layer

**What it does.** Encrypt and decrypt payloads; produce and verify
proofs about statements without revealing the witness.

## Interface

```python
class Privacy(Protocol):
    async def encrypt(self, data: bytes, audience: list[AgentId]) -> bytes: ...
    async def decrypt(self, data: bytes) -> bytes: ...
    async def prove(self, statement: Statement, witness: Witness) -> Proof: ...
    async def verify_proof(self, statement: Statement, proof: Proof) -> bool: ...
```

Full definition: [`nest_core/layers/privacy.py`](../../packages/nest-core/nest_core/layers/privacy.py).

## Default plugin

`noop` — **passthrough.** Returns data unchanged; "proofs" are always
valid. Use this when your scenario doesn't care about confidentiality
and you don't want to pay any cost.

Source: [`nest_plugins_reference/privacy/noop.py`](../../packages/nest-plugins-reference/nest_plugins_reference/privacy/noop.py).

## Writing your own

See [`writing-a-plugin.md`](../writing-a-plugin.md). Register under
entry point group `nest.plugins.privacy`.

Good fits to test here: hybrid encryption (X25519 + ChaCha20-Poly1305),
group key exchange, zk-SNARK / zk-STARK / Bulletproofs adapters,
selective disclosure of credentials.
