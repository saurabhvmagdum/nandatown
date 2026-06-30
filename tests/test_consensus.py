"""Unit and integration tests for the NandaQuorum consensus protocol.

Covers:
  - Quorum threshold math (Section 6.1)
  - Happy-path consensus with 3, 5 nodes (Section 6.2)
  - Leader crash fault tolerance (Section 6.2)
  - Network partition / no-quorum safety (Section 6.2)
  - Message validation
  - Leader selection
"""

from __future__ import annotations

import asyncio
import pytest

from src.consensus import (
    Quorum,
    Node,
    NodeState,
    Message,
    QuorumCertificate,
    LeaderSelector,
    Network,
    ConsensusMetrics,
    MetricsCollector,
)


# ──────────────────────────────────────────────────────────
# 6.1 Unit Tests — Quorum Math
# ──────────────────────────────────────────────────────────


class TestQuorumThreshold:
    """Test quorum threshold computation (Appendix A reference table)."""

    def test_threshold_3(self):
        assert Quorum.threshold(3) == 3

    def test_threshold_4(self):
        assert Quorum.threshold(4) == 3

    def test_threshold_5(self):
        assert Quorum.threshold(5) == 4

    def test_threshold_7(self):
        assert Quorum.threshold(7) == 5

    def test_threshold_10(self):
        assert Quorum.threshold(10) == 7

    def test_threshold_invalid(self):
        with pytest.raises(ValueError):
            Quorum.threshold(0)


class TestIsQuorum:
    """Test quorum validation with vote sets."""

    def test_quorum_met_4_nodes(self):
        votes = ["A", "B", "C"]
        assert Quorum.is_quorum(votes, 4) is True

    def test_quorum_not_met_5_nodes(self):
        votes = ["A", "B", "C"]
        assert Quorum.is_quorum(votes, 5) is False

    def test_quorum_with_duplicates(self):
        """Duplicate votes should be deduplicated."""
        votes = ["A", "A", "B", "C"]
        assert Quorum.is_quorum(votes, 4) is True

    def test_quorum_exact_threshold(self):
        votes = ["A", "B", "C", "D"]
        assert Quorum.is_quorum(votes, 5) is True

    def test_max_faults(self):
        assert Quorum.max_faults(4) == 1
        assert Quorum.max_faults(7) == 2
        assert Quorum.max_faults(10) == 3


# ──────────────────────────────────────────────────────────
# Message Validation
# ──────────────────────────────────────────────────────────


class TestMessages:
    """Test message creation, serialization, and validation."""

    def test_message_roundtrip_json(self):
        msg = Message(
            msg_type="PROPOSE",
            height=0,
            round=0,
            sender="node-0",
            payload="value-42",
            timestamp=1000.0,
        )
        restored = Message.from_json(msg.to_json())
        assert restored.msg_type == msg.msg_type
        assert restored.height == msg.height
        assert restored.sender == msg.sender
        assert restored.payload == msg.payload

    def test_invalid_msg_type(self):
        with pytest.raises(ValueError, match="Invalid msg_type"):
            Message(
                msg_type="INVALID",
                height=0,
                round=0,
                sender="node-0",
                payload=None,
            )

    def test_validate_accepts_valid(self):
        msg = Message(
            msg_type="PROPOSE",
            height=1,
            round=0,
            sender="node-0",
            payload="v",
        )
        assert msg.validate(
            current_height=0, current_round=0, known_peers={"node-0", "node-1"}
        ) is True

    def test_validate_rejects_old_height(self):
        msg = Message(
            msg_type="PROPOSE",
            height=0,
            round=0,
            sender="node-0",
            payload="v",
        )
        assert msg.validate(
            current_height=1, current_round=0, known_peers={"node-0"}
        ) is False

    def test_validate_rejects_unknown_sender(self):
        msg = Message(
            msg_type="PROPOSE",
            height=0,
            round=0,
            sender="unknown",
            payload="v",
        )
        assert msg.validate(
            current_height=0, current_round=0, known_peers={"node-0"}
        ) is False

    def test_qc_roundtrip_json(self):
        votes = [
            Message(msg_type="PREPARE_VOTE", height=0, round=0, sender=f"node-{i}", payload="v")
            for i in range(3)
        ]
        qc = QuorumCertificate(height=0, round=0, votes=votes)
        restored = QuorumCertificate.from_json(qc.to_json())
        assert restored.height == 0
        assert restored.round == 0
        assert len(restored.votes) == 3
        assert restored.voter_ids() == {"node-0", "node-1", "node-2"}


# ──────────────────────────────────────────────────────────
# Leader Selection
# ──────────────────────────────────────────────────────────


class TestLeaderSelector:
    """Test round-robin leader election."""

    def test_round_robin(self):
        selector = LeaderSelector(["C", "A", "B"])
        # Sorted order: A, B, C
        assert selector.get_leader(0) == "A"
        assert selector.get_leader(1) == "B"
        assert selector.get_leader(2) == "C"
        assert selector.get_leader(3) == "A"  # wraps around

    def test_is_leader(self):
        selector = LeaderSelector(["node-0", "node-1", "node-2"])
        assert selector.is_leader("node-0", 0) is True
        assert selector.is_leader("node-1", 0) is False
        assert selector.is_leader("node-1", 1) is True

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            LeaderSelector([])


# ──────────────────────────────────────────────────────────
# Metrics
# ──────────────────────────────────────────────────────────


class TestMetrics:
    """Test metrics recording and summary."""

    def test_metrics_log(self):
        m = ConsensusMetrics(
            height=0,
            rounds_to_commit=0,
            prepare_latency_ms=12.3,
            commit_latency_ms=8.1,
            total_messages=9,
            quorum_reached=True,
        )
        log = m.log()
        assert log["height"] == 0
        assert log["quorum_reached"] is True

    def test_collector_summary(self):
        collector = MetricsCollector(enabled=False)
        collector.record(ConsensusMetrics(height=0, rounds_to_commit=0, quorum_reached=True))
        collector.record(ConsensusMetrics(height=1, rounds_to_commit=1, quorum_reached=True))
        summary = collector.summary()
        assert summary["total_heights"] == 2
        assert summary["avg_rounds_to_commit"] == 0.5
        assert summary["quorum_attainment_rate"] == 1.0

    def test_empty_summary(self):
        collector = MetricsCollector(enabled=False)
        summary = collector.summary()
        assert summary["total_heights"] == 0


# ──────────────────────────────────────────────────────────
# 6.2 Integration Tests — Happy Path
# ──────────────────────────────────────────────────────────


def _create_cluster(
    node_ids: list[str],
    metrics_collector: MetricsCollector | None = None,
) -> tuple[Network, dict[str, Node]]:
    """Helper: create a fully-connected cluster of consensus nodes."""
    network = Network()
    mc = metrics_collector or MetricsCollector(enabled=False)
    nodes = {}
    for nid in node_ids:
        node = Node(
            node_id=nid,
            peers=node_ids,
            network=network,
            phase_timeout=5.0,
            max_rounds=10,
            metrics_collector=mc,
        )
        nodes[nid] = node
        network.register(nid, node)
    return network, nodes


@pytest.mark.asyncio
async def test_happy_path_3():
    """3 nodes, 0 faults — should commit in round 0."""
    node_ids = ["node-0", "node-1", "node-2"]
    network, nodes = _create_cluster(node_ids)

    leader_id = LeaderSelector(node_ids).get_leader(0)
    leader = nodes[leader_id]

    await leader.propose("task-assignment-42")

    assert leader.committed_values == ["task-assignment-42"]
    assert leader.height == 1
    # Followers should have advanced via ROUND_CHANGE NEW_HEIGHT
    for nid, node in nodes.items():
        if nid != leader_id:
            assert node.height == 1
            assert "task-assignment-42" in node.committed_values


@pytest.mark.asyncio
async def test_happy_path_5():
    """5 nodes, 0 faults — should commit in round 0."""
    node_ids = [f"node-{i}" for i in range(5)]
    network, nodes = _create_cluster(node_ids)

    leader_id = LeaderSelector(node_ids).get_leader(0)
    leader = nodes[leader_id]

    await leader.propose("state-update-99")

    assert leader.committed_values == ["state-update-99"]
    assert leader.height == 1


@pytest.mark.asyncio
async def test_leader_crash_4():
    """4 nodes, 1 fault (leader crash) — should commit after leader rotation.

    Simulates the leader crashing after proposing by unregistering it from
    the network before the round starts. The next leader in round 1 should
    be able to form consensus.
    """
    node_ids = [f"node-{i}" for i in range(4)]
    network, nodes = _create_cluster(node_ids)

    # Identify round-0 leader and round-1 leader
    selector = LeaderSelector(node_ids)
    round0_leader_id = selector.get_leader(0)
    round1_leader_id = selector.get_leader(1)

    # Crash the round-0 leader before it proposes
    network.unregister(round0_leader_id)

    # Manually advance remaining nodes to round 1
    for nid, node in nodes.items():
        if nid != round0_leader_id:
            node.round = 1

    # Round-1 leader proposes
    round1_leader = nodes[round1_leader_id]
    await round1_leader.propose("recovery-value")

    assert round1_leader.committed_values == ["recovery-value"]
    assert round1_leader.height == 1


@pytest.mark.asyncio
async def test_leader_crash_7():
    """7 nodes, 2 faults (leader + 1 crash) — should commit after round rotation."""
    node_ids = [f"node-{i}" for i in range(7)]
    network, nodes = _create_cluster(node_ids)

    selector = LeaderSelector(node_ids)

    # Crash round-0 leader and one additional node
    round0_leader = selector.get_leader(0)
    round1_leader = selector.get_leader(1)

    # Pick an additional node to crash (not the round-1 leader)
    crash_targets = [round0_leader]
    for nid in node_ids:
        if nid not in (round0_leader, round1_leader) and len(crash_targets) < 2:
            crash_targets.append(nid)
            break

    for cid in crash_targets:
        network.unregister(cid)

    # Advance survivors to round 1
    # Update peers to reflect only surviving nodes for quorum calculation
    surviving_ids = [nid for nid in node_ids if nid not in crash_targets]
    for nid in surviving_ids:
        nodes[nid].round = 1

    round1_node = nodes[round1_leader]
    await round1_node.propose("fault-tolerant-value")

    assert round1_node.committed_values == ["fault-tolerant-value"]


@pytest.mark.asyncio
async def test_no_quorum_partition():
    """5 nodes, 2 crash (network partition) — should NOT commit (safe stall).

    With 5 nodes and threshold=4, losing 2 nodes means only 3 can vote,
    which is below the quorum threshold.
    """
    node_ids = [f"node-{i}" for i in range(5)]
    network, nodes = _create_cluster(node_ids)

    selector = LeaderSelector(node_ids)
    leader_id = selector.get_leader(0)

    # Crash 2 non-leader nodes
    crashed = []
    for nid in node_ids:
        if nid != leader_id and len(crashed) < 2:
            network.unregister(nid)
            crashed.append(nid)

    leader = nodes[leader_id]
    await leader.propose("should-not-commit")

    # Leader should NOT have committed — quorum was not reached
    assert leader.committed_values == []
    assert leader.height == 0


# ──────────────────────────────────────────────────────────
# Network Tests
# ──────────────────────────────────────────────────────────


class TestNetwork:
    """Test the network transport layer."""

    @pytest.mark.asyncio
    async def test_message_count(self):
        """Verify network tracks message deliveries."""
        node_ids = ["A", "B", "C"]
        network, nodes = _create_cluster(node_ids)

        # A full PROPOSE broadcast triggers the complete consensus cascade
        # (PROPOSE → PREPARE_VOTE → QC → COMMIT_VOTE → ROUND_CHANGE),
        # so message_count will be well above 2.
        initial_count = network.message_count
        leader_id = LeaderSelector(node_ids).get_leader(0)
        leader = nodes[leader_id]
        await leader.propose("count-test")
        assert network.message_count > initial_count

    @pytest.mark.asyncio
    async def test_send_to_crashed_node(self):
        """Sending to an unregistered node should not raise."""
        network = Network()
        msg = Message(
            msg_type="PROPOSE",
            height=0,
            round=0,
            sender="A",
            payload="test",
        )
        # Should not raise — just logs a warning
        await network.send("A", "nonexistent", msg)
