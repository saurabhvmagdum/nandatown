# SPDX-License-Identifier: Apache-2.0
"""Adversarial BFT validators for the quorum consensus protocol.

Four validators targeting Byzantine fault tolerance properties that the
default ``contract_net`` plugin trivially fails:

1. **Conflicting commits**: two honest agents committing different
   values in the same round.
2. **Equivocation**: a leader sending different proposals to different
   followers in the same round.
3. **Forged quorum**: a ``commit`` event in the trace not backed by
   ``>= 2f+1`` signed votes from distinct agents.
4. **Stuck view**: no commit progress for K rounds after the network
   is healed.

By construction:

* Against the **quorum_consensus** BFT plugin, all four pass.
* Against the **contract_net** plugin, all four fail — the validator
  literally cannot be satisfied by the reference plugin, which is the
  charter's bar for "adversarial".

Example::

    from nest_plugins_reference.validators.bft_validators import (
        check_no_conflicting_commits,
        check_no_equivocation,
        check_no_forged_quorum,
        check_no_stuck_view,
    )

    report = check_no_conflicting_commits(events)
    assert report.passed, report.detail
"""

from __future__ import annotations

import contextlib
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, cast


@dataclass
class BftValidatorReport:
    """Pass/fail report with a short human-readable explanation.

    Example::

        report = BftValidatorReport(passed=True, detail="no conflicting commits")
        assert report.passed, report.detail
    """

    passed: bool
    detail: str
    evidence: dict[str, Any] = field(default_factory=lambda: cast(dict[str, Any], {}))


class BftValidationError(AssertionError):
    """Raised when a BFT invariant is violated.

    Example::

        raise BftValidationError("conflicting commits in round 3")
    """


def _message_body(ev: dict[str, Any]) -> str:
    """Return payload text without the signature suffix."""
    return str(ev.get("msg", "")).rsplit("|sig:", 1)[0]


def check_no_conflicting_commits(
    events: list[dict[str, Any]],
) -> BftValidatorReport:
    """Assert no two honest agents commit different values in the same round.

    Scans the trace for ``result:{round}:committed:...:{value}`` messages.
    If two different values are committed for the same round, safety is
    violated.

    Example::

        report = check_no_conflicting_commits(events)
        assert report.passed, report.detail
    """
    # round -> set of committed values
    committed_values: dict[str, set[str]] = defaultdict(set)

    for ev in events:
        if ev.get("kind") != "send":
            continue
        msg = _message_body(ev)
        if not msg.startswith("result:"):
            continue
        parts = msg.split(":")
        if len(parts) >= 5 and parts[2] == "committed":
            rnd = parts[1]
            value = parts[4]
            committed_values[rnd].add(value)

    conflicts: list[str] = []
    for rnd, values in committed_values.items():
        if len(values) > 1:
            conflicts.append(f"round {rnd}: conflicting values {values}")

    if conflicts:
        return BftValidatorReport(
            passed=False,
            detail=f"{len(conflicts)} round(s) with conflicting commits",
            evidence={"conflicts": conflicts[:20]},
        )
    checked = sum(1 for vs in committed_values.values() if len(vs) == 1)
    return BftValidatorReport(
        passed=True,
        detail=f"no conflicting commits across {checked} committed round(s)",
    )


def check_no_equivocation(
    events: list[dict[str, Any]],
) -> BftValidatorReport:
    """Assert the leader did not send different proposals to different followers.

    Scans the trace for ``propose:{round}:{value}`` messages from the same
    sender.  If the leader proposes different values to different followers
    in the same round, equivocation is detected.

    Example::

        report = check_no_equivocation(events)
        assert report.passed, report.detail
    """
    # round -> sender -> set of proposed values
    proposals: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))

    for ev in events:
        if ev.get("kind") != "send":
            continue
        msg = _message_body(ev)
        if not msg.startswith("propose:"):
            continue
        parts = msg.split(":")
        if len(parts) >= 3:
            rnd = parts[1]
            value = parts[2]
            sender = str(ev.get("agent", ev.get("sender", "")))
            proposals[rnd][sender].add(value)

    equivocations: list[str] = []
    for rnd, senders in proposals.items():
        for sender, values in senders.items():
            if len(values) > 1:
                equivocations.append(
                    f"round {rnd}: {sender} proposed {len(values)} different values: {values}"
                )

    if equivocations:
        return BftValidatorReport(
            passed=False,
            detail=f"{len(equivocations)} equivocation(s) detected",
            evidence={"equivocations": equivocations[:20]},
        )
    return BftValidatorReport(
        passed=True,
        detail=f"no leader equivocation across {len(proposals)} round(s)",
    )


def check_no_forged_quorum(
    events: list[dict[str, Any]],
    *,
    total_agents: int | None = None,
) -> BftValidatorReport:
    """Assert every committed round is backed by >= 2f+1 votes from distinct agents.

    Scans the trace for ``vote:{round}:accept`` messages and verifies
    that each committed round has enough genuine accept votes to meet the
    BFT quorum threshold.

    Args:
        events: List of trace events.
        total_agents: Total agent count (for computing ``f``).  If ``None``,
            inferred from unique senders in the trace.

    Example::

        report = check_no_forged_quorum(events, total_agents=7)
        assert report.passed, report.detail
    """
    # Infer total agents if not given
    if total_agents is None:
        all_agents: set[str] = set()
        for ev in events:
            agent = str(ev.get("agent", ev.get("sender", "")))
            if agent:
                all_agents.add(agent)
            target = str(ev.get("target", ev.get("target_id", "")))
            if target:
                all_agents.add(target)
        total_agents = max(len(all_agents), 1)

    f = (total_agents - 1) // 3
    threshold = 2 * f + 1

    # round -> set of distinct voters who accepted
    accept_voters: dict[str, set[str]] = defaultdict(set)
    committed_rounds: set[str] = set()

    for ev in events:
        if ev.get("kind") != "send":
            continue
        msg = _message_body(ev)
        if msg.startswith("vote:"):
            parts = msg.split(":")
            if len(parts) >= 3 and parts[2] == "accept":
                rnd = parts[1]
                voter = str(ev.get("agent", ev.get("sender", "")))
                accept_voters[rnd].add(voter)
        elif msg.startswith("result:"):
            parts = msg.split(":")
            if len(parts) >= 3 and parts[2] == "committed":
                committed_rounds.add(parts[1])

    forged: list[str] = []
    for rnd in committed_rounds:
        voters = accept_voters.get(rnd, set())
        if len(voters) < threshold:
            forged.append(
                f"round {rnd}: committed with only {len(voters)} accept votes "
                f"(need {threshold} for n={total_agents})"
            )

    if forged:
        return BftValidatorReport(
            passed=False,
            detail=f"{len(forged)} round(s) with forged/insufficient quorum",
            evidence={"forged_rounds": forged[:20]},
        )
    return BftValidatorReport(
        passed=True,
        detail=(
            f"all {len(committed_rounds)} committed round(s) backed by "
            f">= {threshold} distinct votes (n={total_agents}, f={f})"
        ),
    )


def check_no_stuck_view(
    events: list[dict[str, Any]],
    *,
    max_rounds_without_commit: int = 10,
) -> BftValidatorReport:
    """Assert the protocol makes progress — commits happen within bounded rounds.

    Checks that no window of ``max_rounds_without_commit`` consecutive
    rounds passes without a commit.  This is a liveness check: in the
    absence of partition, the protocol must make progress.

    Args:
        events: List of trace events.
        max_rounds_without_commit: Maximum rounds allowed without any commit
            before declaring a stuck view.  Default 10.

    Example::

        report = check_no_stuck_view(events, max_rounds_without_commit=5)
        assert report.passed, report.detail
    """
    # Collect all round numbers that had proposals and commits
    proposed_rounds: set[int] = set()
    committed_rounds: set[int] = set()

    for ev in events:
        if ev.get("kind") != "send":
            continue
        msg = _message_body(ev)
        if msg.startswith("propose:"):
            parts = msg.split(":")
            if len(parts) >= 2:
                with contextlib.suppress(ValueError):
                    proposed_rounds.add(int(parts[1]))
        elif msg.startswith("result:"):
            parts = msg.split(":")
            if len(parts) >= 3 and parts[2] == "committed":
                with contextlib.suppress(ValueError):
                    committed_rounds.add(int(parts[1]))

    if not proposed_rounds:
        return BftValidatorReport(
            passed=True,
            detail="no proposals observed — nothing to check",
        )

    if not committed_rounds:
        if len(proposed_rounds) <= max_rounds_without_commit:
            return BftValidatorReport(
                passed=True,
                detail=(
                    f"no commits but only {len(proposed_rounds)} round(s) proposed "
                    f"(<= {max_rounds_without_commit} threshold)"
                ),
            )
        return BftValidatorReport(
            passed=False,
            detail=(
                f"no commits across {len(proposed_rounds)} round(s) proposed "
                f"(exceeds {max_rounds_without_commit} threshold)"
            ),
        )

    # Check for gaps between commits that exceed the threshold
    min_rnd = min(proposed_rounds)
    max_rnd = max(proposed_rounds)
    last_commit = min_rnd - 1
    stuck_windows: list[str] = []

    for rnd in range(min_rnd, max_rnd + 1):
        if rnd in committed_rounds:
            last_commit = rnd
        elif rnd - last_commit > max_rounds_without_commit:
            stuck_windows.append(
                f"rounds {last_commit + 1}–{rnd}: "
                f"{rnd - last_commit} rounds without commit"
            )

    if stuck_windows:
        return BftValidatorReport(
            passed=False,
            detail=f"{len(stuck_windows)} stuck window(s) detected",
            evidence={"stuck_windows": stuck_windows[:10]},
        )
    return BftValidatorReport(
        passed=True,
        detail=(
            f"protocol made progress — {len(committed_rounds)} commit(s) "
            f"across rounds {min_rnd}–{max_rnd}"
        ),
    )
