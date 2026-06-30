# NandaQuorum — Formal Protocol Specification

> **Protocol**: Two-Phase Quorum Consensus  
> **Version**: 1.0  
> **Fault Model**: Crash-stop (non-Byzantine)

---

## 1. System Model

### 1.1 Participants
- A set of **N** nodes: `{n₁, n₂, …, nₙ}`
- Each node runs the same deterministic state machine.
- Nodes communicate via asynchronous, reliable (non-lossy) message passing.
- Nodes may crash (halt) but do not behave maliciously.

### 1.2 Quorum
- Quorum threshold: `Q = ⌊2N/3⌋ + 1`
- The protocol tolerates up to `F = N - Q` crash faults.

### 1.3 Assumptions
- Network is eventually synchronous (messages are delivered within a bounded time after GST).
- Nodes have synchronized clocks (sufficient for timeout coordination).
- No Sybil attacks — node identities are pre-configured.

---

## 2. Protocol Phases

### 2.1 Phase 1: PREPARE

1. **PROPOSE**: The leader `L(h, r)` for height `h` and round `r` broadcasts:
   ```
   PROPOSE(value, height=h, round=r, sender=L)
   ```

2. **PREPARE_VOTE**: Each follower node, upon receiving a valid PROPOSE, responds to the leader:
   ```
   PREPARE_VOTE(height=h, round=r, sender=nᵢ)
   ```

3. **Quorum Certificate (QC)**: The leader collects PREPARE_VOTEs. Once `|votes| ≥ Q`, it forms a Quorum Certificate and broadcasts:
   ```
   QC(height=h, round=r, votes=[v₁, v₂, …, vQ])
   ```

### 2.2 Phase 2: COMMIT

4. **COMMIT_VOTE**: Each follower, upon receiving a valid QC, sends a commit vote to the leader:
   ```
   COMMIT_VOTE(height=h, round=r, sender=nᵢ)
   ```

5. **Finalization**: The leader collects COMMIT_VOTEs. Once `|votes| ≥ Q`, the value is **committed**:
   - The committed value is applied to the local state.
   - A NEW_HEIGHT message is broadcast to all nodes.

### 2.3 Timeout & Leader Rotation

6. If the leader fails to form a QC within `PHASE_TIMEOUT` seconds:
   - All nodes increment their round: `r ← r + 1`
   - A new leader `L(h, r+1)` is selected via round-robin.
   - The new leader re-proposes the pending value.

7. If `r ≥ MAX_ROUNDS`, the height is aborted (stalled safely).

---

## 3. Safety Properties

### 3.1 Agreement
No two honest nodes commit different values at the same height.

**Proof sketch**: A value can only be committed if it receives `Q ≥ ⌊2N/3⌋ + 1` COMMIT votes. Since two quorums must overlap by at least one honest node, conflicting values cannot both achieve quorum.

### 3.2 Validity
If a value is committed, it was proposed by some leader.

### 3.3 Integrity
Each node commits at most one value per height.

---

## 4. Liveness Properties

### 4.1 Termination
If fewer than `F` nodes have crashed and the network is synchronous, then every proposed value is eventually committed.

**Mechanism**: Timeout-driven leader rotation ensures that a live leader is eventually selected within `MAX_ROUNDS` rounds.

---

## 5. Leader Selection

Leader selection uses deterministic round-robin:
```
L(h, r) = nodes[r mod N]
```
where `nodes` is a sorted list of all node IDs.

This ensures:
- All nodes agree on the leader for any given round.
- Every live node gets a chance to lead within N rounds.

---

## 6. Message Validation Rules

A message `m` is valid if and only if:
1. `m.height ≥ local.height`
2. `m.height == local.height → m.round ≥ local.round`
3. `m.sender ∈ known_peers`
4. `m.msg_type ∈ {PROPOSE, PREPARE_VOTE, COMMIT_VOTE, QC, ROUND_CHANGE}`

---

## 7. Complexity Analysis

| Metric | Happy Path | With f Faults |
|--------|-----------|---------------|
| Message complexity | 3N (PROPOSE + PREPARE + QC + COMMIT + ACK) | (f+1) × 3N |
| Round complexity | 1 round | f+1 rounds |
| Latency | 2 × network RTT | (f+1) × (2 RTT + timeout) |

---

## 8. Comparison with Full BFT

| Property | NandaQuorum | PBFT |
|----------|-------------|------|
| Fault model | Crash-stop | Byzantine |
| Quorum | 2/3 | 2/3 |
| Phases | 2 | 3 (pre-prepare, prepare, commit) |
| Cryptography | None | Signatures, MACs |
| Complexity | O(N) | O(N²) |
| Suitability | Trusted agents | Untrusted networks |

---

*This specification accompanies the NandaQuorum implementation in `src/consensus/`.*
