# SPDX-License-Identifier: Apache-2.0
"""Hypothesis property tests for BFT Quorum Consensus."""

from hypothesis import given, strategies as st
from nest_plugins_reference.coordination.quorum import Quorum


@given(st.integers(min_value=1, max_value=30))
def test_bft_quorum_intersection_property(f: int) -> None:
    """Ensure any two Q-sized subsets overlap by at least 1 honest node."""
    N = 3 * f + 1
    Q = Quorum.threshold(N)  # Which should be 2f + 1
    
    # In a system of N nodes, two sets of size Q overlap by 2Q - N
    overlap = 2 * Q - N
    
    # We require that even if ALL f faulty nodes are in the overlap,
    # there is at least one honest node in the overlap.
    honest_overlap = overlap - f
    
    assert honest_overlap >= 1, f"Overlap fails for f={f}, N={N}, Q={Q}"

@given(st.integers(min_value=4, max_value=100))
def test_bft_quorum_threshold(total: int) -> None:
    """Ensure threshold calculation works for arbitrary sizes."""
    # N = 3f + x (x can be 1, 2, 3)
    f = (total - 1) // 3
    Q = Quorum.threshold(total)
    
    # The threshold must be exactly 2f + 1
    assert Q == 2 * f + 1
