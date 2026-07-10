# SPDX-License-Identifier: Apache-2.0
"""Baseline failure tests for BFT Quorum Validators."""

from typing import Any
from nest_plugins_reference.validators.saurabhvmagdum_bft_quorum_validators import (
    validate_no_conflicting_commits,
    validate_no_equivocation_in_certificate,
    validate_no_forged_quorum,
    validate_no_stuck_view,
)


def _mock_event(msg: str) -> dict[str, Any]:
    return {"kind": "send", "msg": msg}


def test_no_conflicting_commits_fails() -> None:
    events = [
        _mock_event("commit:height=1|round=1|digest=A|qc=cert|signers=a,b|excluded="),
        _mock_event("commit:height=1|round=2|digest=B|qc=cert2|signers=c,d|excluded="),
    ]
    results = validate_no_conflicting_commits(events)
    assert not all(r.passed for r in results)


def test_no_equivocation_in_certificate_fails() -> None:
    events = [
        _mock_event("equivocation:height=1|round=1|agent=a1|vote_a=X|vote_b=Y|evidence=123"),
        # Certificate counts a1 even though they were excluded in this round
        _mock_event("commit:height=1|round=1|digest=A|qc=cert|signers=a1,a2,a3|excluded=a1"),
    ]
    results = validate_no_equivocation_in_certificate(events)
    assert not all(r.passed for r in results)


def test_no_forged_quorum_fails() -> None:
    events = [
        # Only 2 votes but needs 2f+1 (assume scenario has 4 nodes minimum, needs 3)
        _mock_event("vote:height=1|round=1|digest=A|agent=a1"),
        _mock_event("vote:height=1|round=1|digest=A|agent=a2"),
        _mock_event("commit:height=1|round=1|digest=A|qc=cert|signers=a1,a2|excluded="),
    ]
    results = validate_no_forged_quorum(events)
    assert not all(r.passed for r in results)


def test_no_stuck_view_fails() -> None:
    events = [
        _mock_event("propose:height=1|round=1|digest=A|leader=a1"),
        _mock_event("timeout:height=1|round=1|agent=a1"),
        _mock_event("round_change:height=1|round=2|agent=a1|highest_qc=none"),
        # View changes but no subsequent commit occurs in the trace
    ]
    results = validate_no_stuck_view(events)
    assert not all(r.passed for r in results)
