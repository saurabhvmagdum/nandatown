# Trust layer

**What it does.** Maintain per-agent reputation, accept attestations
and abuse reports, optionally support stake.

## Interface

```python
class Trust(Protocol):
    async def score(self, agent: AgentId) -> ReputationScore: ...
    async def attest(self, agent: AgentId, claim: Claim) -> Attestation: ...
    async def report(self, agent: AgentId, evidence: Evidence) -> None: ...
    async def stake(self, agent: AgentId, amount: int) -> None: ...
```

Full definition: [`nest_core/layers/trust.py`](../../packages/nest-core/nest_core/layers/trust.py).

## Default plugin

`score_average` — running mean of feedback scores. No Sybil resistance,
no decay, no stake economics.

Source: [`nest_plugins_reference/trust/score_average.py`](../../packages/nest-plugins-reference/nest_plugins_reference/trust/score_average.py).

The `reputation` scenario exercises this layer — 16 honest + 4
malicious + 1 observer that samples cheat reports probabilistically.

## Writing your own

See [`writing-a-plugin.md`](../writing-a-plugin.md). Register under
entry point group `nest.plugins.trust`.

Good fits to test here: EigenTrust-style transitive reputation,
proof-of-stake reputation, decaying scores, attestation graphs.
