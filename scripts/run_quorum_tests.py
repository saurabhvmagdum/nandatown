#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run all NandaQuorum scenarios, validate traces, and produce a comparison report.

Usage::

    python scripts/run_quorum_tests.py

Runs four scenarios (baseline, stress, drops, byzantine), validates each
trace against the built-in consensus validators, and prints a comparison
table showing which invariants hold under each failure mode.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nest_core.runner import ScenarioRunner
from nest_core.scenario import ScenarioConfig
from nest_core.validators import validate_trace


SCENARIOS = [
    ("quorum_baseline", "scenarios/quorum_baseline.yaml"),
    ("quorum_stress", "scenarios/quorum_stress.yaml"),
    ("quorum_drops", "scenarios/quorum_drops.yaml"),
    ("quorum_byzantine", "scenarios/quorum_byzantine.yaml"),
]

HEADER = (
    f"{'Scenario':<25} | {'Agents':>6} | {'Drop%':>5} | {'Byz%':>4} "
    f"| {'Ticks':>6} | {'Msgs':>5} | {'Drops':>5} "
    f"| {'Agreement':>10} | {'Validity':>10} | {'No-Conflict':>12}"
)
SEP = "-" * len(HEADER)


async def run_scenario(name: str, yaml_path: str) -> dict:
    """Run a single scenario and return results."""
    print(f"\n{'='*60}")
    print(f"  Running: {name}")
    print(f"  Config:  {yaml_path}")
    print(f"{'='*60}")

    config = ScenarioConfig.from_yaml(yaml_path)
    runner = ScenarioRunner(config)
    trace_path = await runner.run()

    print(f"  Trace:   {trace_path}")
    print(f"  Ticks:   {runner._config.get_max_ticks()}")

    # Validate the trace
    results = validate_trace(trace_path, "consensus")

    validator_results = {}
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        validator_results[r.name] = status
        print(f"  [{status}] {r.name}: {r.detail}")

    # Count trace events
    event_count = 0
    msg_count = 0
    drop_count = 0
    with trace_path.open() as f:
        import json
        for line in f:
            line = line.strip()
            if line:
                ev = json.loads(line)
                event_count += 1
                if ev.get("kind") == "send":
                    msg_count += 1
                elif ev.get("kind") == "dropped":
                    drop_count += 1

    return {
        "name": name,
        "agents": config.agents.count,
        "drop_rate": config.failures.message_drop,
        "byzantine": config.failures.byzantine_agents,
        "ticks": event_count,
        "msgs": msg_count,
        "drops": drop_count,
        "agreement": validator_results.get("consensus_agreement", "N/A"),
        "validity": validator_results.get("consensus_validity", "N/A"),
        "no_conflict": validator_results.get("consensus_no_conflict", "N/A"),
    }


async def main() -> None:
    """Run all scenarios and print comparison table."""
    print("\n" + "=" * 60)
    print("  NandaQuorum Protocol Test Suite")
    print("  Testing: 2/3 quorum consensus under various failure modes")
    print("=" * 60)

    all_results = []
    for name, yaml_path in SCENARIOS:
        try:
            result = await run_scenario(name, yaml_path)
            all_results.append(result)
        except Exception as e:
            print(f"\n  ERROR running {name}: {e}")
            all_results.append({
                "name": name,
                "agents": "?",
                "drop_rate": "?",
                "byzantine": "?",
                "ticks": "?",
                "msgs": "?",
                "drops": "?",
                "agreement": "ERROR",
                "validity": "ERROR",
                "no_conflict": "ERROR",
            })

    # Print comparison table
    print(f"\n\n{'='*60}")
    print("  COMPARISON TABLE")
    print(f"{'='*60}\n")
    print(HEADER)
    print(SEP)

    for r in all_results:
        drop_pct = f"{float(r['drop_rate'])*100:.0f}%" if r['drop_rate'] != "?" else "?"
        byz_pct = f"{float(r['byzantine'])*100:.0f}%" if r['byzantine'] != "?" else "?"
        print(
            f"{r['name']:<25} | {r['agents']:>6} | {drop_pct:>5} | {byz_pct:>4} "
            f"| {r['ticks']:>6} | {r['msgs']:>5} | {r['drops']:>5} "
            f"| {r['agreement']:>10} | {r['validity']:>10} | {r['no_conflict']:>12}"
        )

    print(f"\n{'='*60}")

    # Summary
    total_pass = sum(
        1 for r in all_results
        for v in [r["agreement"], r["validity"], r["no_conflict"]]
        if v == "PASS"
    )
    total_fail = sum(
        1 for r in all_results
        for v in [r["agreement"], r["validity"], r["no_conflict"]]
        if v == "FAIL"
    )
    total_checks = total_pass + total_fail
    print(f"  Total checks: {total_checks}  |  PASS: {total_pass}  |  FAIL: {total_fail}")

    if total_fail == 0:
        print("  [OK] All protocol invariants held across all failure modes!")
    else:
        print(f"  [WARNING] {total_fail} invariant(s) violated — see details above.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
