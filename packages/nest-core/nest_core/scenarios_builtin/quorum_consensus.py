# SPDX-License-Identifier: Apache-2.0
"""BFT Quorum scenario logic.

This scenario runs evidence-carrying, rotating-leader BFT.
All the network logic, equivocation detection, and signature verification
is offloaded to the QuorumBFT coordination plugin.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from nest_core.scenario import ScenarioConfig
from nest_core.sim.agent import AgentContext, StateMachineAgent
from nest_core.types import AgentId


class QuorumReplica(StateMachineAgent):
    """Honest Quorum BFT replica."""

    def __init__(self, agent_id: AgentId, peer_ids: Sequence[AgentId], timeout_ticks: int = 40) -> None:
        self.agent_id = agent_id
        self._peer_ids_str = [str(p) for p in sorted(peer_ids)]
        self.peer_ids = peer_ids
        self.timeout_ticks = timeout_ticks
        
        self.height = 1
        self.round = 1
        self.highest_qc = "none"
        
        # (height, round) -> set of round-change voters
        self.round_change_votes: dict[tuple[int, int], set[str]] = {}
        self.partition_config: dict[str, Any] = {}

    def _is_partitioned(self, target: str, current_time: float) -> bool:
        start = self.partition_config.get("start", 0)
        end = self.partition_config.get("end", 0)
        if start <= current_time <= end:
            group1 = self.partition_config.get("group1", [])
            group2 = self.partition_config.get("group2", [])
            my_group = 1 if str(self.agent_id) in group1 else (2 if str(self.agent_id) in group2 else 0)
            target_group = 1 if target in group1 else (2 if target in group2 else 0)
            if my_group != 0 and target_group != 0 and my_group != target_group:
                return True
        return False

    async def _send_if_connected(self, ctx: AgentContext, target: AgentId, payload: bytes) -> None:
        if self._is_partitioned(str(target), ctx.time):
            return
        await ctx.send(target, payload)

    async def on_start(self, ctx: AgentContext) -> None:
        """Schedule initial timeout and potentially propose."""
        await ctx.schedule(self.timeout_ticks, f"timeout:{self.height}:{self.round}".encode())
        coord = ctx.plugins["coordination"]
        
        if hasattr(coord, "get_leader_for_round"):
            if coord.get_leader_for_round(self.height, self.round, self._peer_ids_str) == str(self.agent_id):
                await ctx.schedule(5.0, b"propose")

    async def _propose(self, ctx: AgentContext) -> None:
        """Create and broadcast a proposal."""
        coord = ctx.plugins["coordination"]
        identity = ctx.plugins["identity"]
        
        digest = str(ctx.rng.randint(1, 1000))
        msg_fields = {"height": str(self.height), "round": str(self.round), "digest": digest, "leader": str(self.agent_id)}
        signed_msg = coord.sign_message("propose", msg_fields, identity)
        await ctx.send(self.agent_id, signed_msg)
        for peer in self.peer_ids:
            await self._send_if_connected(ctx, peer, signed_msg)

    async def on_message(self, ctx: AgentContext, sender: AgentId, payload: bytes) -> None:
        """Dispatch incoming messages and timeouts."""
        coord = ctx.plugins.get("coordination")
        identity = ctx.plugins.get("identity")
        
        text = payload.decode(errors="replace")
        if text.startswith("timeout:"):
            try:
                _, h_str, r_str = text.split(":")
                if int(h_str) == self.height and int(r_str) == self.round:
                    await self._handle_timeout(ctx)
            except ValueError:
                pass
            return
        
        if payload == b"propose":
            await self._propose(ctx)
            return

        parsed = coord.parse_and_verify(payload, identity)
        if not parsed:
            return
            
        kind = parsed.get("kind")
        h = int(parsed.get("height", 0))
        r = int(parsed.get("round", 0))
        
        # Drop stale messages
        if h < self.height or (h == self.height and r < self.round):
            return
            
        if kind == "propose":
            await self._handle_propose(ctx, parsed)
        elif kind == "vote":
            await self._handle_vote(ctx, parsed)
        elif kind == "round_change":
            await self._handle_round_change(ctx, parsed)
        elif kind == "commit":
            await self._handle_commit(ctx, parsed)

    async def _handle_timeout(self, ctx: AgentContext) -> None:
        """Handle a round timeout by broadcasting a round_change."""
        coord = ctx.plugins["coordination"]
        identity = ctx.plugins["identity"]
        
        await ctx.send(self.agent_id, f"timeout:height={self.height}|round={self.round}|agent={self.agent_id}".encode())
        self.round += 1
        
        msg_fields = {"height": str(self.height), "round": str(self.round), "agent": str(self.agent_id), "highest_qc": self.highest_qc}
        signed_msg = coord.sign_message("round_change", msg_fields, identity)
        
        for peer in self.peer_ids:
            await self._send_if_connected(ctx, peer, signed_msg)
            
        await ctx.schedule(self.timeout_ticks, f"timeout:{self.height}:{self.round}".encode())

    async def _handle_round_change(self, ctx: AgentContext, parsed: dict[str, str]) -> None:
        h = int(parsed["height"])
        r = int(parsed["round"])
        agent = parsed["agent"]
        
        key = (h, r)
        if key not in self.round_change_votes:
            self.round_change_votes[key] = set()
            
        self.round_change_votes[key].add(agent)
        
        from nest_plugins_reference.coordination.quorum import Quorum
        threshold = Quorum.threshold(len(self.peer_ids))
        
        if not hasattr(self, "_entered_views"):
            self._entered_views = set()
            
        if len(self.round_change_votes[key]) >= threshold:
            if (h, r) not in self._entered_views:
                self._entered_views.add((h, r))
                if h > self.height or (h == self.height and r >= self.round):
                    self.height = h
                    self.round = r
                    await ctx.send(self.agent_id, f"view_change:height={h}|round={r}".encode())
                    
                    coord = ctx.plugins["coordination"]
                    if coord.get_leader_for_round(h, r, self._peer_ids_str) == str(self.agent_id):
                        await ctx.schedule(5.0, b"propose")

    async def _handle_propose(self, ctx: AgentContext, parsed: dict[str, str]) -> None:
        h = int(parsed["height"])
        r = int(parsed["round"])
        digest = parsed["digest"]
        leader = parsed["leader"]
        
        coord = ctx.plugins["coordination"]
        identity = ctx.plugins["identity"]
        
        if leader != coord.get_leader_for_round(h, r, self._peer_ids_str):
            return
            
        msg_fields = {"height": str(h), "round": str(r), "phase": "prepare", "digest": digest, "agent": str(self.agent_id)}
        signed_msg = coord.sign_message("vote", msg_fields, identity)
        await self._send_if_connected(ctx, AgentId(leader), signed_msg)

    async def _handle_vote(self, ctx: AgentContext, parsed: dict[str, str]) -> None:
        h = int(parsed["height"])
        r = int(parsed["round"])
        digest = parsed["digest"]
        agent = parsed["agent"]
        raw_vote = parsed["_raw_payload"]
        
        coord = ctx.plugins["coordination"]
        identity = ctx.plugins["identity"]
        
        is_valid, equiv_msg = coord.process_vote(h, r, agent, digest, raw_vote)
        if equiv_msg:
            await self._send_if_connected(ctx, self.agent_id, equiv_msg.encode("ascii"))
        if not is_valid:
            return
            
        signers = coord.check_quorum(h, r, digest, len(self.peer_ids))
        if signers:
            cert = coord.generate_certificate(h, r, digest, signers)
            
            commit_fields = {"height": str(h), "round": str(r), "digest": digest, "qc": cert, "signers": ",".join(sorted(signers)), "agent": str(self.agent_id)}
            if coord.excluded_voters.get((h, r)):
                commit_fields["excluded"] = ",".join(sorted(coord.excluded_voters[(h, r)]))
                
            commit_msg = coord.sign_message("commit", commit_fields, identity)
            
            for peer in self.peer_ids:
                await self._send_if_connected(ctx, peer, commit_msg)

    async def _handle_commit(self, ctx: AgentContext, parsed: dict[str, str]) -> None:
        h = int(parsed["height"])
        r = int(parsed["round"])
        digest = parsed["digest"]
        
        if h >= self.height:
            self.highest_qc = parsed.get("qc", "")
            self.height = h + 1
            self.round = 1
            
            await ctx.send(self.agent_id, f"commit:height={h}|round={r}|digest={digest}|qc={self.highest_qc}|signers={parsed.get('signers','')}|excluded={parsed.get('excluded','')}".encode())
            
            await ctx.schedule(self.timeout_ticks, f"timeout:{self.height}:{self.round}".encode())
            
            coord = ctx.plugins["coordination"]
            if coord.get_leader_for_round(self.height, self.round, self._peer_ids_str) == str(self.agent_id):
                await ctx.schedule(5.0, b"propose")


class MaliciousQuorumReplica(QuorumReplica):
    """A replica that equivocates when acting as a leader or follower."""

    async def _propose(self, ctx: AgentContext) -> None:
        coord = ctx.plugins["coordination"]
        identity = ctx.plugins["identity"]
        
        half = len(self.peer_ids) // 2
        group_a = self.peer_ids[:half] or list(self.peer_ids)
        group_b = self.peer_ids[half:] or list(self.peer_ids)
        
        digest_a = str(ctx.rng.randint(1, 1000))
        digest_b = str(ctx.rng.randint(1001, 2000))
        
        msg_a_fields = {"height": str(self.height), "round": str(self.round), "digest": digest_a, "leader": str(self.agent_id)}
        msg_b_fields = {"height": str(self.height), "round": str(self.round), "digest": digest_b, "leader": str(self.agent_id)}
        
        msg_a = coord.sign_message("propose", msg_a_fields, identity)
        msg_b = coord.sign_message("propose", msg_b_fields, identity)
        
        for peer in group_a:
            await self._send_if_connected(ctx, peer, msg_a)
        for peer in group_b:
            await self._send_if_connected(ctx, peer, msg_b)
            
    async def _handle_propose(self, ctx: AgentContext, parsed: dict[str, str]) -> None:
        h = int(parsed["height"])
        r = int(parsed["round"])
        digest = parsed["digest"]
        leader = parsed["leader"]
        
        coord = ctx.plugins["coordination"]
        identity = ctx.plugins["identity"]
        
        if leader != coord.get_leader_for_round(h, r, self._peer_ids_str):
            return
            
        msg_fields1 = {"height": str(h), "round": str(r), "phase": "prepare", "digest": digest, "agent": str(self.agent_id)}
        msg_fields2 = {"height": str(h), "round": str(r), "phase": "prepare", "digest": digest + "_fake", "agent": str(self.agent_id)}
        
        msg1 = coord.sign_message("vote", msg_fields1, identity)
        msg2 = coord.sign_message("vote", msg_fields2, identity)
        
        await self._send_if_connected(ctx, AgentId(leader), msg1)
        await self._send_if_connected(ctx, AgentId(leader), msg2)


def instantiate_plugins(plugins: dict[str, Any], all_ids: Sequence[AgentId]) -> None:
    """Wire per-agent signed Identity and QuorumBFT Coordination plugins."""
    identity_cls = plugins.get("identity")
    coord_cls = plugins.get("coordination")
    
    if not (identity_cls and coord_cls):
        return
        
    agent_plugins = plugins.setdefault("_agent_plugins", {})
    identities = {aid: identity_cls(aid, seed=b"sim-seed") for aid in all_ids}
    
    for aid, ident in identities.items():
        for peer_id, peer_ident in identities.items():
            if peer_id != aid:
                ident.register_peer(peer_id, peer_ident.public_key)
                
    all_str_ids = [str(aid) for aid in all_ids]
    
    for aid in all_ids:
        # Give each agent its own Identity and Coordination plugins
        agent_plugins.setdefault(aid, {})["identity"] = identities[aid]
        try:
            agent_plugins[aid]["coordination"] = coord_cls(aid, peer_ids=all_str_ids)
        except TypeError:
            agent_plugins[aid]["coordination"] = coord_cls(aid)
        
    plugins.pop("identity", None)
    plugins.pop("coordination", None)


def quorum_consensus_factory(
    config: ScenarioConfig,
    plugins: dict[str, Any],
) -> dict[AgentId, StateMachineAgent]:
    """Create BFT Quorum agents."""
    task_config = config.task.config
    count = config.agents.count
    view_timeout_ticks = int(task_config.get("view_timeout_ticks", 40))
    malicious_names: set[str] = set(task_config.get("malicious_agents", []))
    partition_config = task_config.get("partition", {})

    replica_ids = [AgentId(f"replica-{i}") for i in range(count)]
    instantiate_plugins(plugins, replica_ids)

    agents: dict[AgentId, StateMachineAgent] = {}
    for rid in replica_ids:
        if str(rid) in malicious_names:
            agent = MaliciousQuorumReplica(rid, replica_ids, timeout_ticks=view_timeout_ticks)
        else:
            agent = QuorumReplica(rid, replica_ids, timeout_ticks=view_timeout_ticks)
        agent.partition_config = partition_config
        agents[rid] = agent
            
    return agents
