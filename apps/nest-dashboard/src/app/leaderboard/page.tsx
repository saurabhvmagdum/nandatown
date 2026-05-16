'use client';

import { useState, useMemo } from 'react';
import { leaderboardData, scenarioColors } from '@/lib/demo-data';

type SortField = 'rank' | 'deliveryRate' | 'dealRate' | 'latency' | 'agents';
type SortDirection = 'asc' | 'desc';

const scenarios = [
  'All',
  'Marketplace',
  'Auction',
  'Voting',
  'Consensus',
  'Supply Chain',
  'Reputation',
] as const;

const scenarioKeyMap: Record<string, string> = {
  Marketplace: 'marketplace',
  Auction: 'auction',
  Voting: 'voting',
  Consensus: 'consensus',
  'Supply Chain': 'supply_chain',
  Reputation: 'reputation',
};

const scenarioLabel: Record<string, string> = {
  marketplace: 'Marketplace',
  auction: 'Auction',
  voting: 'Voting',
  consensus: 'Consensus',
  supply_chain: 'Supply Chain',
  reputation: 'Reputation',
};

function medalEmoji(rank: number): string {
  if (rank === 1) return '\u{1F947}';
  if (rank === 2) return '\u{1F948}';
  if (rank === 3) return '\u{1F949}';
  return '';
}

export default function LeaderboardPage() {
  const [activeFilter, setActiveFilter] = useState<string>('All');
  const [sortField, setSortField] = useState<SortField>('rank');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection(field === 'rank' ? 'asc' : 'desc');
    }
  };

  const filteredAndSorted = useMemo(() => {
    let data = [...leaderboardData];

    if (activeFilter !== 'All') {
      const key = scenarioKeyMap[activeFilter];
      data = data.filter((entry) => entry.scenario === key);
    }

    data.sort((a, b) => {
      let aVal: number;
      let bVal: number;

      switch (sortField) {
        case 'rank':
          aVal = a.rank;
          bVal = b.rank;
          break;
        case 'deliveryRate':
          aVal = a.deliveryRate;
          bVal = b.deliveryRate;
          break;
        case 'dealRate':
          aVal = a.dealRate ?? -1;
          bVal = b.dealRate ?? -1;
          break;
        case 'latency':
          aVal = a.latency;
          bVal = b.latency;
          break;
        case 'agents':
          aVal = a.agents;
          bVal = b.agents;
          break;
        default:
          aVal = a.rank;
          bVal = b.rank;
      }

      return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
    });

    return data;
  }, [activeFilter, sortField, sortDirection]);

  const sortIndicator = (field: SortField) => {
    if (sortField !== field) return null;
    return (
      <span className="ml-1 text-crimson">
        {sortDirection === 'asc' ? '↑' : '↓'}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-warm-50">
      {/* Header */}
      <section className="border-b border-warm-200 bg-white">
        <div className="mx-auto max-w-7xl px-6 py-16">
          <h1 className="text-4xl font-bold tracking-tight text-warm-900 animate-fade-in">
            Leaderboard
          </h1>
          <p className="mt-4 max-w-3xl text-lg leading-relaxed text-warm-500 animate-fade-in stagger-1">
            Benchmark rankings across all scenarios. Individual metrics are
            shown side-by-side &mdash; no composite weighting.
          </p>
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-6 py-10">
        {/* Filters */}
        <div className="animate-fade-in stagger-2">
          <div className="flex flex-wrap gap-2">
            {scenarios.map((scenario) => {
              const isActive = activeFilter === scenario;
              return (
                <button
                  key={scenario}
                  onClick={() => setActiveFilter(scenario)}
                  className={`rounded-full px-4 py-2 text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-warm-900 text-white shadow-sm'
                      : 'bg-white text-warm-600 border border-warm-200 hover:border-warm-300 hover:text-warm-900'
                  }`}
                >
                  {scenario}
                </button>
              );
            })}
          </div>
        </div>

        {/* Sort Controls */}
        <div className="mt-6 flex flex-wrap items-center gap-2 animate-fade-in stagger-3">
          <span className="text-sm font-medium text-warm-500 mr-1">
            Sort by:
          </span>
          {(
            [
              ['rank', 'Rank'],
              ['deliveryRate', 'Delivery Rate'],
              ['dealRate', 'Deal Rate'],
              ['latency', 'Latency'],
              ['agents', 'Agents'],
            ] as [SortField, string][]
          ).map(([field, label]) => {
            const isActive = sortField === field;
            return (
              <button
                key={field}
                onClick={() => handleSort(field)}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-crimson/10 text-crimson border border-crimson/20'
                    : 'text-warm-500 hover:text-warm-700 border border-transparent'
                }`}
              >
                {label}
                {sortIndicator(field)}
              </button>
            );
          })}
        </div>

        {/* Table */}
        <div className="mt-8 animate-fade-in stagger-4">
          <div className="overflow-x-auto rounded-xl border border-warm-200 bg-white shadow-sm">
            <table className="w-full min-w-[800px] text-left">
              <thead>
                <tr className="border-b border-warm-200 bg-warm-50/80">
                  <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wider text-warm-500">
                    Rank
                  </th>
                  <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wider text-warm-500">
                    Name
                  </th>
                  <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wider text-warm-500">
                    Scenario
                  </th>
                  <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wider text-warm-500">
                    Agents
                  </th>
                  <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wider text-warm-500">
                    Delivery Rate
                  </th>
                  <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wider text-warm-500">
                    Deal Rate
                  </th>
                  <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wider text-warm-500">
                    Latency (ticks)
                  </th>
                  <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wider text-warm-500">
                    Throughput (msg/tick)
                  </th>
                  <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wider text-warm-500">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-warm-100">
                {filteredAndSorted.map((entry) => {
                  const medal = medalEmoji(entry.rank);
                  const badgeColor = scenarioColors[entry.scenario] || '#78716C';
                  const barWidth = Math.min(entry.deliveryRate, 100);

                  return (
                    <tr
                      key={`${entry.rank}-${entry.name}`}
                      className="transition-colors hover:bg-warm-50/60"
                    >
                      {/* Rank */}
                      <td className="px-5 py-4 whitespace-nowrap">
                        <span className="text-sm font-semibold text-warm-900">
                          {medal ? `${medal} ` : ''}
                          {entry.rank}
                        </span>
                      </td>

                      {/* Name */}
                      <td className="px-5 py-4">
                        <span className="text-sm font-medium text-warm-900">
                          {entry.name}
                        </span>
                      </td>

                      {/* Scenario Badge */}
                      <td className="px-5 py-4 whitespace-nowrap">
                        <span
                          className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium text-white"
                          style={{ backgroundColor: badgeColor }}
                        >
                          {scenarioLabel[entry.scenario] || entry.scenario}
                        </span>
                      </td>

                      {/* Agents */}
                      <td className="px-5 py-4 whitespace-nowrap">
                        <span className="text-sm text-warm-700">
                          {entry.agents}
                        </span>
                      </td>

                      {/* Delivery Rate */}
                      <td className="px-5 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-warm-900">
                            {entry.deliveryRate}%
                          </span>
                          <div className="h-1.5 w-16 rounded-full bg-warm-200">
                            <div
                              className="h-1.5 rounded-full bg-crimson"
                              style={{ width: `${barWidth}%` }}
                            />
                          </div>
                        </div>
                      </td>

                      {/* Deal Rate */}
                      <td className="px-5 py-4 whitespace-nowrap">
                        <span className="text-sm text-warm-700">
                          {entry.dealRate !== null
                            ? `${entry.dealRate}%`
                            : '—'}
                        </span>
                      </td>

                      {/* Latency */}
                      <td className="px-5 py-4 whitespace-nowrap">
                        <span className="text-sm text-warm-700">
                          {entry.latency} ticks
                        </span>
                      </td>

                      {/* Throughput */}
                      <td className="px-5 py-4 whitespace-nowrap">
                        <span className="text-sm text-warm-700">
                          {entry.throughput} msg/tick
                        </span>
                      </td>

                      {/* Date */}
                      <td className="px-5 py-4 whitespace-nowrap">
                        <span className="text-sm text-warm-400">
                          {entry.date}
                        </span>
                      </td>
                    </tr>
                  );
                })}

                {filteredAndSorted.length === 0 && (
                  <tr>
                    <td
                      colSpan={9}
                      className="px-5 py-16 text-center text-sm text-warm-400"
                    >
                      No entries match the selected filter.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Reproducibility Note */}
        <div className="mt-10 animate-fade-in stagger-5">
          <div className="rounded-xl border border-warm-200 bg-white p-8 shadow-sm">
            <h2 className="text-lg font-semibold text-warm-900">
              About These Rankings
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-warm-600">
              Rankings are based on Tier 1 reference simulations. Results are
              deterministic and reproducible with the same seed. Tier 1 uses
              virtual tick-based time with no transport failures, so delivery
              rates are expected to be near 100%.
            </p>

            <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {[
                {
                  label: 'Delivery Rate',
                  desc: 'Fraction of sent messages that were received. Not a measure of protocol success.',
                },
                {
                  label: 'Deal Rate',
                  desc: 'Percentage of buy requests that resulted in a successful trade. Marketplace/auction only.',
                },
                {
                  label: 'Latency',
                  desc: 'Mean ticks between send and receive for correlated message pairs.',
                },
                {
                  label: 'Throughput',
                  desc: 'Messages processed per tick across all agents.',
                },
              ].map((metric) => (
                <div
                  key={metric.label}
                  className="rounded-lg border border-warm-200 bg-warm-50/50 p-4"
                >
                  <span className="text-sm font-semibold text-warm-900">
                    {metric.label}
                  </span>
                  <p className="mt-1 text-xs text-warm-500">{metric.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
