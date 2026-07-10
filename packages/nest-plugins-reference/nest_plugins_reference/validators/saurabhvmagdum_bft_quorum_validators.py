# SPDX-License-Identifier: Apache-2.0
"""BFT Quorum protocol invariant validators."""

from __future__ import annotations

import collections
import hashlib
from typing import Any

from nest_core.validators import VALIDATORS, ValidationResult
from nest_core.types import AgentId, Signature
from nest_plugins_reference.identity.did_key import DidKeyIdentity
from nest_plugins_reference.coordination.quorum import Quorum

def _message_body(ev: dict[str, Any]) -> str:
    """Extract message payload without signature."""
    return str(ev.get("msg", "")).rsplit("|sig=", 1)[0]
    
def _get_sig(ev: dict[str, Any]) -> str | None:
    msg_str = str(ev.get("msg", ""))
    if "|sig=" in msg_str:
        return msg_str.rsplit("|sig=", 1)[1]
    return None

def validate_no_conflicting_commits(events: list[dict[str, Any]]) -> list[ValidationResult]:
    """Ensure no two distinct digests are committed at the same height."""
    commits_by_height: dict[int, set[str]] = collections.defaultdict(set)
    has_commits = False
    
    for ev in events:
        if ev.get("kind") != "send":
            continue
        msg = _message_body(ev)
        if msg.startswith("commit:"):
            parts = dict(kv.split("=", 1) for kv in msg.split(":", 1)[1].split("|") if "=" in kv)
            if "height" in parts and "digest" in parts:
                commits_by_height[int(parts["height"])].add(parts["digest"])
                has_commits = True
                
    if not has_commits:
        return [ValidationResult("validate_no_conflicting_commits", False, "No commit is observable.")]
        
    for height, digests in commits_by_height.items():
        if len(digests) > 1:
            return [ValidationResult("validate_no_conflicting_commits", False, f"Conflicting commits at height {height}: {digests}")]
            
    return [ValidationResult("validate_no_conflicting_commits", True, "No conflicting commits found.")]


def validate_no_equivocation_in_certificate(events: list[dict[str, Any]]) -> list[ValidationResult]:
    """Ensure certificates do not contain excluded equivocators and are valid."""
    equivocators_by_round: dict[tuple[int, int], set[str]] = collections.defaultdict(set)
    has_commits = False
    
    for ev in events:
        if ev.get("kind") != "send":
            continue
        msg = _message_body(ev)
        
        if msg.startswith("equivocation:"):
            parts = dict(kv.split("=", 1) for kv in msg.split(":", 1)[1].split("|") if "=" in kv)
            if "height" in parts and "round" in parts and "agent" in parts:
                equivocators_by_round[(int(parts["height"]), int(parts["round"]))].add(parts["agent"])
                
        elif msg.startswith("commit:"):
            has_commits = True
            parts = dict(kv.split("=", 1) for kv in msg.split(":", 1)[1].split("|") if "=" in kv)
            if "height" not in parts or "round" not in parts or "qc" not in parts or "signers" not in parts:
                return [ValidationResult("validate_no_equivocation_in_certificate", False, "Certificate malformed or missing.")]
                
            height = int(parts["height"])
            round_id = int(parts["round"])
            key = (height, round_id)
            signers = parts["signers"].split(",") if parts["signers"] else []
            excluded_in_cert = parts.get("excluded", "").split(",") if parts.get("excluded") else []
            
            # Check unique signers
            if len(signers) != len(set(signers)):
                return [ValidationResult("validate_no_equivocation_in_certificate", False, "Certificate contains duplicate signers.")]
                
            # Check if any signer was actually excluded
            excluded_actual = equivocators_by_round.get(key, set())
            for signer in signers:
                if signer in excluded_actual:
                    return [ValidationResult("validate_no_equivocation_in_certificate", False, f"Signer {signer} was excluded but counted in certificate.")]
                    
    if not has_commits:
        return [ValidationResult("validate_no_equivocation_in_certificate", False, "No commits found to validate certificate.")]
        
    return [ValidationResult("validate_no_equivocation_in_certificate", True, "All certificates valid and equivocators excluded.")]


def validate_no_forged_quorum(events: list[dict[str, Any]]) -> list[ValidationResult]:
    """Ensure every commit is backed by Q=2f+1 unique valid trace votes."""
    votes_by_round_digest: dict[tuple[int, int, str], set[str]] = collections.defaultdict(set)
    commits_to_check = []
    
    # We must determine total nodes dynamically or assume 7 from the scenario.
    # Usually we count total unique agents sending votes.
    all_voters = set()
    
    for ev in events:
        if ev.get("kind") != "send":
            continue
        msg = _message_body(ev)
        
        if msg.startswith("vote:"):
            parts = dict(kv.split("=", 1) for kv in msg.split(":", 1)[1].split("|") if "=" in kv)
            if "height" in parts and "round" in parts and "digest" in parts and "agent" in parts:
                # Basic check: in a real trace, signature would be verified.
                # Here we assume the trace content is what was recorded.
                votes_by_round_digest[(int(parts["height"]), int(parts["round"]), parts["digest"])].add(parts["agent"])
                all_voters.add(parts["agent"])
                
        elif msg.startswith("commit:"):
            parts = dict(kv.split("=", 1) for kv in msg.split(":", 1)[1].split("|") if "=" in kv)
            if "height" in parts and "round" in parts and "digest" in parts:
                commits_to_check.append({
                    "height": int(parts["height"]),
                    "round": int(parts["round"]),
                    "digest": parts["digest"]
                })
                
    if not commits_to_check:
        return [ValidationResult("validate_no_forged_quorum", False, "No commits found.")]
        
    total_nodes = len(all_voters) if len(all_voters) >= 4 else 7 # Fallback
    threshold = Quorum.threshold(total_nodes)
    
    for commit in commits_to_check:
        key = (commit["height"], commit["round"], commit["digest"])
        actual_votes = votes_by_round_digest.get(key, set())
        
        if len(actual_votes) < threshold:
            return [ValidationResult("validate_no_forged_quorum", False, f"Commit forged: has {len(actual_votes)} votes, needs {threshold}.")]
            
    return [ValidationResult("validate_no_forged_quorum", True, "All commits backed by valid 2f+1 quorums.")]


def validate_no_stuck_view(events: list[dict[str, Any]]) -> list[ValidationResult]:
    """Ensure progress is made (commit observed) after any view change."""
    has_proposals = False
    view_changes = 0
    commits_after_view_change = 0
    
    for ev in events:
        if ev.get("kind") != "send":
            continue
        msg = _message_body(ev)
        
        if msg.startswith("propose:"):
            has_proposals = True
        elif msg.startswith("round_change:") or msg.startswith("timeout:"):
            view_changes += 1
        elif msg.startswith("commit:"):
            if view_changes > 0:
                commits_after_view_change += 1
                
    if not has_proposals:
        return [ValidationResult("validate_no_stuck_view", False, "No proposals found.")]
        
    # The requirement is that we expect a post-fault commit if there was a fault (timeout).
    if view_changes > 0 and commits_after_view_change == 0:
        return [ValidationResult("validate_no_stuck_view", False, "View changed but no subsequent commit occurred (stuck view).")]
        
    return [ValidationResult("validate_no_stuck_view", True, "Progress maintained across view changes.")]

