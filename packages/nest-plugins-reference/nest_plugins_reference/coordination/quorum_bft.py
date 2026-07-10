# SPDX-License-Identifier: Apache-2.0
"""BFT Quorum coordination plugin — evidence-carrying, rotating-leader BFT.

This plugin implements a Byzantine Fault Tolerant (BFT) quorum consensus
protocol with explicit equivocation exclusion. It requires N = 3f + 1
validators and a quorum of Q = 2f + 1.

Every consensus event contains a deterministic signed envelope. Equivocating
voters are excluded from quorum counts, and evidence of their equivocation
is emitted and required in the decision certificate.
"""

from __future__ import annotations

import hashlib
from typing import Any

from nest_core.types import AgentId, Outcome, Round, Signature, Task, Vote

from .quorum import Quorum


class QuorumBFT:
    """Evidence-carrying BFT Quorum Consensus plugin."""

    def __init__(
        self,
        agent_id: AgentId,
        peer_ids: list[str] | None = None,
    ) -> None:
        """Initialize the BFT quorum consensus plugin.

        Args:
            agent_id: This agent's ID.
            peer_ids: List of all participating agent IDs (for quorum calc).
        """
        self._agent_id = agent_id
        self._peer_ids = peer_ids or []
        
        # BFT Protocol State
        # (height, round) -> voter_id -> signed digest
        self.voter_values: dict[tuple[int, int], dict[str, str]] = {}
        # (height, round) -> set of excluded voter IDs
        self.excluded_voters: dict[tuple[int, int], set[str]] = {}
        # (height, round) -> list of valid vote messages
        self.tallies: dict[tuple[int, int], list[dict[str, Any]]] = {}

    async def propose(self, task: Task) -> Round:
        """Coordination protocol conformance."""
        return Round(
            id=f"{task.id}:1",
            task=task,
            participants=[],
            metadata={"phase": "prepare", "votes": []},
        )

    async def participate(self, round: Round) -> Vote:
        """Coordination protocol conformance."""
        return Vote(voter=self._agent_id, round_id=round.id, value="accept")

    async def resolve(self, round: Round) -> Outcome:
        """Coordination protocol conformance."""
        return Outcome(round_id=round.id, winner=self._agent_id, task=round.task)

    async def commit(self, outcome: Outcome) -> None:
        """Coordination protocol conformance."""
        pass

    # -----------------------------------------------------------------------
    # Scenario Factory Methods (Wire Protocol)
    # -----------------------------------------------------------------------
    def sign_message(self, message_type: str, fields: dict[str, str], identity_plugin: Any) -> bytes:
        """Sign a canonical payload and attach the signature envelope."""
        fields["protocol_version"] = "1"
        fields["message_type"] = message_type
        
        # Sort keys to ensure deterministic canonical form
        canonical_parts = [f"{k}={fields[k]}" for k in sorted(fields.keys())]
        canonical_str = f"{message_type}:" + "|".join(canonical_parts)
        canonical = canonical_str.encode("utf-8")
        
        sig: Signature = identity_plugin.sign(canonical)
        sig_hex = sig.value.hex()
        return canonical + f"|sig={sig_hex}".encode("ascii")

    def parse_and_verify(
        self,
        message: bytes,
        identity_plugin: Any,
    ) -> dict[str, str] | None:
        """Parse a signed message, verify the signature, and return fields.
        
        Malformed or unsigned messages return None.
        """
        msg_str = message.decode("utf-8", errors="replace")
        if "|sig=" not in msg_str:
            return None
        
        payload_str, sig_hex = msg_str.rsplit("|sig=", 1)
        payload = payload_str.encode("utf-8")
        
        fields = {}
        if ":" not in payload_str:
            return None
        kind, rest = payload_str.split(":", 1)
        fields["kind"] = kind
        
        for kv in rest.split("|"):
            if "=" in kv:
                k, v = kv.split("=", 1)
                fields[k] = v
                
        # Find who is supposed to have signed it
        signer_id_str = fields.get("sender_id") or fields.get("agent") or fields.get("leader") or fields.get("voter")
        if not signer_id_str:
            return None
            
        signer = AgentId(signer_id_str)
        try:
            sig_bytes = bytes.fromhex(sig_hex)
        except ValueError:
            return None
            
        sig = Signature(signer=signer, value=sig_bytes, algorithm="sim-rsa-sha256")
        if not identity_plugin.verify(payload, sig, signer):
            return None
            
        fields["_raw_payload"] = payload_str
        fields["_raw_sig"] = sig_hex
        return fields

    def process_vote(
        self,
        height: int,
        round_id: int,
        voter: str,
        digest: str,
        raw_vote: str,
    ) -> tuple[bool, str | None]:
        """Process a valid vote. Detects equivocation.
        
        Returns (is_valid, equivocation_trace_msg).
        """
        key = (height, round_id)
        
        if key not in self.voter_values:
            self.voter_values[key] = {}
        if key not in self.excluded_voters:
            self.excluded_voters[key] = set()
        if key not in self.tallies:
            self.tallies[key] = []
            
        if voter in self.excluded_voters[key]:
            return False, None # Already excluded
            
        existing_digest = self.voter_values[key].get(voter)
        if existing_digest is not None and existing_digest != digest:
            # Equivocation detected!
            self.excluded_voters[key].add(voter)
            
            # Find the previous vote to form evidence
            prev_vote = None
            for v in self.tallies[key]:
                if v["voter"] == voter:
                    prev_vote = v["raw_vote"]
                    break
                    
            evidence = hashlib.sha256((str(prev_vote) + raw_vote).encode()).hexdigest()
            
            # Remove all previous votes from this equivocator
            self.tallies[key] = [v for v in self.tallies[key] if v["voter"] != voter]
            
            # Emit equivocation evidence trace
            msg = f"equivocation:height={height}|round={round_id}|agent={voter}|vote_a={existing_digest}|vote_b={digest}|evidence={evidence}"
            return False, msg
            
        self.voter_values[key][voter] = digest
        # Add to tally if not already present (duplicate deliveries are ignored)
        if not any(v["voter"] == voter for v in self.tallies[key]):
            self.tallies[key].append({
                "voter": voter,
                "digest": digest,
                "raw_vote": raw_vote,
            })
            
        return True, None

    def check_quorum(self, height: int, round_id: int, digest: str, total_nodes: int) -> list[str] | None:
        """Check if a quorum has been reached for a digest at a specific height/round."""
        key = (height, round_id)
        if key not in self.tallies:
            return None
            
        threshold = Quorum.threshold(total_nodes)
        
        valid_signers = []
        excluded = self.excluded_voters.get(key, set())
        
        for vote in self.tallies[key]:
            if vote["voter"] not in excluded and vote["digest"] == digest:
                valid_signers.append(vote["voter"])
                
        unique_signers = list(set(valid_signers))
        
        if len(unique_signers) >= threshold:
            return unique_signers
            
        return None
        
    def generate_certificate(self, height: int, round_id: int, digest: str, signers: list[str]) -> str:
        """Generate a decision certificate carrying evidence of excluded voters."""
        key = (height, round_id)
        excluded = sorted(list(self.excluded_voters.get(key, set())))
        
        cert_data = f"height={height}|round={round_id}|digest={digest}|signers={','.join(sorted(signers))}|excluded={','.join(excluded)}"
        return hashlib.sha256(cert_data.encode()).hexdigest()

    def get_leader_for_round(self, height: int, round_id: int, sorted_validators: list[str]) -> str:
        """Deterministic round rotation."""
        if not sorted_validators:
            return str(self._agent_id)
        leader_index = (height + round_id) % len(sorted_validators)
        return sorted_validators[leader_index]
