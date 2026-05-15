# SPDX-License-Identifier: Apache-2.0
"""Marketplace scenario — buyers and sellers exchanging goods.

Buyers discover sellers via the registry, negotiate prices, and pay.
Sellers list products, respond to negotiations, and fulfill orders.

Example::

    agents = marketplace_factory(config, plugins)
"""

from __future__ import annotations

from typing import Any

from nest_core.scenario import ScenarioConfig
from nest_core.sim.agent import AgentContext, StateMachineAgent
from nest_core.types import AgentId


class BuyerAgent(StateMachineAgent):
    """A buyer that discovers sellers and attempts to purchase.

    Example::

        agent = BuyerAgent(AgentId("buyer-0"), catalog_size=10)
    """

    def __init__(self, agent_id: AgentId, num_sellers: int, rounds: int = 10) -> None:
        self._id = agent_id
        self._num_sellers = num_sellers
        self._rounds = rounds
        self._purchases = 0
        self._round = 0

    async def on_start(self, ctx: AgentContext) -> None:
        """Send buy request to a random seller.

        Example::

            await agent.on_start(ctx)
        """
        seller_idx = ctx.rng.randint(0, self._num_sellers - 1)
        seller = AgentId(f"seller-{seller_idx}")
        await ctx.send(seller, b"buy:product-0:50")

    async def on_message(self, ctx: AgentContext, sender: AgentId, payload: bytes) -> None:
        """Handle seller responses.

        Example::

            await agent.on_message(ctx, sender, b"sold:product-0:50")
        """
        msg = payload.decode("utf-8", errors="replace")

        if msg.startswith("sold:"):
            self._purchases += 1
            self._round += 1
            if self._round < self._rounds:
                seller_idx = ctx.rng.randint(0, self._num_sellers - 1)
                seller = AgentId(f"seller-{seller_idx}")
                price = ctx.rng.randint(10, 100)
                await ctx.send(seller, f"buy:product-{self._round}:{price}".encode())

        elif msg.startswith("reject:"):
            self._round += 1
            if self._round < self._rounds:
                seller_idx = ctx.rng.randint(0, self._num_sellers - 1)
                seller = AgentId(f"seller-{seller_idx}")
                price = ctx.rng.randint(10, 100)
                await ctx.send(seller, f"buy:product-{self._round}:{price}".encode())


class SellerAgent(StateMachineAgent):
    """A seller that responds to buy requests.

    Example::

        agent = SellerAgent(AgentId("seller-0"), min_price=20)
    """

    def __init__(self, agent_id: AgentId, min_price: int = 20) -> None:
        self._id = agent_id
        self._min_price = min_price
        self._sales = 0

    async def on_message(self, ctx: AgentContext, sender: AgentId, payload: bytes) -> None:
        """Handle buy requests — accept if price >= min_price.

        Example::

            await agent.on_message(ctx, sender, b"buy:product-0:50")
        """
        msg = payload.decode("utf-8", errors="replace")

        if msg.startswith("buy:"):
            parts = msg.split(":")
            if len(parts) >= 3:
                product = parts[1]
                try:
                    price = int(parts[2])
                except ValueError:
                    price = 0

                if price >= self._min_price:
                    self._sales += 1
                    await ctx.send(sender, f"sold:{product}:{price}".encode())
                else:
                    await ctx.send(sender, f"reject:{product}:{self._min_price}".encode())


def marketplace_factory(
    config: ScenarioConfig,
    plugins: dict[str, Any],
) -> dict[AgentId, StateMachineAgent]:
    """Create buyer and seller agents for the marketplace scenario.

    Example::

        agents = marketplace_factory(config, plugins)
    """
    task_config = config.task.config
    rounds = task_config.get("rounds", 10)

    agents: dict[AgentId, StateMachineAgent] = {}

    if config.agents.roles:
        buyer_count = 0
        seller_count = 0
        for role in config.agents.roles:
            if role.name == "buyer":
                buyer_count = role.count
            elif role.name == "seller":
                seller_count = role.count
    else:
        buyer_count = config.agents.count // 2
        seller_count = config.agents.count - buyer_count

    for i in range(seller_count):
        aid = AgentId(f"seller-{i}")
        min_price = 10 + (i * 5) % 50
        agents[aid] = SellerAgent(aid, min_price=min_price)

    for i in range(buyer_count):
        aid = AgentId(f"buyer-{i}")
        agents[aid] = BuyerAgent(aid, num_sellers=seller_count, rounds=rounds)

    return agents
