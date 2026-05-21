# Example: Full-stack swap

Swap *multiple* layers in one scenario — e.g. your identity scheme +
your trust scheme + your payments scheme — and measure how the whole
stack behaves end-to-end.

The mechanics are exactly the same as a single-layer swap. Each plugin
gets its own entry-point group; the scenario YAML names each by its
entry-point key.

```toml
# pyproject.toml of your aggregator package
[project.entry-points."nest.plugins.identity"]
my_identity = "my_pkg.identity:MyIdentity"

[project.entry-points."nest.plugins.trust"]
my_trust = "my_pkg.trust:MyTrust"

[project.entry-points."nest.plugins.payments"]
my_payments = "my_pkg.payments:MyPayments"
```

```yaml
# scenarios/my_stack.yaml
layers:
  identity: my_identity
  trust: my_trust
  payments: my_payments
  # all unset layers fall back to the built-in default
```

Then:

```bash
pip install -e .
nest plugins list                  # all three of yours should show up
nest run ./scenarios/my_stack.yaml
```

Tips for testing real interactions:

- **Vary one layer at a time first.** If `my_stack` produces unexpected
  metrics, swap one layer back to the default and re-run. The diff is
  almost always your own bug.
- **Use `failures.message_drop` to stress the seam between layers.**
  Reputation feedback loops, payment verification under retries, and
  identity caching are where multi-layer designs fall over.
- **Pin `seed:`** so reruns are byte-identical (Tier 1 only).

For the per-layer interface details see
[`docs/concepts.md`](../../docs/concepts.md) and the pages under
[`docs/layers/`](../../docs/layers/).
The plugin walkthrough is [`docs/writing-a-plugin.md`](../../docs/writing-a-plugin.md);
the scenario schema is [`docs/writing-a-scenario.md`](../../docs/writing-a-scenario.md).
