# SPDX-License-Identifier: Apache-2.0
"""BFT quorum mathematics for NandaQuorum consensus protocol.

Computes quorum thresholds and validates vote sets using BFT-standard
``2f+1`` out of ``3f+1`` majority rule.  This module is the mathematical
foundation of the consensus layer and is fully deterministic — no
wall-clock time, no unseeded RNG.

BFT threshold table (``3f+1`` total, ``2f+1`` quorum):

=====  ===  =========
 n      f   threshold
=====  ===  =========
  4     1      3
  7     2      5
 10     3      7
 13     4      9
=====  ===  =========

Example::

    assert Quorum.threshold(4) == 3       # 2*1 + 1
    assert Quorum.max_byzantine(7) == 2   # (7 - 1) // 3
"""

from typing import Any


class Quorum:
    """Utility class for BFT quorum threshold computation and validation.

    Uses the standard ``n = 3f + 1`` formula where *f* is the maximum
    number of Byzantine faults tolerable:

    * ``threshold(n) = 2f + 1`` where ``f = (n - 1) // 3``
    * A quorum is reached when ``>= threshold`` *distinct* votes are
      collected.

    Example::

        >>> Quorum.threshold(7)
        5
        >>> Quorum.is_quorum(["a", "b", "c", "d", "e"], 7)
        True
    """

    @staticmethod
    def threshold(total_nodes: int) -> int:
        """Return the minimum number of votes needed for a BFT quorum.

        For ``n = 3f + 1``, the threshold is ``2f + 1``.

        Args:
            total_nodes: Total number of participating nodes in the cluster.

        Returns:
            The minimum number of agreeing votes required.

        Raises:
            ValueError: If total_nodes < 1.

        Example::

            >>> Quorum.threshold(4)
            3
            >>> Quorum.threshold(7)
            5
        """
        if total_nodes < 1:
            raise ValueError(f"total_nodes must be >= 1, got {total_nodes}")
        f = (total_nodes - 1) // 3
        return 2 * f + 1

    @staticmethod
    def is_quorum(votes: list[Any], total_nodes: int) -> bool:
        """Check if a list of unique votes meets the quorum threshold.

        Deduplicates votes before counting, so duplicate sender IDs
        are collapsed.

        Args:
            votes: List of voter identifiers (e.g. node IDs).
            total_nodes: Total number of participating nodes.

        Returns:
            True if the number of unique votes meets or exceeds the threshold.

        Example::

            >>> Quorum.is_quorum(["a", "b", "c"], 4)
            True
        """
        return len(set(votes)) >= Quorum.threshold(total_nodes)

    @staticmethod
    def max_byzantine(total_nodes: int) -> int:
        """Return the maximum number of Byzantine faults tolerable.

        For ``n = 3f + 1``, ``f = (n - 1) // 3``.

        Args:
            total_nodes: Total number of participating nodes.

        Returns:
            The maximum number of Byzantine nodes the protocol can
            tolerate while preserving safety.

        Example::

            >>> Quorum.max_byzantine(4)
            1
            >>> Quorum.max_byzantine(7)
            2
        """
        return (total_nodes - 1) // 3

    @staticmethod
    def max_faults(total_nodes: int) -> int:
        """Alias for :meth:`max_byzantine` — backward compatibility.

        Args:
            total_nodes: Total number of participating nodes.

        Returns:
            The maximum number of faults tolerable.
        """
        return Quorum.max_byzantine(total_nodes)
