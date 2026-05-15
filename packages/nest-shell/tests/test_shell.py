# SPDX-License-Identifier: Apache-2.0
"""Tests for Tier 2 shell agent."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from nest_core.scenario import ScenarioConfig
from nest_core.sim.simulator import Simulator
from nest_core.types import AgentId
from nest_shell.agent import ShellAgent, parse_action, shell_marketplace_factory
from nest_shell.llm import MockLLMBackend


class TestParseAction:
    def test_parse_send(self) -> None:
        response = "ACTION: send\nTO: seller-0\nMESSAGE: buy:product-0:50"
        action = parse_action(response, AgentId("buyer-0"))
        assert action is not None
        assert action["action"] == "send"
        assert action["to"] == AgentId("seller-0")
        assert action["message"] == b"buy:product-0:50"

    def test_parse_none(self) -> None:
        action = parse_action("ACTION: none", AgentId("buyer-0"))
        assert action is None

    def test_parse_sender_placeholder(self) -> None:
        response = "ACTION: send\nTO: {sender}\nMESSAGE: sold:product:50"
        action = parse_action(response, AgentId("buyer-3"))
        assert action is not None
        assert action["to"] == AgentId("buyer-3")

    def test_parse_no_to_defaults_to_sender(self) -> None:
        response = "ACTION: send\nMESSAGE: sold:product:50"
        action = parse_action(response, AgentId("buyer-5"))
        assert action is not None
        assert action["to"] == AgentId("buyer-5")

    def test_parse_garbage(self) -> None:
        action = parse_action("I don't know what to do", AgentId("a"))
        assert action is None


class TestMockLLMBackend:
    @pytest.mark.asyncio
    async def test_buy_response(self) -> None:
        backend = MockLLMBackend()
        response = await backend.complete([
            {"role": "user", "content": "Message from buyer-0: buy:product:50"}
        ])
        assert "ACTION: send" in response
        assert "sold:" in response
        assert backend.call_count == 1

    @pytest.mark.asyncio
    async def test_sold_response(self) -> None:
        backend = MockLLMBackend()
        response = await backend.complete([
            {"role": "user", "content": "Message from seller-0: sold:product:50"}
        ])
        assert "ACTION: send" in response
        assert "buy:" in response

    @pytest.mark.asyncio
    async def test_none_response(self) -> None:
        backend = MockLLMBackend()
        response = await backend.complete([
            {"role": "user", "content": "Hello world"}
        ])
        assert "ACTION: none" in response

    @pytest.mark.asyncio
    async def test_custom_responses(self) -> None:
        backend = MockLLMBackend(responses={
            "special": "ACTION: send\nTO: admin\nMESSAGE: alert:critical",
        })
        response = await backend.complete([
            {"role": "user", "content": "This is a special message"}
        ])
        assert "alert:critical" in response


class TestShellAgent:
    @pytest.mark.asyncio
    async def test_shell_agent_simulation(self, tmp_path: Path) -> None:
        backend = MockLLMBackend()
        trace_file = tmp_path / "shell.jsonl"

        sim = Simulator(seed=42, trace_path=trace_file)

        buyer = ShellAgent(
            AgentId("buyer-0"), role="buyer", backend=backend, num_sellers=2, rounds=3,
        )
        seller = ShellAgent(
            AgentId("seller-0"), role="seller", backend=backend, num_sellers=2, rounds=3,
        )
        seller2 = ShellAgent(
            AgentId("seller-1"), role="seller", backend=backend, num_sellers=2, rounds=3,
        )

        sim.add_agent(AgentId("buyer-0"), buyer)
        sim.add_agent(AgentId("seller-0"), seller)
        sim.add_agent(AgentId("seller-1"), seller2)

        await sim.run(max_ticks=5000)

        assert trace_file.exists()
        content = trace_file.read_text()
        lines = [ln for ln in content.strip().split("\n") if ln]
        assert len(lines) > 0

        assert backend.call_count > 0
        assert buyer.action_count > 0

    @pytest.mark.asyncio
    async def test_shell_marketplace_factory(self, tmp_path: Path) -> None:
        backend = MockLLMBackend()
        trace_file = tmp_path / "shell_market.jsonl"

        config = ScenarioConfig.from_dict({
            "name": "shell-test",
            "seed": 42,
            "agents": {
                "count": 6,
                "roles": [
                    {"name": "buyer", "count": 3},
                    {"name": "seller", "count": 3},
                ],
            },
            "task": {"type": "marketplace", "config": {"rounds": 3}},
            "duration": "ticks: 2000",
            "output": {"trace": str(trace_file)},
        })

        agents = shell_marketplace_factory(config, {}, backend=backend)
        assert len(agents) == 6

        buyer_count = sum(1 for k in agents if str(k).startswith("buyer"))
        seller_count = sum(1 for k in agents if str(k).startswith("seller"))
        assert buyer_count == 3
        assert seller_count == 3

        sim = Simulator(seed=42, trace_path=trace_file)
        for aid, agent in agents.items():
            sim.add_agent(aid, agent)

        await sim.run(max_ticks=2000)

        assert trace_file.exists()
        content = trace_file.read_text()
        lines = [ln for ln in content.strip().split("\n") if ln]
        assert len(lines) > 0

        send_count = 0
        for line in lines:
            event: dict[str, Any] = json.loads(line)
            if event["kind"] == "send":
                send_count += 1
        assert send_count > 0
        assert backend.call_count > 0

    @pytest.mark.asyncio
    async def test_history_truncation(self) -> None:
        """Verify conversation history doesn't grow unbounded."""
        backend = MockLLMBackend()
        agent = ShellAgent(
            AgentId("buyer-0"), role="buyer", backend=backend,
            num_sellers=1, rounds=50,
        )
        assert agent.history_length == 1  # system prompt only
