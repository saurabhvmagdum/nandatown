# SPDX-License-Identifier: Apache-2.0
"""Tests for layer interface definitions — verify they are importable and runtime-checkable."""

from typing import runtime_checkable

from nest_core.layers import (
    Auth,
    CommsProtocol,
    Coordination,
    DataFacts,
    Identity,
    Memory,
    Negotiation,
    Payments,
    Privacy,
    Registry,
    Transport,
    Trust,
)


def test_all_12_layers_importable() -> None:
    """All 12 layer protocols can be imported from nest_core.layers."""
    layers = [
        Auth,
        CommsProtocol,
        Coordination,
        DataFacts,
        Identity,
        Memory,
        Negotiation,
        Payments,
        Privacy,
        Registry,
        Transport,
        Trust,
    ]
    assert len(layers) == 12


def test_layers_are_runtime_checkable() -> None:
    """All layer protocols are decorated with @runtime_checkable."""
    for protocol in [
        Auth,
        CommsProtocol,
        Coordination,
        DataFacts,
        Identity,
        Memory,
        Negotiation,
        Payments,
        Privacy,
        Registry,
        Transport,
        Trust,
    ]:
        assert runtime_checkable(protocol) is protocol
