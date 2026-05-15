# Writing a plugin

## Overview

A NEST plugin implements one layer interface and registers itself via Python entry points.

## Step 1: Choose your layer

Pick the layer you want to implement from the 12 available. See `docs/layers/` for interface details.

## Step 2: Implement the interface

```python
from nest_sdk import Payments, AgentId, Money, PaymentRef, Quote, Receipt, PaymentStatus, ServiceRef

class MyPaymentProtocol:
    async def quote(self, service: ServiceRef) -> Quote:
        ...

    async def pay(self, to: AgentId, amount: Money, ref: PaymentRef) -> Receipt:
        ...

    async def verify_payment(self, ref: PaymentRef) -> PaymentStatus:
        ...

    async def refund(self, ref: PaymentRef) -> None:
        ...
```

## Step 3: Register via entry points

In your `pyproject.toml`:

```toml
[project.entry-points."nest.plugins.payments"]
my_payment = "my_pkg.plugin:MyPaymentProtocol"
```

## Step 4: Declare requirements (optional)

```python
class MyPaymentProtocol:
    requires = ["transport.supports_streaming", "identity"]
    ...
```

## Step 5: Test conformance

```bash
nest plugins conform my_pkg
```

This runs the conformance test suite for your layer's interface.
