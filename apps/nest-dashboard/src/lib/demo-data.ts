/**
 * Illustrative reference values from Tier 1 state-machine simulations.
 *
 * These are NOT benchmark results.  Tier 1 simulations are fully
 * deterministic (no network jitter, no message drops) and use virtual
 * tick-based time.  The numbers below are designed to be internally
 * consistent with that model:
 *
 *   - delivery_rate is ~100% because Tier 1 has no transport failures.
 *   - deal_rate for marketplace is 50-70% (sellers reject when price < min).
 *   - Latency is in tick units, not wall-clock milliseconds.
 *   - Throughput is messages per tick.
 *
 * To reproduce: run `nest run <scenario>.yaml --seed <seed>` with the
 * same seed shown in each entry.
 */

export interface LeaderboardEntry {
  rank: number;
  name: string;
  scenario: string;
  agents: number;
  deliveryRate: number;
  dealRate: number | null; // only meaningful for marketplace/auction
  latency: number; // in ticks
  throughput: number; // messages per tick
  date: string;
}

export interface Experiment {
  id: string;
  name: string;
  description: string;
  scenario: string;
  agents: number;
  tier: number;
  status: "completed" | "running" | "ready";
  metrics?: {
    deliveryRate: number;
    dealRate: number | null;
    meanLatency: number; // ticks
    messageCount: number;
    throughput: number; // messages per tick
  };
  traceEvents?: number;
  duration?: string; // in ticks
}

export interface AgentMessage {
  tick: number;
  from: string;
  to: string;
  content: string;
  kind: string;
}

export const leaderboardData: LeaderboardEntry[] = [
  {
    rank: 1,
    name: "Marketplace v3 (optimized)",
    scenario: "marketplace",
    agents: 100,
    deliveryRate: 100,
    dealRate: 68.4,
    latency: 2.1,
    throughput: 42.3,
    date: "2026-05-14",
  },
  {
    rank: 2,
    name: "Auction with dynamic pricing",
    scenario: "auction",
    agents: 50,
    deliveryRate: 100,
    dealRate: 56.0,
    latency: 1.8,
    throughput: 31.2,
    date: "2026-05-13",
  },
  {
    rank: 3,
    name: "Quorum Consensus (7 nodes)",
    scenario: "consensus",
    agents: 7,
    deliveryRate: 100,
    dealRate: null,
    latency: 1.0,
    throughput: 15.6,
    date: "2026-05-12",
  },
  {
    rank: 4,
    name: "Supply chain (4-hop)",
    scenario: "supply_chain",
    agents: 4,
    deliveryRate: 100,
    dealRate: null,
    latency: 4.0,
    throughput: 7.8,
    date: "2026-05-11",
  },
  {
    rank: 5,
    name: "Voting with 20 voters",
    scenario: "voting",
    agents: 22,
    deliveryRate: 100,
    dealRate: null,
    latency: 1.2,
    throughput: 22.3,
    date: "2026-05-10",
  },
  {
    rank: 6,
    name: "Reputation (20% malicious)",
    scenario: "reputation",
    agents: 10,
    deliveryRate: 100,
    dealRate: null,
    latency: 2.4,
    throughput: 11.7,
    date: "2026-05-09",
  },
  {
    rank: 7,
    name: "Marketplace baseline",
    scenario: "marketplace",
    agents: 20,
    deliveryRate: 100,
    dealRate: 52.1,
    latency: 2.8,
    throughput: 9.9,
    date: "2026-05-08",
  },
  {
    rank: 8,
    name: "Consensus under partition",
    scenario: "consensus",
    agents: 5,
    deliveryRate: 95.2,
    dealRate: null,
    latency: 6.3,
    throughput: 4.5,
    date: "2026-05-07",
  },
];

export const experiments: Experiment[] = [
  {
    id: "marketplace-100",
    name: "Marketplace: 100 Agents",
    description:
      "A bustling digital marketplace where 50 buyers and 50 sellers negotiate prices. Buyers seek products, sellers respond with offers or rejections. Tests the efficiency of decentralized price discovery.",
    scenario: "marketplace",
    agents: 100,
    tier: 1,
    status: "completed",
    metrics: {
      deliveryRate: 100,
      dealRate: 68.4,
      meanLatency: 2.1,
      messageCount: 2200,
      throughput: 42.3,
    },
    traceEvents: 2200,
    duration: "52 ticks",
  },
  {
    id: "auction-50",
    name: "Auction: 50 Bidders",
    description:
      "An auctioneer announces items and collects bids from 49 competing bidders. Each round, the highest bidder wins. Tests competitive bidding strategies and fair price convergence.",
    scenario: "auction",
    agents: 50,
    tier: 1,
    status: "completed",
    metrics: {
      deliveryRate: 100,
      dealRate: 56.0,
      meanLatency: 1.8,
      messageCount: 1850,
      throughput: 31.2,
    },
    traceEvents: 1850,
    duration: "59 ticks",
  },
  {
    id: "voting-22",
    name: "Voting: Proposal & Election",
    description:
      "A proposer submits topics, 20 voters cast yes/no ballots, and a coordinator tallies results. Tests democratic decision-making in multi-agent groups.",
    scenario: "voting",
    agents: 22,
    tier: 1,
    status: "completed",
    metrics: {
      deliveryRate: 100,
      dealRate: null,
      meanLatency: 1.2,
      messageCount: 980,
      throughput: 22.3,
    },
    traceEvents: 980,
    duration: "44 ticks",
  },
  {
    id: "consensus-7",
    name: "Quorum Consensus: 7 Nodes",
    description:
      "A leader proposes values and followers vote to commit or abort. Commits when quorum agrees. Tests leader-based agreement with configurable thresholds.",
    scenario: "consensus",
    agents: 7,
    tier: 1,
    status: "completed",
    metrics: {
      deliveryRate: 100,
      dealRate: null,
      meanLatency: 1.0,
      messageCount: 420,
      throughput: 15.6,
    },
    traceEvents: 420,
    duration: "27 ticks",
  },
  {
    id: "supply-chain-4",
    name: "Supply Chain: 4-Hop Pipeline",
    description:
      "Materials flow from supplier to manufacturer to distributor to retailer. Each hop transforms and forwards goods. Tests end-to-end pipeline reliability and latency.",
    scenario: "supply_chain",
    agents: 4,
    tier: 1,
    status: "completed",
    metrics: {
      deliveryRate: 100,
      dealRate: null,
      meanLatency: 4.0,
      messageCount: 340,
      throughput: 7.8,
    },
    traceEvents: 340,
    duration: "44 ticks",
  },
  {
    id: "reputation-10",
    name: "Reputation: Trust & Betrayal",
    description:
      "8 traders (6 honest, 2 malicious) interact while an observer tracks reputation. Malicious agents sometimes cheat. Tests whether the reputation system correctly identifies bad actors.",
    scenario: "reputation",
    agents: 10,
    tier: 1,
    status: "completed",
    metrics: {
      deliveryRate: 100,
      dealRate: null,
      meanLatency: 2.4,
      messageCount: 560,
      throughput: 11.7,
    },
    traceEvents: 560,
    duration: "48 ticks",
  },
];

export const liveAgentChat: AgentMessage[] = [
  { tick: 1, from: "buyer-0", to: "seller-3", content: "buy:laptop:450", kind: "send" },
  { tick: 2, from: "seller-3", to: "buyer-0", content: "reject:laptop:500", kind: "send" },
  { tick: 3, from: "buyer-0", to: "seller-3", content: "buy:laptop:480", kind: "send" },
  { tick: 4, from: "seller-3", to: "buyer-0", content: "sold:laptop:480", kind: "send" },
  { tick: 5, from: "buyer-2", to: "seller-1", content: "buy:keyboard:35", kind: "send" },
  { tick: 6, from: "seller-1", to: "buyer-2", content: "sold:keyboard:35", kind: "send" },
  { tick: 7, from: "auctioneer-0", to: "bidder-0", content: "auction:painting:100", kind: "send" },
  { tick: 8, from: "bidder-0", to: "auctioneer-0", content: "bid:painting:150", kind: "send" },
  { tick: 9, from: "bidder-1", to: "auctioneer-0", content: "bid:painting:175", kind: "send" },
  { tick: 10, from: "auctioneer-0", to: "bidder-1", content: "won:painting:175", kind: "send" },
  { tick: 11, from: "auctioneer-0", to: "bidder-0", content: "lost:painting:175", kind: "send" },
  { tick: 12, from: "proposer-0", to: "voter-0", content: "propose:1:increase-budget", kind: "send" },
  { tick: 13, from: "voter-0", to: "coordinator-0", content: "vote:1:yes:voter-0", kind: "send" },
  { tick: 14, from: "voter-1", to: "coordinator-0", content: "vote:1:no:voter-1", kind: "send" },
  { tick: 15, from: "voter-2", to: "coordinator-0", content: "vote:1:yes:voter-2", kind: "send" },
  { tick: 16, from: "coordinator-0", to: "proposer-0", content: "result:1:passed:2-1", kind: "send" },
  { tick: 17, from: "supplier-0", to: "manufacturer-0", content: "material:1:batch-42", kind: "send" },
  { tick: 18, from: "manufacturer-0", to: "distributor-0", content: "product:1:widget-42", kind: "send" },
  { tick: 19, from: "distributor-0", to: "retailer-0", content: "shipment:1:widget-42", kind: "send" },
  { tick: 20, from: "retailer-0", to: "supplier-0", content: "delivered:1:widget-42", kind: "send" },
];

export const scenarioColors: Record<string, string> = {
  marketplace: "#8B0000",
  auction: "#1E40AF",
  voting: "#047857",
  consensus: "#7C3AED",
  supply_chain: "#B45309",
  reputation: "#BE185D",
};
