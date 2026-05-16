'use client';

import Link from 'next/link';
import { useState, useMemo, useCallback, useRef } from 'react';

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface TraceEvent {
  tick: number;
  kind: 'start' | 'stop' | 'send' | 'recv' | 'bid' | 'ask' | 'ack';
  agent: string;
  from?: string;
  to?: string;
  payload?: string;
  role?: string;
}

interface AgentInfo {
  id: string;
  role: string;
  sent: number;
  received: number;
  firstTick: number;
  lastTick: number;
}

type SortKey = keyof AgentInfo;
type SortDir = 'asc' | 'desc';
type Tab = 'map' | 'timeline' | 'stats';

/* ------------------------------------------------------------------ */
/*  Demo data generator                                                */
/* ------------------------------------------------------------------ */

const ROLES: Record<string, string> = {
  buyer: '#8B0000',     // crimson
  seller: '#1C1917',    // warm-900 (black)
  auctioneer: '#1E40AF', // blue-800
  observer: '#78716C',  // warm-500
  broker: '#92400E',    // amber-800
};

function generateDemoTrace(): TraceEvent[] {
  const agents: { id: string; role: string }[] = [
    { id: 'buyer-0', role: 'buyer' },
    { id: 'buyer-1', role: 'buyer' },
    { id: 'buyer-2', role: 'buyer' },
    { id: 'seller-0', role: 'seller' },
    { id: 'seller-1', role: 'seller' },
    { id: 'auctioneer-0', role: 'auctioneer' },
    { id: 'broker-0', role: 'broker' },
    { id: 'observer-0', role: 'observer' },
  ];

  const events: TraceEvent[] = [];

  // Tick 0 — everyone starts
  for (const a of agents) {
    events.push({ tick: 0, kind: 'start', agent: a.id, role: a.role });
  }

  // Seed a deterministic PRNG so demo always looks the same
  let seed = 42;
  const rand = () => {
    seed = (seed * 16807 + 0) % 2147483647;
    return (seed - 1) / 2147483646;
  };

  const products = ['laptop', 'phone', 'tablet', 'monitor', 'keyboard'];

  for (let tick = 1; tick <= 18; tick++) {
    // Buyers send bids to auctioneer
    for (let b = 0; b < 3; b++) {
      if (rand() > 0.35) {
        const product = products[Math.floor(rand() * products.length)];
        const price = Math.floor(rand() * 200 + 20);
        events.push({
          tick,
          kind: 'bid',
          agent: `buyer-${b}`,
          from: `buyer-${b}`,
          to: 'auctioneer-0',
          payload: `bid:${product}:${price}`,
        });
      }
    }

    // Sellers send asks to auctioneer
    for (let s = 0; s < 2; s++) {
      if (rand() > 0.4) {
        const product = products[Math.floor(rand() * products.length)];
        const price = Math.floor(rand() * 180 + 30);
        events.push({
          tick,
          kind: 'ask',
          agent: `seller-${s}`,
          from: `seller-${s}`,
          to: 'auctioneer-0',
          payload: `ask:${product}:${price}`,
        });
      }
    }

    // Auctioneer matches and sends ack back
    if (rand() > 0.5) {
      const buyerIdx = Math.floor(rand() * 3);
      const sellerIdx = Math.floor(rand() * 2);
      events.push({
        tick,
        kind: 'ack',
        agent: 'auctioneer-0',
        from: 'auctioneer-0',
        to: `buyer-${buyerIdx}`,
        payload: 'match:confirmed',
      });
      events.push({
        tick,
        kind: 'ack',
        agent: 'auctioneer-0',
        from: 'auctioneer-0',
        to: `seller-${sellerIdx}`,
        payload: 'match:confirmed',
      });
    }

    // Broker relays messages occasionally
    if (rand() > 0.6) {
      const from = `buyer-${Math.floor(rand() * 3)}`;
      const to = `seller-${Math.floor(rand() * 2)}`;
      events.push({
        tick,
        kind: 'send',
        agent: 'broker-0',
        from: 'broker-0',
        to,
        payload: `relay:${from}`,
      });
    }

    // Observer sends periodic pings
    if (tick % 4 === 0) {
      events.push({
        tick,
        kind: 'send',
        agent: 'observer-0',
        from: 'observer-0',
        to: 'auctioneer-0',
        payload: 'heartbeat',
      });
    }
  }

  // Final tick — everyone stops
  for (const a of agents) {
    events.push({ tick: 20, kind: 'stop', agent: a.id, role: a.role });
  }

  return events;
}

/* ------------------------------------------------------------------ */
/*  Derived data helpers                                               */
/* ------------------------------------------------------------------ */

function deriveAgents(events: TraceEvent[]): AgentInfo[] {
  const map = new Map<string, AgentInfo>();

  const ensure = (id: string, role?: string) => {
    if (!map.has(id)) {
      map.set(id, {
        id,
        role: role ?? id.replace(/-\d+$/, ''),
        sent: 0,
        received: 0,
        firstTick: Infinity,
        lastTick: -Infinity,
      });
    }
    return map.get(id)!;
  };

  for (const e of events) {
    const a = ensure(e.agent, e.role);
    a.firstTick = Math.min(a.firstTick, e.tick);
    a.lastTick = Math.max(a.lastTick, e.tick);

    if (e.from) {
      const sender = ensure(e.from);
      sender.sent++;
      sender.firstTick = Math.min(sender.firstTick, e.tick);
      sender.lastTick = Math.max(sender.lastTick, e.tick);
    }
    if (e.to) {
      const receiver = ensure(e.to);
      receiver.received++;
      receiver.firstTick = Math.min(receiver.firstTick, e.tick);
      receiver.lastTick = Math.max(receiver.lastTick, e.tick);
    }
  }

  return Array.from(map.values());
}

interface EdgeInfo {
  source: string;
  target: string;
  count: number;
}

function deriveEdges(events: TraceEvent[]): EdgeInfo[] {
  const map = new Map<string, number>();
  for (const e of events) {
    if (e.from && e.to) {
      const key = [e.from, e.to].sort().join('::');
      map.set(key, (map.get(key) ?? 0) + 1);
    }
  }
  return Array.from(map.entries()).map(([key, count]) => {
    const [source, target] = key.split('::');
    return { source, target, count };
  });
}

function roleColor(role: string): string {
  return ROLES[role] ?? '#78716C';
}

/* ------------------------------------------------------------------ */
/*  Communication Map (SVG)                                            */
/* ------------------------------------------------------------------ */

function CommunicationMap({ events }: { events: TraceEvent[] }) {
  const [hovered, setHovered] = useState<string | null>(null);
  const agents = useMemo(() => deriveAgents(events), [events]);
  const edges = useMemo(() => deriveEdges(events), [events]);

  const maxEdgeCount = useMemo(
    () => Math.max(...edges.map((e) => e.count), 1),
    [edges],
  );

  // Ring layout
  const cx = 300;
  const cy = 300;
  const radius = 220;
  const positions = useMemo(() => {
    const pos = new Map<string, { x: number; y: number }>();
    agents.forEach((a, i) => {
      const angle = (2 * Math.PI * i) / agents.length - Math.PI / 2;
      pos.set(a.id, {
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
      });
    });
    return pos;
  }, [agents]);

  const connectedTo = useMemo(() => {
    if (!hovered) return new Set<string>();
    const set = new Set<string>();
    for (const e of edges) {
      if (e.source === hovered) set.add(e.target);
      if (e.target === hovered) set.add(e.source);
    }
    return set;
  }, [hovered, edges]);

  const uniqueRoles = useMemo(() => {
    const set = new Set<string>();
    agents.forEach((a) => set.add(a.role));
    return Array.from(set);
  }, [agents]);

  return (
    <div className="space-y-4">
      <svg
        viewBox="0 0 600 600"
        className="w-full max-w-[700px] mx-auto"
        style={{ overflow: 'visible' }}
      >
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="shadow">
            <feDropShadow dx="0" dy="1" stdDeviation="2" floodOpacity="0.15" />
          </filter>
        </defs>

        {/* Edges */}
        {edges.map((edge) => {
          const p1 = positions.get(edge.source);
          const p2 = positions.get(edge.target);
          if (!p1 || !p2) return null;

          const isHighlighted =
            !hovered ||
            edge.source === hovered ||
            edge.target === hovered;
          const thickness = 1 + (edge.count / maxEdgeCount) * 6;

          return (
            <line
              key={`${edge.source}-${edge.target}`}
              x1={p1.x}
              y1={p1.y}
              x2={p2.x}
              y2={p2.y}
              stroke={isHighlighted ? '#8B0000' : '#E7E5E4'}
              strokeWidth={isHighlighted ? thickness : thickness * 0.5}
              strokeOpacity={isHighlighted ? 0.6 : 0.15}
              strokeLinecap="round"
              style={{
                transition: 'all 0.35s cubic-bezier(0.4, 0, 0.2, 1)',
              }}
            />
          );
        })}

        {/* Edge count labels (only when hovered) */}
        {hovered &&
          edges
            .filter((e) => e.source === hovered || e.target === hovered)
            .map((edge) => {
              const p1 = positions.get(edge.source);
              const p2 = positions.get(edge.target);
              if (!p1 || !p2) return null;
              const mx = (p1.x + p2.x) / 2;
              const my = (p1.y + p2.y) / 2;
              return (
                <g key={`label-${edge.source}-${edge.target}`}>
                  <circle cx={mx} cy={my} r={12} fill="white" filter="url(#shadow)" />
                  <text
                    x={mx}
                    y={my}
                    textAnchor="middle"
                    dominantBaseline="central"
                    fontSize={10}
                    fontWeight={600}
                    fill="#1C1917"
                  >
                    {edge.count}
                  </text>
                </g>
              );
            })}

        {/* Nodes */}
        {agents.map((agent) => {
          const pos = positions.get(agent.id);
          if (!pos) return null;

          const isActive =
            !hovered || hovered === agent.id || connectedTo.has(agent.id);
          const nodeRadius = hovered === agent.id ? 24 : 18;
          const color = roleColor(agent.role);

          return (
            <g
              key={agent.id}
              onMouseEnter={() => setHovered(agent.id)}
              onMouseLeave={() => setHovered(null)}
              style={{
                cursor: 'pointer',
                transition: 'opacity 0.35s ease',
                opacity: isActive ? 1 : 0.2,
              }}
            >
              {/* Pulse ring on hover */}
              {hovered === agent.id && (
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r={nodeRadius + 6}
                  fill="none"
                  stroke={color}
                  strokeWidth={2}
                  strokeOpacity={0.3}
                  className="animate-pulse-dot"
                />
              )}
              <circle
                cx={pos.x}
                cy={pos.y}
                r={nodeRadius}
                fill={color}
                filter={hovered === agent.id ? 'url(#glow)' : undefined}
                style={{
                  transition: 'r 0.35s cubic-bezier(0.4, 0, 0.2, 1)',
                }}
              />
              <text
                x={pos.x}
                y={pos.y}
                textAnchor="middle"
                dominantBaseline="central"
                fontSize={9}
                fontWeight={700}
                fill="white"
                style={{ pointerEvents: 'none' }}
              >
                {agent.id.split('-')[0][0].toUpperCase()}
                {agent.id.split('-')[1]}
              </text>
              {/* External label */}
              <text
                x={pos.x}
                y={pos.y + nodeRadius + 16}
                textAnchor="middle"
                fontSize={11}
                fontWeight={500}
                fill="#44403C"
                style={{
                  transition: 'opacity 0.35s ease',
                  opacity: isActive ? 1 : 0.3,
                  pointerEvents: 'none',
                }}
              >
                {agent.id}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Legend */}
      <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
        {uniqueRoles.map((role) => (
          <div key={role} className="flex items-center gap-2">
            <span
              className="inline-block h-3 w-3 rounded-full"
              style={{ backgroundColor: roleColor(role) }}
            />
            <span className="text-sm text-warm-600 capitalize">{role}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Timeline                                                           */
/* ------------------------------------------------------------------ */

const KIND_COLORS: Record<string, string> = {
  start: '#16A34A',
  stop: '#78716C',
  send: '#8B0000',
  recv: '#D97706',
  bid: '#8B0000',
  ask: '#1E40AF',
  ack: '#059669',
};

function Timeline({ events }: { events: TraceEvent[] }) {
  const maxTick = useMemo(
    () => Math.max(...events.map((e) => e.tick), 1),
    [events],
  );

  const [selectedTick, setSelectedTick] = useState<number | null>(null);

  const filteredEvents = useMemo(
    () =>
      selectedTick !== null
        ? events.filter((e) => e.tick === selectedTick)
        : events,
    [events, selectedTick],
  );

  // Build tick marks
  const ticks = useMemo(() => {
    const set = new Set(events.map((e) => e.tick));
    return Array.from(set).sort((a, b) => a - b);
  }, [events]);

  // Group events by tick for stacking dots
  const tickGroups = useMemo(() => {
    const map = new Map<number, TraceEvent[]>();
    for (const e of events) {
      if (!map.has(e.tick)) map.set(e.tick, []);
      map.get(e.tick)!.push(e);
    }
    return map;
  }, [events]);

  const svgWidth = 900;
  const svgHeight = 160;
  const paddingX = 60;
  const baseY = 90;

  const xScale = useCallback(
    (tick: number) => paddingX + ((svgWidth - paddingX * 2) * tick) / maxTick,
    [maxTick],
  );

  return (
    <div className="space-y-6">
      <div className="overflow-x-auto rounded-xl border border-warm-200 bg-white p-4">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="w-full min-w-[600px]"
          style={{ overflow: 'visible' }}
        >
          {/* Axis line */}
          <line
            x1={paddingX}
            y1={baseY}
            x2={svgWidth - paddingX}
            y2={baseY}
            stroke="#D6D3D1"
            strokeWidth={1.5}
          />

          {/* Tick marks and labels */}
          {ticks.map((t) => (
            <g key={`tick-${t}`}>
              <line
                x1={xScale(t)}
                y1={baseY - 4}
                x2={xScale(t)}
                y2={baseY + 4}
                stroke="#A8A29E"
                strokeWidth={1}
              />
              <text
                x={xScale(t)}
                y={baseY + 20}
                textAnchor="middle"
                fontSize={10}
                fill="#78716C"
              >
                {t}
              </text>
            </g>
          ))}

          {/* Axis label */}
          <text
            x={svgWidth / 2}
            y={baseY + 40}
            textAnchor="middle"
            fontSize={12}
            fill="#A8A29E"
            fontWeight={500}
          >
            Tick
          </text>

          {/* Event dots */}
          {ticks.map((t) => {
            const group = tickGroups.get(t) ?? [];
            return group.map((ev, i) => {
              const color = KIND_COLORS[ev.kind] ?? '#78716C';
              const yOffset = -(i * 10 + 12);
              const isSelected = selectedTick === null || selectedTick === t;
              return (
                <circle
                  key={`dot-${t}-${i}`}
                  cx={xScale(t)}
                  cy={baseY + yOffset}
                  r={isSelected ? 5 : 3}
                  fill={color}
                  fillOpacity={isSelected ? 0.9 : 0.2}
                  stroke={isSelected ? color : 'none'}
                  strokeWidth={1.5}
                  strokeOpacity={0.3}
                  style={{
                    cursor: 'pointer',
                    transition: 'all 0.25s ease',
                  }}
                  onClick={() =>
                    setSelectedTick(selectedTick === t ? null : t)
                  }
                />
              );
            });
          })}
        </svg>
      </div>

      {/* Kind legend */}
      <div className="flex flex-wrap items-center gap-4">
        {Object.entries(KIND_COLORS).map(([kind, color]) => (
          <div key={kind} className="flex items-center gap-1.5">
            <span
              className="inline-block h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: color }}
            />
            <span className="text-xs text-warm-500 capitalize">{kind}</span>
          </div>
        ))}
      </div>

      {/* Event log */}
      <div className="rounded-xl border border-warm-200 bg-white">
        <div className="flex items-center justify-between border-b border-warm-100 px-5 py-3">
          <h3 className="text-sm font-semibold text-warm-900">
            Event Log
            {selectedTick !== null && (
              <span className="ml-2 text-warm-400 font-normal">
                — tick {selectedTick}
              </span>
            )}
          </h3>
          {selectedTick !== null && (
            <button
              onClick={() => setSelectedTick(null)}
              className="text-xs text-crimson hover:text-crimson-light transition-colors"
            >
              Show all
            </button>
          )}
        </div>
        <div className="max-h-72 overflow-y-auto divide-y divide-warm-100">
          {filteredEvents.map((ev, i) => (
            <div
              key={i}
              className="flex items-center gap-4 px-5 py-2.5 hover:bg-warm-50 transition-colors"
            >
              <span className="w-10 shrink-0 text-right font-mono text-xs text-warm-400">
                {ev.tick}
              </span>
              <span
                className="inline-flex h-5 items-center rounded px-1.5 text-[10px] font-semibold uppercase tracking-wider text-white"
                style={{
                  backgroundColor: KIND_COLORS[ev.kind] ?? '#78716C',
                }}
              >
                {ev.kind}
              </span>
              <span className="text-sm text-warm-700 font-medium">
                {ev.agent}
              </span>
              {ev.from && ev.to && (
                <span className="text-xs text-warm-400">
                  {ev.from} &rarr; {ev.to}
                </span>
              )}
              {ev.payload && (
                <span className="ml-auto truncate text-xs font-mono text-warm-400 max-w-[220px]">
                  {ev.payload}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Agent Stats                                                        */
/* ------------------------------------------------------------------ */

function AgentStats({ events }: { events: TraceEvent[] }) {
  const agents = useMemo(() => deriveAgents(events), [events]);
  const [sortKey, setSortKey] = useState<SortKey>('id');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  const sorted = useMemo(() => {
    const copy = [...agents];
    copy.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (typeof av === 'number' && typeof bv === 'number') {
        return sortDir === 'asc' ? av - bv : bv - av;
      }
      return sortDir === 'asc'
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av));
    });
    return copy;
  }, [agents, sortKey, sortDir]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const columns: { key: SortKey; label: string }[] = [
    { key: 'id', label: 'Agent' },
    { key: 'role', label: 'Role' },
    { key: 'sent', label: 'Sent' },
    { key: 'received', label: 'Received' },
    { key: 'firstTick', label: 'First Active' },
    { key: 'lastTick', label: 'Last Active' },
  ];

  return (
    <div className="rounded-xl border border-warm-200 bg-white overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-warm-100">
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={() => toggleSort(col.key)}
                  className="cursor-pointer select-none px-5 py-3 text-xs font-semibold uppercase tracking-wider text-warm-500 hover:text-warm-900 transition-colors"
                >
                  <span className="inline-flex items-center gap-1">
                    {col.label}
                    {sortKey === col.key && (
                      <span className="text-crimson">
                        {sortDir === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-warm-100">
            {sorted.map((agent) => (
              <tr
                key={agent.id}
                className="hover:bg-warm-50 transition-colors"
              >
                <td className="px-5 py-3 text-sm font-medium text-warm-900">
                  <span className="flex items-center gap-2">
                    <span
                      className="inline-block h-2.5 w-2.5 rounded-full"
                      style={{ backgroundColor: roleColor(agent.role) }}
                    />
                    {agent.id}
                  </span>
                </td>
                <td className="px-5 py-3 text-sm text-warm-600 capitalize">
                  {agent.role}
                </td>
                <td className="px-5 py-3 text-sm font-mono text-warm-700">
                  {agent.sent}
                </td>
                <td className="px-5 py-3 text-sm font-mono text-warm-700">
                  {agent.received}
                </td>
                <td className="px-5 py-3 text-sm font-mono text-warm-500">
                  {agent.firstTick === Infinity ? '—' : agent.firstTick}
                </td>
                <td className="px-5 py-3 text-sm font-mono text-warm-500">
                  {agent.lastTick === -Infinity ? '—' : agent.lastTick}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  File Upload                                                        */
/* ------------------------------------------------------------------ */

function parseTraceFile(text: string): TraceEvent[] {
  const lines = text.trim().split('\n');
  const events: TraceEvent[] = [];
  for (const line of lines) {
    try {
      const parsed = JSON.parse(line);
      if (parsed && typeof parsed.tick === 'number' && parsed.kind) {
        events.push(parsed as TraceEvent);
      }
    } catch {
      // skip malformed lines
    }
  }
  return events;
}

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export default function VisualizerPage() {
  const [events, setEvents] = useState<TraceEvent[] | null>(null);
  const [tab, setTab] = useState<Tab>('map');
  const [dragOver, setDragOver] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((file: File) => {
    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      const parsed = parseTraceFile(text);
      if (parsed.length > 0) {
        setEvents(parsed);
        setTab('map');
      }
    };
    reader.readAsText(file);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const loadDemo = useCallback(() => {
    setEvents(generateDemoTrace());
    setFileName(null);
    setTab('map');
  }, []);

  const tabs: { id: Tab; label: string }[] = [
    { id: 'map', label: 'Communication Map' },
    { id: 'timeline', label: 'Timeline' },
    { id: 'stats', label: 'Agent Stats' },
  ];

  return (
    <div className="mx-auto max-w-7xl px-6 py-16">
      {/* Header */}
      <div className="animate-fade-in">
        <h1 className="text-4xl font-bold tracking-tight text-warm-900">
          Visualizer
        </h1>
        <p className="mt-2 text-lg text-warm-500">
          Upload a trace file or explore the built-in demo.
        </p>
      </div>

      {/* Upload / Demo */}
      <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:items-stretch animate-fade-in stagger-1">
        {/* Load Demo */}
        <button
          onClick={loadDemo}
          className="flex items-center justify-center gap-3 rounded-xl border-2 border-warm-200 bg-white px-8 py-6 text-sm font-semibold text-warm-900 shadow-sm transition-all hover:border-crimson hover:shadow-md active:scale-[0.98]"
        >
          <svg
            className="h-5 w-5 text-crimson"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={2}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z"
            />
          </svg>
          Load Demo
        </button>

        {/* Drop zone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`flex flex-1 cursor-pointer items-center justify-center rounded-xl border-2 border-dashed px-8 py-6 text-sm transition-all ${
            dragOver
              ? 'border-crimson bg-crimson/5 text-crimson'
              : 'border-warm-300 bg-white text-warm-500 hover:border-warm-400 hover:text-warm-700'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".jsonl,.json,.ndjson"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFile(file);
            }}
          />
          <div className="flex flex-col items-center gap-1">
            <svg
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5"
              />
            </svg>
            <span>
              {fileName ? fileName : 'Drop a .jsonl trace file or click to browse'}
            </span>
          </div>
        </div>
      </div>

      {/* Content — only shown when data is loaded */}
      {events && events.length > 0 && (
        <div className="mt-10 animate-fade-in stagger-2">
          {/* Summary bar */}
          <div className="mb-6 flex flex-wrap gap-6">
            {[
              { label: 'Events', value: events.length },
              {
                label: 'Agents',
                value: deriveAgents(events).length,
              },
              {
                label: 'Ticks',
                value: Math.max(...events.map((e) => e.tick)) + 1,
              },
              {
                label: 'Connections',
                value: deriveEdges(events).length,
              },
            ].map((stat) => (
              <div key={stat.label} className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-warm-900">
                  {stat.value}
                </span>
                <span className="text-sm text-warm-400">{stat.label}</span>
              </div>
            ))}
          </div>

          {/* Tabs */}
          <div className="flex gap-1 rounded-xl bg-warm-100 p-1 mb-8">
            {tabs.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex-1 rounded-lg px-4 py-2.5 text-sm font-medium transition-all ${
                  tab === t.id
                    ? 'bg-white text-warm-900 shadow-sm'
                    : 'text-warm-500 hover:text-warm-700'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div>
            {tab === 'map' && <CommunicationMap events={events} />}
            {tab === 'timeline' && <Timeline events={events} />}
            {tab === 'stats' && <AgentStats events={events} />}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!events && (
        <div className="mt-20 flex flex-col items-center justify-center text-center animate-fade-in stagger-3">
          <div className="rounded-full bg-warm-100 p-4">
            <svg
              className="h-8 w-8 text-warm-400"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M7.5 14.25v2.25m3-4.5v4.5m3-6.75v6.75m3-9v9M6 20.25h12A2.25 2.25 0 0 0 20.25 18V6A2.25 2.25 0 0 0 18 3.75H6A2.25 2.25 0 0 0 3.75 6v12A2.25 2.25 0 0 0 6 20.25Z"
              />
            </svg>
          </div>
          <p className="mt-4 text-sm text-warm-400">
            Load the demo or upload a trace file to get started.
          </p>
        </div>
      )}
    </div>
  );
}
