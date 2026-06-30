"""Round-robin leader election and rotation for NandaQuorum.

The leader is selected deterministically based on the consensus round
using a simple modulo rotation over a sorted list of node IDs.
"""

from __future__ import annotations


class LeaderSelector:
    """Deterministic round-robin leader selection.

    Node IDs are sorted lexicographically at construction time to ensure
    all nodes agree on the same leader for a given round, regardless of
    the order in which they discovered peers.

    Attributes:
        node_ids: Sorted list of all participating node IDs.
    """

    def __init__(self, node_ids: list[str]) -> None:
        """Initialize the leader selector.

        Args:
            node_ids: List of all participating node IDs.

        Raises:
            ValueError: If node_ids is empty.
        """
        if not node_ids:
            raise ValueError("node_ids must be non-empty")
        self.node_ids: list[str] = sorted(node_ids)

    def get_leader(self, round: int) -> str:
        """Select leader using round-robin modulo rotation.

        Args:
            round: The current consensus round number.

        Returns:
            The node ID of the leader for this round.
        """
        return self.node_ids[round % len(self.node_ids)]

    def is_leader(self, node_id: str, round: int) -> bool:
        """Check if the given node is the leader for the specified round.

        Args:
            node_id: The node ID to check.
            round: The consensus round number.

        Returns:
            True if node_id is the leader for this round.
        """
        return self.get_leader(round) == node_id

    def next_leader(self, current_round: int) -> str:
        """Return the leader for the next round.

        Args:
            current_round: The current consensus round.

        Returns:
            The node ID of the next round's leader.
        """
        return self.get_leader(current_round + 1)
