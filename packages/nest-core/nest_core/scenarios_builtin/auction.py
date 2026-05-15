# SPDX-License-Identifier: Apache-2.0
"""Auction scenario — bidders compete for items from an auctioneer.

The auctioneer announces items, bidders submit bids, and the
highest bidder wins each round.

Example::

    agents = auction_factory(config, plugins)
"""

from __future__ import annotations

from typing import Any

from nest_core.scenario import ScenarioConfig
from nest_core.sim.agent import AgentContext, StateMachineAgent
from nest_core.types import AgentId


class AuctioneerAgent(StateMachineAgent):
    """Announces items and selects the highest bidder each round."""

    def __init__(self, agent_id: AgentId, num_bidders: int, rounds: int = 5) -> None:
        self._id = agent_id
        self._num_bidders = num_bidders
        self._rounds = rounds
        self._round = 0
        self._bids: dict[str, int] = {}
        self._sales = 0

    async def on_start(self, ctx: AgentContext) -> None:
        self._round = 1
        for i in range(self._num_bidders):
            bidder = AgentId(f"bidder-{i}")
            await ctx.send(bidder, f"auction:item-{self._round}:100".encode())

    async def on_message(self, ctx: AgentContext, sender: AgentId, payload: bytes) -> None:
        msg = payload.decode("utf-8", errors="replace")

        if msg.startswith("bid:"):
            parts = msg.split(":")
            if len(parts) >= 3:
                try:
                    amount = int(parts[2])
                except ValueError:
                    amount = 0
                self._bids[str(sender)] = amount

                if len(self._bids) >= self._num_bidders:
                    winner = max(self._bids, key=lambda k: self._bids[k])
                    winning_bid = self._bids[winner]
                    self._sales += 1

                    for i in range(self._num_bidders):
                        bidder = AgentId(f"bidder-{i}")
                        if str(bidder) == winner:
                            await ctx.send(bidder, f"won:item-{self._round}:{winning_bid}".encode())
                        else:
                            msg = f"lost:item-{self._round}:{winning_bid}"
                            await ctx.send(bidder, msg.encode())

                    self._bids.clear()
                    self._round += 1

                    if self._round <= self._rounds:
                        for i in range(self._num_bidders):
                            bidder = AgentId(f"bidder-{i}")
                            base_price = 50 + self._round * 10
                            msg = f"auction:item-{self._round}:{base_price}"
                            await ctx.send(bidder, msg.encode())


class BidderAgent(StateMachineAgent):
    """Submits bids based on item value and a random markup."""

    def __init__(self, agent_id: AgentId, max_budget: int = 200) -> None:
        self._id = agent_id
        self._max_budget = max_budget
        self._wins = 0
        self._spent = 0

    async def on_message(self, ctx: AgentContext, sender: AgentId, payload: bytes) -> None:
        msg = payload.decode("utf-8", errors="replace")

        if msg.startswith("auction:"):
            parts = msg.split(":")
            if len(parts) >= 3:
                item = parts[1]
                try:
                    base_price = int(parts[2])
                except ValueError:
                    base_price = 50

                markup = ctx.rng.randint(0, 50)
                bid = min(base_price + markup, self._max_budget - self._spent)
                if bid > 0:
                    await ctx.send(sender, f"bid:{item}:{bid}".encode())
                else:
                    await ctx.send(sender, f"bid:{item}:0".encode())

        elif msg.startswith("won:"):
            parts = msg.split(":")
            if len(parts) >= 3:
                try:
                    price = int(parts[2])
                except ValueError:
                    price = 0
                self._wins += 1
                self._spent += price


def auction_factory(
    config: ScenarioConfig,
    plugins: dict[str, Any],
) -> dict[AgentId, StateMachineAgent]:
    """Create auctioneer and bidder agents.

    Example::

        agents = auction_factory(config, plugins)
    """
    task_config = config.task.config
    rounds = task_config.get("rounds", 5)

    agents: dict[AgentId, StateMachineAgent] = {}

    if config.agents.roles:
        bidder_count = 0
        for role in config.agents.roles:
            if role.name == "bidder":
                bidder_count = role.count
        if bidder_count == 0:
            bidder_count = config.agents.count - 1
    else:
        bidder_count = config.agents.count - 1

    auctioneer_id = AgentId("auctioneer-0")
    agents[auctioneer_id] = AuctioneerAgent(auctioneer_id, num_bidders=bidder_count, rounds=rounds)

    for i in range(bidder_count):
        aid = AgentId(f"bidder-{i}")
        max_budget = 100 + (i * 20) % 200
        agents[aid] = BidderAgent(aid, max_budget=max_budget)

    return agents
