# Example: New payment protocol

Build a custom `Payments` plugin, register it via entry point, and
benchmark it against the bundled `prepaid_credits` baseline using the
`marketplace` scenario.

For the full walkthrough (with code you can paste), see
[`docs/writing-a-plugin.md`](../../docs/writing-a-plugin.md). The TL;DR:

1. Implement the `Payments` Protocol — `quote`, `pay`, `verify_payment`,
   `refund`. No base class required (it's a `typing.Protocol`).
2. Add `[project.entry-points."nest.plugins.payments"]` to your
   `pyproject.toml`.
3. `pip install -e .`
4. `nest plugins list | grep payments` — confirm your plugin appears.
5. `nest scenarios cp marketplace ./bench.yaml`, change
   `layers.payments` to your plugin's name, and `nest run ./bench.yaml`.
6. Generate reports for both traces (`nest report …`) and diff them.

Layer reference: [`docs/layers/payments.md`](../../docs/layers/payments.md).
Reference implementation to copy: [`prepaid_credits.py`](../../packages/nest-plugins-reference/nest_plugins_reference/payments/prepaid_credits.py).
