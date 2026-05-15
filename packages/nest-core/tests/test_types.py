# SPDX-License-Identifier: Apache-2.0
"""Tests for core types."""

from nest_core.types import (
    AgentCard,
    AgentId,
    Message,
    MessageId,
    Money,
    PaymentStatus,
    Query,
    Task,
    TransportCapabilities,
)


def test_agent_id_is_str() -> None:
    """AgentId wraps a string."""
    aid = AgentId("agent-1")
    assert aid == "agent-1"


def test_message_creation() -> None:
    """Messages can be created with required fields."""
    msg = Message(
        id=MessageId("m1"),
        sender=AgentId("a1"),
        receiver=AgentId("a2"),
        payload=b"hello",
    )
    assert msg.sender == AgentId("a1")
    assert msg.payload == b"hello"


def test_agent_card_defaults() -> None:
    """AgentCard has sensible defaults."""
    card = AgentCard(agent_id=AgentId("a1"), name="TestAgent")
    assert card.capabilities == []
    assert card.endpoint is None


def test_query_defaults() -> None:
    """Query has sensible defaults."""
    q = Query()
    assert q.capabilities == []
    assert q.name_pattern is None


def test_money() -> None:
    """Money has amount and currency."""
    m = Money(amount=100)
    assert m.currency == "credits"
    assert m.amount == 100


def test_payment_status_enum() -> None:
    """PaymentStatus enum has expected values."""
    assert PaymentStatus.CONFIRMED.value == "confirmed"
    assert PaymentStatus.REFUNDED.value == "refunded"


def test_task_creation() -> None:
    """Tasks can be created."""
    t = Task(id="t1", description="do stuff")
    assert t.requirements == []


def test_transport_capabilities_defaults() -> None:
    """TransportCapabilities has sensible defaults."""
    caps = TransportCapabilities()
    assert caps.ordered is True
    assert caps.reliable is True
    assert caps.supports_streaming is False
