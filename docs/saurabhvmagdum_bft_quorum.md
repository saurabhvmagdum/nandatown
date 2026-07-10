# BFT Quorum Consensus

## Overview

This submission replaces the default crash-stop BFT implementation with a new evidence-carrying, rotating-leader BFT protocol. The `saurabhvmagdum_bft_quorum` coordination plugin manages the complex network interactions, signature verification, and Byzantine fault handling, allowing scenario agents to remain simple state machines.

## Architecture

- **`QuorumBFT` Plugin**: Implements the `Coordination` protocol. Generates deterministically signed JSON-like canonical representations for all consensus events.
- **Equivocation Exclusion**: Any validator that submits multiple distinct votes for the same height/round is excluded. A hash of their conflicting votes is recorded as evidence and embedded within the final certificate. The required threshold ($Q = 2f+1$) is strictly enforced irrespective of active exclusions.
- **Round Rotation**: The leader for a round is selected deterministically: `(height + round_id) % total_validators`.
- **Validators**: The trace output is analyzed by `saurabhvmagdum_bft_quorum_validators` which verify protocol invariants: no conflicting commits, valid certificates, non-forged quorums, and liveness (no stuck views).

## Scenarios

- `saurabhvmagdum_bft_quorum_byzantine.yaml`: Tests the resilience of the network with 2 malicious nodes that attempt to equivocate. The honest nodes successfully exclude the malicious nodes and reach consensus.
- `saurabhvmagdum_bft_quorum_partition.yaml`: Tests the behavior of the network under partitions.

## Correctness

All Hypothesis property tests and mock trace validation tests pass, confirming the robustness of the $Q = 2f + 1$ quorum intersection and protocol invariants.
