"""Quorum mathematics for NandaQuorum consensus protocol.

Computes quorum thresholds and validates vote sets using a 2/3 majority rule.
This module is the mathematical foundation of the consensus layer.
"""


class Quorum:
    """Utility class for quorum threshold computation and validation.

    The quorum fraction is fixed at 2/3 (ceil), meaning:
      - n=3 → threshold=3  (tolerates 0 crash faults)
      - n=4 → threshold=3  (tolerates 1 crash fault)
      - n=5 → threshold=4  (tolerates 1 crash fault)
      - n=7 → threshold=5  (tolerates 2 crash faults)
      - n=10 → threshold=7 (tolerates 3 crash faults)
    """

    @staticmethod
    def threshold(total_nodes: int) -> int:
        """Return the minimum number of votes needed for a 2/3 quorum.

        Args:
            total_nodes: Total number of participating nodes in the cluster.

        Returns:
            The minimum number of agreeing votes required.

        Raises:
            ValueError: If total_nodes < 1.
        """
        if total_nodes < 1:
            raise ValueError(f"total_nodes must be >= 1, got {total_nodes}")
        return (2 * total_nodes) // 3 + 1

    @staticmethod
    def is_quorum(votes: list, total_nodes: int) -> bool:
        """Check if a list of unique votes meets the quorum threshold.

        Deduplicates votes before counting, so duplicate sender IDs
        are collapsed.

        Args:
            votes: List of voter identifiers (e.g. node IDs).
            total_nodes: Total number of participating nodes.

        Returns:
            True if the number of unique votes meets or exceeds the threshold.
        """
        return len(set(votes)) >= Quorum.threshold(total_nodes)

    @staticmethod
    def max_faults(total_nodes: int) -> int:
        """Return the maximum number of crash faults tolerable.

        Args:
            total_nodes: Total number of participating nodes.

        Returns:
            The maximum number of nodes that can crash while still
            allowing quorum to be reached.
        """
        return total_nodes - Quorum.threshold(total_nodes)
