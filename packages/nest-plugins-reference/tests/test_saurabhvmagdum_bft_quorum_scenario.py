# SPDX-License-Identifier: Apache-2.0
"""End-to-end tests for BFT Quorum Consensus."""

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest
from nest_core.cli import _run_scenario  # pyright: ignore[reportPrivateUsage]
from nest_core.scenario import ScenarioConfig
from nest_plugins_reference.validators.saurabhvmagdum_bft_quorum_validators import (
    validate_no_conflicting_commits,
    validate_no_equivocation_in_certificate,
    validate_no_forged_quorum,
    validate_no_stuck_view,
)


def _load_trace(path: Path | str) -> list[dict[str, Any]]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def _message_body(ev: dict[str, Any]) -> str:
    return str(ev.get("msg", "")).rsplit("|sig=", 1)[0]


@pytest.mark.asyncio
async def test_byzantine_scenario_passes_validators() -> None:
    """Run the byzantine scenario and assert all validators pass."""
    repo_root = Path(__file__).parent.parent.parent.parent
    path = repo_root / "scenarios" / "saurabhvmagdum_bft_quorum_byzantine.yaml"

    config = ScenarioConfig.from_yaml(path)
    config.duration = "time: 200"

    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
        trace_file = tmp.name
    config.output.trace = trace_file

    trace_path = await _run_scenario(config)
    events = _load_trace(trace_path)

    validators = [
        validate_no_conflicting_commits,
        validate_no_equivocation_in_certificate,
        validate_no_forged_quorum,
        validate_no_stuck_view,
    ]

    for validator in validators:
        results = validator(events)
        for r in results:
            assert r.passed, f"Validator {r.name} failed: {r.detail}"

    equivocation_events = [
        ev
        for ev in events
        if ev.get("kind") == "send" and _message_body(ev).startswith("equivocation:")
    ]
    assert len(equivocation_events) > 0, "No equivocation event observed in trace"

    equivocators: set[str] = set()
    for ev in equivocation_events:
        msg = _message_body(ev)
        parts = dict(kv.split("=", 1) for kv in msg.split(":", 1)[1].split("|") if "=" in kv)
        equivocators.add(parts["agent"])
        assert "evidence" in parts, "Equivocation must contain hash evidence"

    assert len(equivocators) >= 1, "At least one equivocator must be caught"

    commit_events = [
        ev for ev in events if ev.get("kind") == "send" and _message_body(ev).startswith("commit:")
    ]
    assert len(commit_events) > 0, "No commit observed"

    for ev in commit_events:
        msg = _message_body(ev)
        parts = dict(kv.split("=", 1) for kv in msg.split(":", 1)[1].split("|") if "=" in kv)
        signers = parts["signers"].split(",")
        excluded = parts.get("excluded", "").split(",") if parts.get("excluded") else []

        for eq in equivocators:
            assert eq not in signers, f"Equivocator {eq} was included in the commit signers!"
            assert eq in excluded, f"Equivocator {eq} missing from excluded list!"

        assert len(set(signers)) >= 5, (
            f"Commit requires at least 5 non-excluded signers. Got {len(set(signers))}"
        )


@pytest.mark.asyncio
async def test_partition_scenario_passes_validators() -> None:
    """Run the partition scenario and assert all validators pass."""
    repo_root = Path(__file__).parent.parent.parent.parent
    path = repo_root / "scenarios" / "saurabhvmagdum_bft_quorum_partition.yaml"

    config = ScenarioConfig.from_yaml(path)
    config.duration = "time: 200"

    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
        trace_file = tmp.name
    config.output.trace = trace_file

    trace_path = await _run_scenario(config)
    events = _load_trace(trace_path)

    validators = [
        validate_no_conflicting_commits,
        validate_no_equivocation_in_certificate,
        validate_no_forged_quorum,
        validate_no_stuck_view,
    ]

    for validator in validators:
        results = validator(events)
        for r in results:
            assert r.passed, f"Validator {r.name} failed: {r.detail}"

    msgs = [_message_body(ev) for ev in events if ev.get("kind") == "send"]

    has_proposal = any(m.startswith("propose:") for m in msgs)
    has_timeout = any(m.startswith("timeout:") for m in msgs)
    has_commit = any(m.startswith("commit:") for m in msgs)

    assert has_proposal, "Trace must contain a proposal"
    assert has_timeout, "Trace must contain a timeout (partition activation/stalling)"
    assert has_commit, "Trace must contain a post-heal commit"


@pytest.mark.asyncio
async def test_non_bft_trace_fails_validators() -> None:
    """Run a non-BFT scenario and assert validators fail (no commits)."""
    repo_root = Path(__file__).parent.parent.parent.parent
    path = repo_root / "scenarios" / "marketplace.yaml"

    config = ScenarioConfig.from_yaml(path)
    config.duration = "ticks: 10"

    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
        trace_file = tmp.name
    config.output.trace = trace_file

    trace_path = await _run_scenario(config)
    events = _load_trace(trace_path)

    results = validate_no_conflicting_commits(events)
    assert any(not r.passed for r in results), "Expected validator to fail on non-BFT trace."


@pytest.mark.asyncio
async def test_selected_plugin_changes_execution_trace() -> None:
    """Prove the scenario runs the plugin and not an inline fallback."""
    repo_root = Path(__file__).parent.parent.parent.parent
    path = repo_root / "scenarios" / "saurabhvmagdum_bft_quorum_byzantine.yaml"

    config1 = ScenarioConfig.from_yaml(path)
    config1.duration = "ticks: 200"
    config1.seed = 42
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp1:
        config1.output.trace = tmp1.name
    trace_path1 = await _run_scenario(config1)

    config2 = ScenarioConfig.from_yaml(path)
    config2.duration = "time: 200"
    config2.seed = 42
    config2.layers.coordination = "contract_net"  # Override coordination layer correctly

    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp2:
        config2.output.trace = tmp2.name

    try:
        trace_path2 = await _run_scenario(config2)
        with open(trace_path2) as f2:
            baseline_trace = f2.read()
    except Exception as e:
        # Fallback crashes because it lacks BFT features like sign_message or get_leader_for_round
        baseline_trace = str(e)

    with open(trace_path1) as f1:
        quorum_trace = f1.read()

    assert quorum_trace != baseline_trace
    assert "round_change:" in quorum_trace
    assert "equivocation:" in quorum_trace
