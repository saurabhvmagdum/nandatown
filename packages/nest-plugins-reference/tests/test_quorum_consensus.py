"""Unit and integration tests for the NandaQuorum BFT consensus protocol.

Covers:
  - BFT quorum threshold math (Section 6.1)
  - Quorum validation and max_byzantine
  - Coordination plugin: propose, participate, resolve, commit
  - Equivocation detection
  - Deterministic round IDs (no uuid.uuid4)
  - BFT adversarial validators
  - Scenario factory: honest and Byzantine agents
"""

from __future__ import annotations

from typing import Any

import pytest
from nest_core.types import AgentId, Task
from nest_plugins_reference.coordination.quorum import Quorum
from nest_plugins_reference.coordination.quorum_consensus import QuorumConsensus
from nest_plugins_reference.validators.bft_validators import (
    check_no_conflicting_commits,
    check_no_equivocation,
    check_no_forged_quorum,
    check_no_stuck_view,
)

# ──────────────────────────────────────────────────────────
# 6.1 Unit Tests — BFT Quorum Math
# ──────────────────────────────────────────────────────────


class TestQuorumThreshold:
    """Test BFT quorum threshold computation (2f+1 out of 3f+1)."""

    def test_threshold_1(self):
        """n=1: f=0, threshold=1."""
        assert Quorum.threshold(1) == 1

    def test_threshold_4(self):
        """n=4: f=1, threshold=3."""
        assert Quorum.threshold(4) == 3

    def test_threshold_7(self):
        """n=7: f=2, threshold=5."""
        assert Quorum.threshold(7) == 5

    def test_threshold_10(self):
        """n=10: f=3, threshold=7."""
        assert Quorum.threshold(10) == 7

    def test_threshold_13(self):
        """n=13: f=4, threshold=9."""
        assert Quorum.threshold(13) == 9

    def test_threshold_invalid(self):
        with pytest.raises(ValueError):
            Quorum.threshold(0)


class TestIsQuorum:
    """Test quorum validation with vote sets."""

    def test_quorum_met_4_nodes(self):
        """4 nodes, threshold=3, 3 votes => quorum."""
        votes = ["A", "B", "C"]
        assert Quorum.is_quorum(votes, 4) is True

    def test_quorum_not_met_4_nodes(self):
        """4 nodes, threshold=3, 2 votes => no quorum."""
        votes = ["A", "B"]
        assert Quorum.is_quorum(votes, 4) is False

    def test_quorum_with_duplicates(self):
        """Duplicate votes should be deduplicated."""
        votes = ["A", "A", "B", "C"]
        assert Quorum.is_quorum(votes, 4) is True

    def test_quorum_exact_threshold_7(self):
        """7 nodes, threshold=5, exactly 5 votes => quorum."""
        votes = ["A", "B", "C", "D", "E"]
        assert Quorum.is_quorum(votes, 7) is True

    def test_quorum_below_threshold_7(self):
        """7 nodes, threshold=5, only 4 votes => no quorum."""
        votes = ["A", "B", "C", "D"]
        assert Quorum.is_quorum(votes, 7) is False

    def test_max_byzantine(self):
        """Test max_byzantine (f) computation."""
        assert Quorum.max_byzantine(4) == 1
        assert Quorum.max_byzantine(7) == 2
        assert Quorum.max_byzantine(10) == 3
        assert Quorum.max_byzantine(13) == 4

    def test_max_faults_alias(self):
        """max_faults is an alias for max_byzantine."""
        assert Quorum.max_faults(4) == Quorum.max_byzantine(4)
        assert Quorum.max_faults(7) == Quorum.max_byzantine(7)


# ──────────────────────────────────────────────────────────
# Coordination Plugin Tests
# ──────────────────────────────────────────────────────────


class TestQuorumConsensusPlugin:
    """Test the QuorumConsensus coordination plugin."""

    @pytest.mark.asyncio
    async def test_propose_creates_round(self):
        """propose() should create a round with BFT metadata."""
        coord = QuorumConsensus(AgentId("a0"), ["a0", "a1", "a2", "a3"])
        task = Task(id="t1", description="assign work")
        rnd = await coord.propose(task)

        assert rnd.id == "t1:1"  # deterministic, not uuid4
        assert rnd.metadata["quorum_threshold"] == 3  # 2*1+1 for n=4
        assert rnd.metadata["total_nodes"] == 4
        assert rnd.metadata["max_byzantine"] == 1
        assert rnd.metadata["phase"] == "prepare"

    @pytest.mark.asyncio
    async def test_deterministic_round_ids(self):
        """Round IDs should be deterministic — no uuid.uuid4()."""
        coord = QuorumConsensus(AgentId("a0"), ["a0", "a1"])
        task1 = Task(id="t1", description="work1")
        task2 = Task(id="t2", description="work2")

        rnd1 = await coord.propose(task1)
        rnd2 = await coord.propose(task2)

        assert rnd1.id == "t1:1"
        assert rnd2.id == "t2:2"

    @pytest.mark.asyncio
    async def test_participate_adds_vote(self):
        """participate() should add a vote to round metadata."""
        coord = QuorumConsensus(AgentId("a1"), ["a0", "a1", "a2", "a3"])
        task = Task(id="t1", description="work")
        rnd = await coord.propose(task)

        vote = await coord.participate(rnd)
        from nest_core.types import Vote

        assert isinstance(vote, Vote)
        assert vote.value == "accept"
        assert len(rnd.metadata["votes"]) == 1
        assert rnd.metadata["votes"][0]["voter"] == "a1"

    @pytest.mark.asyncio
    async def test_equivocation_detected(self):
        """Duplicate participation by the same agent should flag equivocation."""
        coord = QuorumConsensus(AgentId("a1"), ["a0", "a1", "a2", "a3"])
        task = Task(id="t1", description="work")
        rnd = await coord.propose(task)

        await coord.participate(rnd)  # first vote
        await coord.participate(rnd)  # equivocation!

        assert "a1" in rnd.metadata["equivocations"]
        # Only one genuine vote should be counted
        assert len(rnd.metadata["votes"]) == 1

    @pytest.mark.asyncio
    async def test_resolve_quorum_reached(self):
        """resolve() with enough votes should reach quorum."""
        peers = ["a0", "a1", "a2", "a3"]
        task = Task(id="t1", description="work")

        # Have 3 different agents participate (threshold=3 for n=4)
        proposer = QuorumConsensus(AgentId("a0"), peers)
        rnd = await proposer.propose(task)

        for aid in ["a1", "a2", "a3"]:
            voter = QuorumConsensus(AgentId(aid), peers)
            await voter.participate(rnd)

        outcome = await proposer.resolve(rnd)
        assert outcome.metadata["quorum_reached"] is True
        assert outcome.metadata["accept_count"] == 3

    @pytest.mark.asyncio
    async def test_resolve_quorum_not_reached(self):
        """resolve() without enough votes should not reach quorum."""
        peers = ["a0", "a1", "a2", "a3"]
        task = Task(id="t1", description="work")

        proposer = QuorumConsensus(AgentId("a0"), peers)
        rnd = await proposer.propose(task)

        # Only 1 voter (threshold=3)
        voter = QuorumConsensus(AgentId("a1"), peers)
        await voter.participate(rnd)

        outcome = await proposer.resolve(rnd)
        assert outcome.metadata["quorum_reached"] is False

    @pytest.mark.asyncio
    async def test_resolve_excludes_equivocators(self):
        """Equivocating voters should be excluded from quorum count."""
        peers = ["a0", "a1", "a2", "a3"]
        task = Task(id="t1", description="work")

        proposer = QuorumConsensus(AgentId("a0"), peers)
        rnd = await proposer.propose(task)

        # 2 genuine voters + 1 equivocator
        for aid in ["a1", "a2"]:
            voter = QuorumConsensus(AgentId(aid), peers)
            await voter.participate(rnd)

        equivocator = QuorumConsensus(AgentId("a3"), peers)
        await equivocator.participate(rnd)
        await equivocator.participate(rnd)  # equivocation!

        outcome = await proposer.resolve(rnd)
        # 2 genuine votes < threshold(4)=3, so no quorum
        assert outcome.metadata["quorum_reached"] is False
        assert outcome.metadata["equivocations"] == ["a3"]

    @pytest.mark.asyncio
    async def test_commit_is_noop(self):
        """commit() should complete without error."""
        coord = QuorumConsensus(AgentId("a0"), ["a0", "a1"])
        task = Task(id="t1", description="work")
        rnd = await coord.propose(task)
        outcome = await coord.resolve(rnd)
        await coord.commit(outcome)  # Should not raise


# ──────────────────────────────────────────────────────────
# BFT Validator Tests
# ──────────────────────────────────────────────────────────


class TestBftValidators:
    """Test the four BFT adversarial validators."""

    def _make_send_event(self, agent: str, target: str, msg: str) -> dict[str, Any]:
        """Helper to create a trace send event."""
        return {"kind": "send", "agent": agent, "target": target, "msg": msg}

    def test_no_conflicting_commits_passes(self):
        """No conflicts — same value committed in each round."""
        events: list[dict[str, Any]] = [
            self._make_send_event("leader", "f0", "result:1:committed:3/4:42"),
            self._make_send_event("leader", "f1", "result:1:committed:3/4:42"),
            self._make_send_event("leader", "f2", "result:2:committed:3/4:99"),
        ]
        report = check_no_conflicting_commits(events)
        assert report.passed

    def test_no_conflicting_commits_fails(self):
        """Conflict — different values committed in the same round."""
        events: list[dict[str, Any]] = [
            self._make_send_event("leader", "f0", "result:1:committed:3/4:42"),
            self._make_send_event("leader", "f1", "result:1:committed:3/4:99"),
        ]
        report = check_no_conflicting_commits(events)
        assert not report.passed
        assert "conflicting" in report.detail

    def test_no_equivocation_passes(self):
        """Leader proposes the same value to all followers."""
        events: list[dict[str, Any]] = [
            self._make_send_event("leader", "f0", "propose:1:42"),
            self._make_send_event("leader", "f1", "propose:1:42"),
            self._make_send_event("leader", "f2", "propose:1:42"),
        ]
        report = check_no_equivocation(events)
        assert report.passed

    def test_no_equivocation_fails(self):
        """Leader proposes different values to different followers."""
        events: list[dict[str, Any]] = [
            self._make_send_event("leader", "f0", "propose:1:42"),
            self._make_send_event("leader", "f1", "propose:1:99"),
        ]
        report = check_no_equivocation(events)
        assert not report.passed
        assert "equivocation" in report.detail

    def test_no_forged_quorum_passes(self):
        """Committed round backed by enough distinct votes (n=4, f=1, threshold=3)."""
        events: list[dict[str, Any]] = [
            self._make_send_event("f0", "leader", "vote:1:accept"),
            self._make_send_event("f1", "leader", "vote:1:accept"),
            self._make_send_event("f2", "leader", "vote:1:accept"),
            self._make_send_event("leader", "f0", "result:1:committed:3/3:42"),
        ]
        report = check_no_forged_quorum(events, total_agents=4)
        assert report.passed

    def test_no_forged_quorum_fails(self):
        """Committed round with only 1 vote (n=4, threshold=3) — forged."""
        events: list[dict[str, Any]] = [
            self._make_send_event("f0", "leader", "vote:1:accept"),
            self._make_send_event("leader", "f0", "result:1:committed:1/1:42"),
        ]
        report = check_no_forged_quorum(events, total_agents=4)
        assert not report.passed
        assert "forged" in report.detail or "insufficient" in report.detail

    def test_no_stuck_view_passes(self):
        """Commits happen regularly within the threshold."""
        events: list[dict[str, Any]] = [
            self._make_send_event("leader", "f0", "propose:1:42"),
            self._make_send_event("leader", "f0", "result:1:committed:3/4:42"),
            self._make_send_event("leader", "f0", "propose:2:99"),
            self._make_send_event("leader", "f0", "result:2:committed:3/4:99"),
        ]
        report = check_no_stuck_view(events, max_rounds_without_commit=5)
        assert report.passed

    def test_no_stuck_view_fails_no_commits(self):
        """Many rounds proposed but no commits — stuck."""
        events: list[dict[str, Any]] = [
            self._make_send_event("leader", "f0", f"propose:{i}:42") for i in range(1, 20)
        ]
        report = check_no_stuck_view(events, max_rounds_without_commit=5)
        assert not report.passed

    def test_no_stuck_view_passes_few_rounds(self):
        """Few rounds proposed, no commits — below threshold."""
        events: list[dict[str, Any]] = [
            self._make_send_event("leader", "f0", "propose:1:42"),
            self._make_send_event("leader", "f0", "propose:2:42"),
        ]
        report = check_no_stuck_view(events, max_rounds_without_commit=5)
        assert report.passed


# ──────────────────────────────────────────────────────────
# Scenario Factory Tests
# ──────────────────────────────────────────────────────────


class TestScenarioFactory:
    """Test the quorum_consensus_factory function."""

    def test_factory_creates_agents(self):
        """Factory should create replica agents."""
        from nest_core.scenario import ScenarioConfig
        from nest_core.scenarios_builtin.quorum_consensus import quorum_consensus_factory

        config = ScenarioConfig.from_yaml("scenarios/quorum_baseline.yaml")
        agents = quorum_consensus_factory(config, {})

        assert AgentId("replica-0") in agents
        assert AgentId("replica-1") in agents
        assert len(agents) == 20

    def test_factory_creates_byzantine_agents(self):
        """Factory with byzantine_agents should create MaliciousQuorumReplica."""
        from nest_core.scenario import ScenarioConfig
        from nest_core.scenarios_builtin.quorum_consensus import (
            MaliciousQuorumReplica,
            quorum_consensus_factory,
        )

        config = ScenarioConfig.from_yaml("scenarios/quorum_byzantine.yaml")

        # Override to ensure malicious_agents is set as expected by the new factory
        config.task.config["malicious_agents"] = ["replica-0", "replica-1"]
        agents = quorum_consensus_factory(config, {})

        byzantine_agents = [a for a in agents.values() if isinstance(a, MaliciousQuorumReplica)]
        assert len(byzantine_agents) >= 1
