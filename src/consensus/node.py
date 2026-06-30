"""Consensus node state machine and voting logic for NandaQuorum.

Implements the two-phase (PREPARE + COMMIT) quorum consensus protocol.
Each node transitions through FOLLOWER → CANDIDATE → LEADER states and
handles incoming protocol messages according to its current role.
"""

from __future__ import annotations

import asyncio
import logging
import time
from enum import Enum
from typing import TYPE_CHECKING, Any

from .leader import LeaderSelector
from .messages import Message, QuorumCertificate
from .metrics import ConsensusMetrics, LatencyTimer, MetricsCollector
from .quorum import Quorum

if TYPE_CHECKING:
    from .network import Network

logger = logging.getLogger(__name__)


class NodeState(Enum):
    """Possible states for a consensus node."""

    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


class Node:
    """A consensus node participating in the NandaQuorum protocol.

    Each node maintains its own view of the current height and round,
    collects votes, and transitions through the state machine as the
    protocol progresses.

    State Transitions:
        FOLLOWER  → CANDIDATE  (on phase timeout)
        CANDIDATE → LEADER     (if round matches node_id rotation)
        LEADER    → FOLLOWER   (after commit or on new height)

    Attributes:
        node_id: Unique identifier for this node.
        peers: List of all peer node IDs (including self).
        state: Current NodeState.
        height: Current consensus height.
        round: Current consensus round within the height.
        prepare_votes: Mapping of round → set of sender IDs who sent PREPARE_VOTE.
        commit_votes: Mapping of round → set of sender IDs who sent COMMIT_VOTE.
        leader_id: Current leader node ID (may be None).
        pending_value: The value being proposed / voted on.
        committed_values: List of values committed at each height.
        network: Reference to the network transport layer.
        leader_selector: Round-robin leader selector.
        metrics_collector: Metrics collector for evaluation.
        phase_timeout: Timeout in seconds for each phase.
        max_rounds: Maximum rounds before aborting.
    """

    def __init__(
        self,
        node_id: str,
        peers: list[str],
        network: Network | None = None,
        phase_timeout: float = 5.0,
        max_rounds: int = 10,
        metrics_collector: MetricsCollector | None = None,
    ) -> None:
        """Initialize a consensus node.

        Args:
            node_id: Unique identifier for this node.
            peers: List of all participating node IDs (including self).
            network: Network transport layer for sending messages.
            phase_timeout: Timeout in seconds before triggering leader rotation.
            max_rounds: Maximum consensus rounds before aborting a height.
            metrics_collector: Optional metrics collector for evaluation logging.
        """
        self.node_id = node_id
        self.peers = peers
        self.state = NodeState.FOLLOWER
        self.height = 0
        self.round = 0
        self.prepare_votes: dict[int, set[str]] = {}
        self.commit_votes: dict[int, set[str]] = {}
        self.leader_id: str | None = None
        self.pending_value: Any = None
        self.committed_values: list[Any] = []

        # External dependencies
        self.network = network
        self.leader_selector = LeaderSelector(peers)
        self.metrics_collector = metrics_collector or MetricsCollector(enabled=False)

        # Configuration
        self.phase_timeout = phase_timeout
        self.max_rounds = max_rounds

        # Internal timing
        self._prepare_timer = LatencyTimer()
        self._commit_timer = LatencyTimer()
        self._current_metrics = ConsensusMetrics(height=self.height)

        # Protocol phase guards (prevent re-entering quorum logic)
        self._qc_formed: bool = False
        self._committed: bool = False

        # Timeout task handle
        self._timeout_task: asyncio.Task | None = None

    @property
    def total_nodes(self) -> int:
        """Return the total number of nodes in the cluster."""
        return len(self.peers)

    def _is_leader(self) -> bool:
        """Check if this node is the leader for the current round."""
        return self.leader_selector.is_leader(self.node_id, self.round)

    async def receive_message(self, msg: Message) -> None:
        """Route an incoming message to the appropriate handler.

        This is the main entry point for message processing. It validates
        the message and dispatches to the correct handler based on msg_type.

        Args:
            msg: The incoming protocol message.
        """
        known_peers = set(self.peers)
        if not msg.validate(self.height, self.round, known_peers):
            logger.debug(
                "[%s] Dropping invalid message from %s: type=%s h=%d r=%d",
                self.node_id, msg.sender, msg.msg_type, msg.height, msg.round,
            )
            return

        self._current_metrics.total_messages += 1

        if msg.msg_type == "PROPOSE":
            await self.handle_propose(msg)
        elif msg.msg_type == "PREPARE_VOTE":
            await self.handle_prepare_vote(msg)
        elif msg.msg_type == "QC":
            await self.handle_quorum_certificate(msg)
        elif msg.msg_type == "COMMIT_VOTE":
            await self.handle_commit_vote(msg)
        elif msg.msg_type == "ROUND_CHANGE":
            await self.handle_round_change(msg)

    async def propose(self, value: Any) -> None:
        """Initiate a new consensus round by proposing a value.

        Only the current leader should call this. Broadcasts a PROPOSE
        message to all peers and starts the prepare phase timer.

        Args:
            value: The value to propose for consensus.
        """
        if not self._is_leader():
            logger.warning("[%s] Non-leader attempted to propose", self.node_id)
            return

        self.state = NodeState.LEADER
        self.leader_id = self.node_id
        self.pending_value = value
        self._qc_formed = False
        self._committed = False
        self._current_metrics = ConsensusMetrics(height=self.height)
        self._prepare_timer.start()

        msg = Message(
            msg_type="PROPOSE",
            height=self.height,
            round=self.round,
            sender=self.node_id,
            payload=value,
        )

        logger.info(
            "[%s] PROPOSE value=%s at h=%d r=%d",
            self.node_id, value, self.height, self.round,
        )

        # Leader also votes for its own proposal (must be before broadcast
        # so that when follower responses arrive synchronously, the leader's
        # vote is already counted toward quorum).
        self.prepare_votes.setdefault(self.round, set()).add(self.node_id)

        if self.network:
            self._current_metrics.total_messages += 1
            await self.network.broadcast(self.node_id, msg)

        # Start timeout
        self._start_timeout()

    async def handle_propose(self, msg: Message) -> None:
        """Phase 1: Validate proposal and broadcast PREPARE_VOTE.

        Called when a follower receives a PROPOSE message from the leader.

        Args:
            msg: The PROPOSE message from the leader.
        """
        expected_leader = self.leader_selector.get_leader(msg.round)
        if msg.sender != expected_leader:
            logger.warning(
                "[%s] Rejecting PROPOSE from non-leader %s (expected %s)",
                self.node_id, msg.sender, expected_leader,
            )
            return

        self.leader_id = msg.sender
        self.pending_value = msg.payload
        self.state = NodeState.FOLLOWER

        # Send PREPARE_VOTE
        vote = Message(
            msg_type="PREPARE_VOTE",
            height=msg.height,
            round=msg.round,
            sender=self.node_id,
            payload=msg.payload,
        )

        logger.info(
            "[%s] PREPARE_VOTE for h=%d r=%d",
            self.node_id, msg.height, msg.round,
        )

        if self.network:
            self._current_metrics.total_messages += 1
            await self.network.send(self.node_id, self.leader_id, vote)

    async def handle_prepare_vote(self, msg: Message) -> None:
        """Collect PREPARE votes; if leader and quorum reached, broadcast QC.

        Called when the leader receives a PREPARE_VOTE from a follower.

        Args:
            msg: The PREPARE_VOTE message.
        """
        self.prepare_votes.setdefault(msg.round, set()).add(msg.sender)
        vote_count = len(self.prepare_votes[msg.round])

        logger.debug(
            "[%s] PREPARE_VOTE from %s (count=%d/%d)",
            self.node_id, msg.sender, vote_count,
            Quorum.threshold(self.total_nodes),
        )

        if self._is_leader() and not self._qc_formed and Quorum.is_quorum(
            list(self.prepare_votes[msg.round]), self.total_nodes
        ):
            self._qc_formed = True
            # Quorum reached — form QC and broadcast
            prepare_latency = self._prepare_timer.stop()
            self._current_metrics.prepare_latency_ms = prepare_latency
            self._commit_timer.start()

            qc_votes = [
                Message(
                    msg_type="PREPARE_VOTE",
                    height=self.height,
                    round=self.round,
                    sender=voter_id,
                    payload=self.pending_value,
                )
                for voter_id in self.prepare_votes[msg.round]
            ]
            qc = QuorumCertificate(
                height=self.height, round=self.round, votes=qc_votes
            )

            qc_msg = Message(
                msg_type="QC",
                height=self.height,
                round=self.round,
                sender=self.node_id,
                payload=qc.to_json(),
            )

            logger.info(
                "[%s] QC formed at h=%d r=%d (prepare_latency=%.1fms)",
                self.node_id, self.height, self.round, prepare_latency,
            )

            # Leader also votes to commit (must be before broadcast
            # so that when follower responses arrive synchronously, the
            # leader's vote is already counted toward quorum).
            self.commit_votes.setdefault(self.round, set()).add(self.node_id)

            if self.network:
                self._current_metrics.total_messages += 1
                await self.network.broadcast(self.node_id, qc_msg)

    async def handle_quorum_certificate(self, msg: Message) -> None:
        """Phase 2: Validate QC and broadcast COMMIT_VOTE.

        Called when a follower receives a QC from the leader.

        Args:
            msg: The QC message from the leader.
        """
        # Verify the QC came from the expected leader
        expected_leader = self.leader_selector.get_leader(msg.round)
        if msg.sender != expected_leader:
            logger.warning(
                "[%s] Rejecting QC from non-leader %s",
                self.node_id, msg.sender,
            )
            return

        # Send COMMIT_VOTE
        vote = Message(
            msg_type="COMMIT_VOTE",
            height=msg.height,
            round=msg.round,
            sender=self.node_id,
            payload=self.pending_value,
        )

        logger.info(
            "[%s] COMMIT_VOTE for h=%d r=%d",
            self.node_id, msg.height, msg.round,
        )

        if self.network:
            self._current_metrics.total_messages += 1
            await self.network.send(self.node_id, expected_leader, vote)

    async def handle_commit_vote(self, msg: Message) -> None:
        """Collect COMMIT votes; if quorum reached, finalize value.

        Called when the leader receives a COMMIT_VOTE from a follower.

        Args:
            msg: The COMMIT_VOTE message.
        """
        self.commit_votes.setdefault(msg.round, set()).add(msg.sender)
        vote_count = len(self.commit_votes[msg.round])

        logger.debug(
            "[%s] COMMIT_VOTE from %s (count=%d/%d)",
            self.node_id, msg.sender, vote_count,
            Quorum.threshold(self.total_nodes),
        )

        if self._is_leader() and not self._committed and Quorum.is_quorum(
            list(self.commit_votes[msg.round]), self.total_nodes
        ):
            self._committed = True
            # COMMIT quorum reached — finalize value
            commit_latency = self._commit_timer.stop()
            self._current_metrics.commit_latency_ms = commit_latency
            self._current_metrics.quorum_reached = True
            self._current_metrics.rounds_to_commit = self.round

            logger.info(
                "[%s] COMMITTED value=%s at h=%d r=%d "
                "(commit_latency=%.1fms, total_msgs=%d)",
                self.node_id, self.pending_value, self.height, self.round,
                commit_latency, self._current_metrics.total_messages,
            )

            # Record metrics
            self.metrics_collector.record(self._current_metrics)

            # Finalize
            self.committed_values.append(self.pending_value)

            # Broadcast commit acknowledgment and advance height
            ack = Message(
                msg_type="ROUND_CHANGE",
                height=self.height + 1,
                round=0,
                sender=self.node_id,
                payload={"action": "NEW_HEIGHT", "committed": self.pending_value},
            )

            if self.network:
                self._current_metrics.total_messages += 1
                await self.network.broadcast(self.node_id, ack)

            self._advance_height()

    async def handle_round_change(self, msg: Message) -> None:
        """Handle a round change or new height notification.

        Args:
            msg: The ROUND_CHANGE message.
        """
        payload = msg.payload if isinstance(msg.payload, dict) else {}

        if payload.get("action") == "NEW_HEIGHT":
            # Advance to the new height
            committed = payload.get("committed")
            if committed is not None:
                self.committed_values.append(committed)
            self.height = msg.height
            self.round = 0
            self.state = NodeState.FOLLOWER
            self.pending_value = None
            self.prepare_votes.clear()
            self.commit_votes.clear()
            self._cancel_timeout()
            logger.info(
                "[%s] Advanced to height %d", self.node_id, self.height
            )
        else:
            # Round rotation due to timeout
            self.round = msg.round
            self.state = NodeState.FOLLOWER
            self.prepare_votes.setdefault(self.round, set())
            self.commit_votes.setdefault(self.round, set())
            self._cancel_timeout()
            logger.info(
                "[%s] Round change to r=%d", self.node_id, self.round
            )

    def _advance_height(self) -> None:
        """Advance the local state to the next height."""
        self.height += 1
        self.round = 0
        self.state = NodeState.FOLLOWER
        self.leader_id = None
        self.pending_value = None
        self.prepare_votes.clear()
        self.commit_votes.clear()
        self._qc_formed = False
        self._committed = False
        self._current_metrics = ConsensusMetrics(height=self.height)
        self._cancel_timeout()

    def _start_timeout(self) -> None:
        """Start a phase timeout that triggers leader rotation."""
        self._cancel_timeout()
        try:
            loop = asyncio.get_running_loop()
            self._timeout_task = loop.create_task(self._timeout_handler())
        except RuntimeError:
            # No running event loop — skip timeout (useful in sync tests)
            pass

    def _cancel_timeout(self) -> None:
        """Cancel any active timeout task."""
        if self._timeout_task and not self._timeout_task.done():
            self._timeout_task.cancel()
            self._timeout_task = None

    async def _timeout_handler(self) -> None:
        """Handle phase timeout by rotating leader to the next round."""
        await asyncio.sleep(self.phase_timeout)

        logger.warning(
            "[%s] Phase timeout at h=%d r=%d — rotating leader",
            self.node_id, self.height, self.round,
        )

        self.round += 1
        if self.round >= self.max_rounds:
            logger.error(
                "[%s] Max rounds (%d) reached at h=%d — aborting",
                self.node_id, self.max_rounds, self.height,
            )
            self._current_metrics.quorum_reached = False
            self.metrics_collector.record(self._current_metrics)
            return

        # Broadcast round change
        msg = Message(
            msg_type="ROUND_CHANGE",
            height=self.height,
            round=self.round,
            sender=self.node_id,
            payload={"action": "TIMEOUT"},
        )

        if self.network:
            await self.network.broadcast(self.node_id, msg)

        # If this node is now the leader, propose
        if self._is_leader() and self.pending_value is not None:
            await self.propose(self.pending_value)
