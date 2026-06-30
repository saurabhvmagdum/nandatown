"""NandaQuorum — Lightweight 2/3 Quorum Consensus for Nanda Town.

This package implements a two-phase (PREPARE + COMMIT) voting protocol
that lets a cluster of Nanda Town agents agree on a single value using
a 2/3 quorum threshold. It is crash-fault tolerant (not Byzantine).

Public API:
    Quorum              — Quorum threshold math and vote validation
    Node                — Consensus node state machine
    NodeState           — Enum of node states (FOLLOWER, CANDIDATE, LEADER)
    Message             — Protocol message dataclass with JSON serialization
    QuorumCertificate   — Aggregated PREPARE votes proving quorum
    LeaderSelector      — Round-robin leader election
    Network             — Async in-memory message transport
    ConsensusMetrics    — Per-height metrics dataclass
    MetricsCollector    — JSONL metrics logger
    LatencyTimer        — Phase latency measurement
"""

from .quorum import Quorum
from .node import Node, NodeState
from .messages import Message, QuorumCertificate
from .leader import LeaderSelector
from .network import Network
from .metrics import ConsensusMetrics, MetricsCollector, LatencyTimer

__all__ = [
    "Quorum",
    "Node",
    "NodeState",
    "Message",
    "QuorumCertificate",
    "LeaderSelector",
    "Network",
    "ConsensusMetrics",
    "MetricsCollector",
    "LatencyTimer",
]
