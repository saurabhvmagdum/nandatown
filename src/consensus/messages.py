"""Message definitions and JSON serialization for NandaQuorum protocol.

Defines the core message types used in the two-phase consensus protocol:
  - PROPOSE: Leader proposes a value at a given height/round.
  - PREPARE_VOTE: Follower votes to prepare the proposed value.
  - COMMIT_VOTE: Follower votes to commit after seeing a Quorum Certificate.
  - QC: Quorum Certificate aggregating PREPARE_VOTE messages.
  - ROUND_CHANGE: Signals a leader rotation / timeout.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any
import json
import time

# Valid message types for protocol enforcement.
VALID_MSG_TYPES = frozenset({
    "PROPOSE",
    "PREPARE_VOTE",
    "COMMIT_VOTE",
    "QC",
    "ROUND_CHANGE",
})


@dataclass
class Message:
    """A single protocol message exchanged between consensus nodes.

    Attributes:
        msg_type: One of PROPOSE, PREPARE_VOTE, COMMIT_VOTE, QC, ROUND_CHANGE.
        height: Logical block / state height being decided.
        round: Consensus round within the height.
        sender: Node ID of the message originator.
        payload: The proposed value, hash, or vote data.
        timestamp: Unix timestamp of message creation.
    """

    msg_type: str
    height: int
    round: int
    sender: str
    payload: Any
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        """Validate message invariants after construction."""
        if self.msg_type not in VALID_MSG_TYPES:
            raise ValueError(
                f"Invalid msg_type '{self.msg_type}'. "
                f"Must be one of {sorted(VALID_MSG_TYPES)}"
            )

    def to_json(self) -> str:
        """Serialize the message to a JSON string."""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, raw: str) -> Message:
        """Deserialize a message from a JSON string.

        Args:
            raw: JSON-encoded message string.

        Returns:
            A new Message instance.

        Raises:
            json.JSONDecodeError: If raw is not valid JSON.
            TypeError: If required fields are missing.
        """
        data = json.loads(raw)
        return cls(**data)

    def validate(self, current_height: int, current_round: int, known_peers: set[str]) -> bool:
        """Validate a message against local protocol state.

        Validation Rules (from spec §3.2):
          1. height must be >= current local height.
          2. round must be >= current local round (within the same height).
          3. sender must be in the known peer list.
          4. msg_type must be one of the allowed types (checked in __post_init__).

        Args:
            current_height: The node's current consensus height.
            current_round: The node's current consensus round.
            known_peers: Set of known node IDs.

        Returns:
            True if the message passes all validation checks.
        """
        if self.height < current_height:
            return False
        if self.height == current_height and self.round < current_round:
            return False
        if self.sender not in known_peers:
            return False
        return True


@dataclass
class QuorumCertificate:
    """Aggregation of PREPARE_VOTE messages that proves quorum was reached.

    A QuorumCertificate (QC) is produced by the leader once it collects
    enough PREPARE_VOTE messages to meet the 2/3 threshold. It is then
    broadcast to all nodes to initiate the COMMIT phase.

    Attributes:
        height: The consensus height this QC covers.
        round: The consensus round this QC covers.
        votes: List of PREPARE_VOTE Message objects forming the certificate.
    """

    height: int
    round: int
    votes: list[Message] = field(default_factory=list)

    def voter_ids(self) -> set[str]:
        """Return the set of unique voter IDs in this QC."""
        return {v.sender for v in self.votes}

    def to_json(self) -> str:
        """Serialize the QC to a JSON string."""
        return json.dumps({
            "height": self.height,
            "round": self.round,
            "votes": [asdict(v) for v in self.votes],
        })

    @classmethod
    def from_json(cls, raw: str) -> QuorumCertificate:
        """Deserialize a QC from a JSON string."""
        data = json.loads(raw)
        votes = [Message(**v) for v in data.get("votes", [])]
        return cls(height=data["height"], round=data["round"], votes=votes)
