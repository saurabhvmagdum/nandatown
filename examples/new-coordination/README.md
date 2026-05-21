# Example: New coordination protocol

Build a custom `Coordination` plugin (e.g. Raft, Paxos, a BFT variant)
and test it against the bundled `auction`, `voting`, or `consensus`
scenarios.

For the full plugin walkthrough see
[`docs/writing-a-plugin.md`](../../docs/writing-a-plugin.md). The
shape:

1. Implement `Coordination` — `propose`, `participate`, `resolve`,
   `commit`. No inheritance required.
2. Register it under `[project.entry-points."nest.plugins.coordination"]`
   in your `pyproject.toml`.
3. `pip install -e .` then `nest plugins list | grep coordination` to
   confirm it loads.
4. `nest scenarios cp consensus ./bench.yaml`, set `layers.coordination`
   to your plugin's name, then `nest run ./bench.yaml`.
5. Validate the trace:

   ```bash
   python -c "
   from pathlib import Path
   from nest_core.validators import validate_trace
   for r in validate_trace(Path('traces/bench.jsonl'), 'consensus'):
       print(('PASS' if r.passed else 'FAIL'), r.name, '-', r.detail)
   "
   ```

   The consensus validators check ≥ 2/3 accepts, no committed value
   that wasn't proposed, and ≤ 1 commit per round — a real BFT/Raft
   plugin should keep them all passing under non-trivial
   `failures.message_drop` and `failures.byzantine_agents`.

Layer reference: [`docs/layers/coordination.md`](../../docs/layers/coordination.md).
Reference implementation to copy: [`contract_net.py`](../../packages/nest-plugins-reference/nest_plugins_reference/coordination/contract_net.py).
