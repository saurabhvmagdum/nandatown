export interface LeaderboardEntry {
  rank: number;
  name: string;
  scenario: string;
  agents: number;
  successRate: number;
  latency: number;
  throughput: number;
  reliability: number;
  composite: number;
  grade: string;
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
    successRate: number;
    meanLatency: number;
    messageCount: number;
    throughput: number;
  };
  traceEvents?: number;
  duration?: string;
}

export interface AgentMessage {
  tick: number;
  from: string;
  to: string;
  content: string;
  kind: string;
}

function grade(score: number): string {
  if (score >= 90) return "A";
  if (score >= 80) return "B";
  if (score >= 70) return "C";
  if (score >= 60) return "D";
  return "F";
}

export const leaderboardData: LeaderboardEntry[] = [
  {
    rank: 1,
    name: "Marketplace v3 (optimized)",
    scenario: "marketplace",
    agents: 100,
    successRate: 94.2,
    latency: 12.3,
    throughput: 847,
    reliability: 99.1,
    composite: 92.4,
    grade: grade(92.4),
    date: "2026-05-14",
  },
  {
    rank: 2,
    name: "Auction with dynamic pricing",
    scenario: "auction",
    agents: 50,
    successRate: 91.8,
    latency: 8.7,
    throughput: 623,
    reliability: 98.5,
    composite: 89.7,
    grade: grade(89.7),
    date: "2026-05-13",
  },
  {
    rank: 3,
    name: "Quorum Consensus (7 nodes)",
    scenario: "consensus",
    agents: 7,
    successRate: 100,
    latency: 3.2,
    throughput: 312,
    reliability: 100,
    composite: 88.1,
    grade: grade(88.1),
    date: "2026-05-12",
  },
  {
    rank: 4,
    name: "Supply chain (4-hop)",
    scenario: "supply_chain",
    agents: 4,
    successRate: 87.5,
    latency: 24.1,
    throughput: 156,
    reliability: 95.0,
    composite: 82.3,
    grade: grade(82.3),
    date: "2026-05-11",
  },
  {
    rank: 5,
    name: "Voting with 20 voters",
    scenario: "voting",
    agents: 22,
    successRate: 95.5,
    latency: 5.4,
    throughput: 445,
    reliability: 97.2,
    composite: 81.9,
    grade: grade(81.9),
    date: "2026-05-10",
  },
  {
    rank: 6,
    name: "Reputation (20% malicious)",
    scenario: "reputation",
    agents: 10,
    successRate: 80.0,
    latency: 15.6,
    throughput: 234,
    reliability: 92.0,
    composite: 76.4,
    grade: grade(76.4),
    date: "2026-05-09",
  },
  {
    rank: 7,
    name: "Marketplace baseline",
    scenario: "marketplace",
    agents: 20,
    successRate: 78.3,
    latency: 18.9,
    throughput: 198,
    reliability: 88.5,
    composite: 71.2,
    grade: grade(71.2),
    date: "2026-05-08",
  },
  {
    rank: 8,
    name: "Consensus under partition",
    scenario: "consensus",
    agents: 5,
    successRate: 60.0,
    latency: 45.2,
    throughput: 89,
    reliability: 72.0,
    composite: 58.3,
    grade: grade(58.3),
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
      successRate: 94.2,
      meanLatency: 12.3,
      messageCount: 2200,
      throughput: 847,
    },
    traceEvents: 2200,
    duration: "1.8s",
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
      successRate: 91.8,
      meanLatency: 8.7,
      messageCount: 1850,
      throughput: 623,
    },
    traceEvents: 1850,
    duration: "1.4s",
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
      successRate: 95.5,
      meanLatency: 5.4,
      messageCount: 980,
      throughput: 445,
    },
    traceEvents: 980,
    duration: "0.9s",
  },
  {
    id: "consensus-7",
    name: "BFT Consensus: 7 Nodes",
    description:
      "A leader proposes values and followers vote to commit or abort. Commits when quorum agrees. Tests leader-based agreement with configurable thresholds.",
    scenario: "consensus",
    agents: 7,
    tier: 1,
    status: "completed",
    metrics: {
      successRate: 100,
      meanLatency: 3.2,
      messageCount: 420,
      throughput: 312,
    },
    traceEvents: 420,
    duration: "0.5s",
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
      successRate: 87.5,
      meanLatency: 24.1,
      messageCount: 340,
      throughput: 156,
    },
    traceEvents: 340,
    duration: "0.6s",
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
      successRate: 80.0,
      meanLatency: 15.6,
      messageCount: 560,
      throughput: 234,
    },
    traceEvents: 560,
    duration: "0.7s",
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
