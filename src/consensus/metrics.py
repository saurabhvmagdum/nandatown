"""Consensus metrics collection for hackathon evaluation.

Tracks per-height metrics including latency, message counts, and quorum
attainment. Metrics can be logged to a JSONL file for post-hoc analysis
by hackathon judges.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class ConsensusMetrics:
    """Per-height consensus metrics.

    Attributes:
        height: The consensus height this metric covers.
        rounds_to_commit: Number of rounds needed to reach consensus (0 = optimal).
        prepare_latency_ms: Time from PROPOSE to QC formation in milliseconds.
        commit_latency_ms: Time from QC broadcast to COMMIT quorum in milliseconds.
        total_messages: Total number of protocol messages exchanged.
        quorum_reached: Whether consensus was successfully reached.
    """

    height: int = 0
    rounds_to_commit: int = 0
    prepare_latency_ms: float = 0.0
    commit_latency_ms: float = 0.0
    total_messages: int = 0
    quorum_reached: bool = False

    def log(self) -> dict:
        """Return a dictionary representation of the metrics.

        Returns:
            A dictionary suitable for JSON serialization.
        """
        return {
            "height": self.height,
            "rounds_to_commit": self.rounds_to_commit,
            "prepare_latency_ms": self.prepare_latency_ms,
            "commit_latency_ms": self.commit_latency_ms,
            "total_messages": self.total_messages,
            "quorum_reached": self.quorum_reached,
        }


class MetricsCollector:
    """Collects and persists consensus metrics across multiple heights.

    Writes metrics as JSONL (one JSON object per line) to the configured
    log path. Each entry includes a UTC timestamp.

    Attributes:
        log_path: Path to the JSONL metrics file.
        entries: In-memory list of all collected metrics.
        enabled: Whether metrics collection is active.
    """

    def __init__(self, log_path: str = "logs/consensus_metrics.jsonl", enabled: bool = True):
        """Initialize the metrics collector.

        Args:
            log_path: File path for the JSONL metrics log.
            enabled: If False, metrics are not persisted to disk.
        """
        self.log_path = log_path
        self.entries: list[ConsensusMetrics] = []
        self.enabled = enabled

        if self.enabled:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def record(self, metrics: ConsensusMetrics) -> None:
        """Record a completed height's metrics.

        Appends the metrics to the in-memory list and, if enabled,
        writes a JSONL entry to disk.

        Args:
            metrics: The ConsensusMetrics for a completed height.
        """
        self.entries.append(metrics)
        if self.enabled:
            entry = metrics.log()
            entry["timestamp"] = datetime.now(timezone.utc).isoformat()
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")

    def summary(self) -> dict:
        """Compute aggregate statistics across all recorded heights.

        Returns:
            A summary dictionary with averages and totals.
        """
        if not self.entries:
            return {
                "total_heights": 0,
                "avg_rounds_to_commit": 0.0,
                "avg_prepare_latency_ms": 0.0,
                "avg_commit_latency_ms": 0.0,
                "total_messages": 0,
                "quorum_attainment_rate": 0.0,
            }

        n = len(self.entries)
        return {
            "total_heights": n,
            "avg_rounds_to_commit": sum(e.rounds_to_commit for e in self.entries) / n,
            "avg_prepare_latency_ms": sum(e.prepare_latency_ms for e in self.entries) / n,
            "avg_commit_latency_ms": sum(e.commit_latency_ms for e in self.entries) / n,
            "total_messages": sum(e.total_messages for e in self.entries),
            "quorum_attainment_rate": sum(1 for e in self.entries if e.quorum_reached) / n,
        }


class LatencyTimer:
    """Simple context-manager / manual timer for measuring phase latencies.

    Usage:
        timer = LatencyTimer()
        timer.start()
        # ... do work ...
        elapsed_ms = timer.stop()
    """

    def __init__(self) -> None:
        self._start: float | None = None
        self._elapsed_ms: float = 0.0

    def start(self) -> None:
        """Start the timer."""
        self._start = time.monotonic()

    def stop(self) -> float:
        """Stop the timer and return elapsed milliseconds.

        Returns:
            Elapsed time in milliseconds since start().

        Raises:
            RuntimeError: If start() was not called.
        """
        if self._start is None:
            raise RuntimeError("Timer was not started")
        self._elapsed_ms = (time.monotonic() - self._start) * 1000.0
        self._start = None
        return self._elapsed_ms

    @property
    def elapsed_ms(self) -> float:
        """Return the last measured elapsed time in milliseconds."""
        return self._elapsed_ms
