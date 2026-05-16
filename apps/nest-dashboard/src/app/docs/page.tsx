'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface TocItem {
  id: string;
  label: string;
}

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const TOC: TocItem[] = [
  { id: 'getting-started', label: 'Getting Started' },
  { id: 'installation', label: 'Installation' },
  { id: 'first-experiment', label: 'Your First Experiment' },
  { id: 'scenarios', label: 'Understanding Scenarios' },
  { id: 'layers', label: 'The 12 Layers' },
  { id: 'templates', label: 'Agent Templates' },
  { id: 'plugins', label: 'Writing a Plugin' },
  { id: 'cli', label: 'CLI Reference' },
  { id: 'faq', label: 'FAQ' },
];

/* ------------------------------------------------------------------ */
/*  CopyButton                                                         */
/* ------------------------------------------------------------------ */

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [text]);

  return (
    <button
      onClick={handleCopy}
      className="absolute top-3 right-3 rounded-md border border-warm-700 bg-warm-800 px-2.5 py-1 text-xs font-medium text-warm-300 transition-all hover:bg-warm-700 hover:text-warm-100"
      aria-label="Copy to clipboard"
    >
      {copied ? 'Copied!' : 'Copy'}
    </button>
  );
}

/* ------------------------------------------------------------------ */
/*  CodeBlock                                                          */
/* ------------------------------------------------------------------ */

function CodeBlock({
  children,
  title,
}: {
  children: string;
  title?: string;
}) {
  return (
    <div className="group relative my-4 overflow-hidden rounded-xl border border-warm-800 bg-warm-900">
      {title && (
        <div className="border-b border-warm-800 bg-warm-950 px-4 py-2 text-xs font-medium text-warm-400">
          {title}
        </div>
      )}
      <CopyButton text={children} />
      <pre className="overflow-x-auto p-4 pr-20 text-sm leading-relaxed text-warm-200">
        <code className="font-mono">{children}</code>
      </pre>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  TerminalBlock — simulated terminal output                          */
/* ------------------------------------------------------------------ */

function TerminalBlock({ children }: { children: string }) {
  return (
    <div className="group relative my-4 overflow-hidden rounded-xl border border-warm-800 bg-warm-950">
      <div className="flex items-center gap-2 border-b border-warm-800 bg-warm-900 px-4 py-2.5">
        <span className="h-3 w-3 rounded-full bg-red-500/80" />
        <span className="h-3 w-3 rounded-full bg-yellow-500/80" />
        <span className="h-3 w-3 rounded-full bg-green-500/80" />
        <span className="ml-2 text-xs text-warm-500">Terminal</span>
      </div>
      <pre className="overflow-x-auto p-4 text-sm leading-relaxed text-green-400">
        <code className="font-mono">{children}</code>
      </pre>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  InlineCode                                                         */
/* ------------------------------------------------------------------ */

function InlineCode({ children }: { children: React.ReactNode }) {
  return (
    <code className="rounded-md border border-warm-200 bg-warm-100 px-1.5 py-0.5 text-sm font-mono text-crimson">
      {children}
    </code>
  );
}

/* ------------------------------------------------------------------ */
/*  Section wrapper                                                    */
/* ------------------------------------------------------------------ */

function Section({
  id,
  title,
  children,
}: {
  id: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="scroll-mt-24 py-16 first:pt-8">
      <h2 className="mb-8 text-3xl font-bold tracking-tight text-warm-900">
        {title}
      </h2>
      {children}
    </section>
  );
}

/* ------------------------------------------------------------------ */
/*  Sidebar (desktop + mobile)                                         */
/* ------------------------------------------------------------------ */

function Sidebar({
  activeId,
  open,
  onClose,
}: {
  activeId: string;
  open: boolean;
  onClose: () => void;
}) {
  return (
    <>
      {/* Backdrop (mobile) */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Panel */}
      <aside
        className={`
          fixed top-16 left-0 z-50 h-[calc(100vh-4rem)] w-72 transform border-r border-warm-200
          bg-white/95 backdrop-blur-md transition-transform duration-300 ease-in-out
          lg:sticky lg:z-10 lg:translate-x-0 lg:border-r lg:bg-white/80
          ${open ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        <nav className="h-full overflow-y-auto px-6 py-8">
          <p className="mb-6 text-xs font-semibold uppercase tracking-widest text-warm-400">
            Documentation
          </p>
          <ul className="space-y-1">
            {TOC.map((item) => {
              const isActive = activeId === item.id;
              return (
                <li key={item.id}>
                  <a
                    href={`#${item.id}`}
                    onClick={onClose}
                    className={`
                      flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-all
                      ${
                        isActive
                          ? 'bg-crimson/10 text-crimson'
                          : 'text-warm-500 hover:bg-warm-50 hover:text-warm-900'
                      }
                    `}
                  >
                    {isActive && (
                      <span className="mr-2.5 h-1.5 w-1.5 rounded-full bg-crimson" />
                    )}
                    {item.label}
                  </a>
                </li>
              );
            })}
          </ul>

          <div className="mt-10 rounded-xl border border-warm-200 bg-warm-50 p-4">
            <p className="text-xs font-semibold text-warm-700">Need help?</p>
            <p className="mt-1 text-xs leading-relaxed text-warm-500">
              Open an issue on{' '}
              <a
                href="https://github.com/mariagorskikh/nest/issues"
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-crimson hover:underline"
              >
                GitHub
              </a>{' '}
              or join the{' '}
              <a
                href="https://github.com/mariagorskikh/nest/discussions"
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-crimson hover:underline"
              >
                Discussions
              </a>
              .
            </p>
          </div>
        </nav>
      </aside>
    </>
  );
}

/* ------------------------------------------------------------------ */
/*  FAQ Item                                                           */
/* ------------------------------------------------------------------ */

function FaqItem({
  question,
  answer,
}: {
  question: string;
  answer: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-b border-warm-200 last:border-b-0">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between py-5 text-left"
      >
        <span className="text-base font-semibold text-warm-900">
          {question}
        </span>
        <svg
          className={`h-5 w-5 shrink-0 text-warm-400 transition-transform duration-200 ${
            open ? 'rotate-180' : ''
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <div className="pb-5 text-sm leading-relaxed text-warm-600">
          {answer}
        </div>
      )}
    </div>
  );
}

/* ================================================================== */
/*  Page                                                               */
/* ================================================================== */

export default function DocsPage() {
  const [activeId, setActiveId] = useState('getting-started');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  /* ---- IntersectionObserver for active section tracking ---- */
  useEffect(() => {
    const ids = TOC.map((t) => t.id);
    const elements = ids
      .map((id) => document.getElementById(id))
      .filter(Boolean) as HTMLElement[];

    if (elements.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        // Find the first visible section
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => {
            const aIdx = ids.indexOf(a.target.id);
            const bIdx = ids.indexOf(b.target.id);
            return aIdx - bIdx;
          });

        if (visible.length > 0) {
          setActiveId(visible[0].target.id);
        }
      },
      { rootMargin: '-80px 0px -60% 0px', threshold: 0 },
    );

    elements.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  return (
    <div className="relative min-h-screen bg-white">
      {/* Mobile menu button */}
      <button
        onClick={() => setSidebarOpen(true)}
        className="fixed bottom-6 left-6 z-50 flex h-12 w-12 items-center justify-center rounded-full border border-warm-200 bg-white shadow-lg transition-transform hover:scale-105 lg:hidden"
        aria-label="Open navigation"
      >
        <svg
          className="h-5 w-5 text-warm-700"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M4 6h16M4 12h16M4 18h16"
          />
        </svg>
      </button>

      {/* Sidebar */}
      <Sidebar
        activeId={activeId}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main content */}
      <div className="lg:ml-72">
        <div className="mx-auto max-w-3xl px-6 pb-24 lg:px-12">
          {/* Hero */}
          <div className="pb-12 pt-12">
            <div className="inline-flex items-center gap-2 rounded-full border border-crimson/20 bg-crimson/5 px-3.5 py-1 text-xs font-medium text-crimson">
              <span className="h-1.5 w-1.5 rounded-full bg-crimson" />
              Documentation
            </div>
            <h1 className="mt-6 text-4xl font-bold tracking-tight text-warm-950 sm:text-5xl">
              NEST Documentation
            </h1>
            <p className="mt-4 text-lg leading-relaxed text-warm-500">
              Everything you need to install, configure, and run multi-agent
              simulations with NEST. Written for humans, not just engineers.
            </p>
          </div>

          <div className="h-px bg-warm-200" />

          {/* ================================================== */}
          {/*  Getting Started                                    */}
          {/* ================================================== */}
          <Section id="getting-started" title="Getting Started">
            <h3 className="mb-4 text-xl font-semibold text-warm-800">
              What is NEST?
            </h3>
            <p className="mb-4 text-base leading-relaxed text-warm-600">
              NEST is a sandbox where you can test how AI agents interact with
              each other. Think of it like a flight simulator, but for AI agent
              networks. You define a scenario (like a marketplace or an
              election), NEST creates the agents, runs the simulation, and shows
              you exactly what happened.
            </p>
            <p className="mb-8 text-base leading-relaxed text-warm-600">
              There are no black boxes here. Every message, every decision, every
              trust score is recorded in a trace file you can inspect, replay,
              and visualize.
            </p>

            <h3 className="mb-4 text-xl font-semibold text-warm-800">
              Who is NEST for?
            </h3>
            <div className="grid gap-4 sm:grid-cols-2">
              {[
                {
                  title: 'Researchers',
                  desc: 'Study emergent behavior, coordination failures, and trust dynamics in multi-agent systems.',
                },
                {
                  title: 'Protocol Designers',
                  desc: 'Stress-test your protocol with hundreds of agents before deploying it to the real world.',
                },
                {
                  title: 'Developers',
                  desc: 'Build and debug multi-agent applications with complete observability and reproducible traces.',
                },
                {
                  title: 'Students',
                  desc: 'Learn about AI coordination, game theory, and agent interaction patterns hands-on.',
                },
              ].map((card) => (
                <div
                  key={card.title}
                  className="rounded-xl border border-warm-200 bg-warm-50/50 p-5"
                >
                  <p className="font-semibold text-warm-900">{card.title}</p>
                  <p className="mt-1.5 text-sm leading-relaxed text-warm-500">
                    {card.desc}
                  </p>
                </div>
              ))}
            </div>
          </Section>

          <div className="h-px bg-warm-200" />

          {/* ================================================== */}
          {/*  Installation                                       */}
          {/* ================================================== */}
          <Section id="installation" title="Installation">
            <h3 className="mb-3 text-lg font-semibold text-warm-800">
              Prerequisites
            </h3>
            <ul className="mb-6 list-inside list-disc space-y-1 text-base text-warm-600">
              <li>
                <strong>Python 3.12+</strong> &mdash; check with{' '}
                <InlineCode>python --version</InlineCode>
              </li>
            </ul>

            <h3 className="mb-3 text-lg font-semibold text-warm-800">
              Install the CLI
            </h3>
            <CodeBlock>pip install nest-cli</CodeBlock>

            <h3 className="mb-3 text-lg font-semibold text-warm-800">
              Verify your installation
            </h3>
            <CodeBlock>nest doctor</CodeBlock>

            <p className="mb-3 text-sm text-warm-500">
              You should see output like this:
            </p>
            <TerminalBlock>
{`$ nest doctor
NEST CLI v0.6.0
Python ......... 3.12.4  ✓
Runtime ........ ok       ✓
Plugins ........ 12/12    ✓
Scenarios ...... 6 found  ✓
Dashboard ...... ready    ✓

All checks passed. You're good to go.`}
            </TerminalBlock>
          </Section>

          <div className="h-px bg-warm-200" />

          {/* ================================================== */}
          {/*  Your First Experiment                               */}
          {/* ================================================== */}
          <Section id="first-experiment" title="Your First Experiment">
            <p className="mb-8 text-base leading-relaxed text-warm-600">
              Let&rsquo;s run a marketplace simulation end-to-end in four steps.
              This will create agents, run the scenario, and produce a visual
              report.
            </p>

            {/* Step 1 */}
            <div className="mb-8">
              <div className="flex items-center gap-3 mb-3">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-crimson text-xs font-bold text-white">
                  1
                </span>
                <h3 className="text-lg font-semibold text-warm-800">
                  Run a scenario
                </h3>
              </div>
              <p className="mb-3 text-sm text-warm-600">
                This reads the scenario YAML, spins up the agents, and executes
                the simulation. The trace is saved automatically.
              </p>
              <CodeBlock>nest run scenarios/marketplace.yaml</CodeBlock>
            </div>

            {/* Step 2 */}
            <div className="mb-8">
              <div className="flex items-center gap-3 mb-3">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-crimson text-xs font-bold text-white">
                  2
                </span>
                <h3 className="text-lg font-semibold text-warm-800">
                  Inspect the trace
                </h3>
              </div>
              <p className="mb-3 text-sm text-warm-600">
                Opens an interactive terminal viewer showing every message,
                decision, and state change in chronological order.
              </p>
              <CodeBlock>nest inspect traces/marketplace.jsonl</CodeBlock>
            </div>

            {/* Step 3 */}
            <div className="mb-8">
              <div className="flex items-center gap-3 mb-3">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-crimson text-xs font-bold text-white">
                  3
                </span>
                <h3 className="text-lg font-semibold text-warm-800">
                  Open the dashboard
                </h3>
              </div>
              <p className="mb-3 text-sm text-warm-600">
                Launches a local web dashboard where you can visualize agent
                interactions, replay events, and explore the network graph.
              </p>
              <CodeBlock>nest dashboard traces/marketplace.jsonl</CodeBlock>
            </div>

            {/* Step 4 */}
            <div className="mb-8">
              <div className="flex items-center gap-3 mb-3">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-crimson text-xs font-bold text-white">
                  4
                </span>
                <h3 className="text-lg font-semibold text-warm-800">
                  View metrics
                </h3>
              </div>
              <p className="mb-3 text-sm text-warm-600">
                Generates an HTML report with aggregated metrics &mdash;
                convergence time, message count, trust distribution, and more.
              </p>
              <CodeBlock>nest report traces/marketplace.jsonl -o report.html</CodeBlock>
            </div>
          </Section>

          <div className="h-px bg-warm-200" />

          {/* ================================================== */}
          {/*  Understanding Scenarios                             */}
          {/* ================================================== */}
          <Section id="scenarios" title="Understanding Scenarios">
            <p className="mb-6 text-base leading-relaxed text-warm-600">
              A scenario is a YAML file that describes the entire simulation:
              which agents exist, what rules they follow, and what you want to
              measure. Here is a complete example with annotations.
            </p>

            <CodeBlock title="scenarios/marketplace.yaml">
{`name: marketplace                   # Unique scenario identifier
tier: 1                              # 1 = rule-based, 2 = LLM-backed

agents:
  count: 50                          # Number of agents to create
  brain: rule                        # "rule" or "llm"
  roles:                             # Role distribution
    - buyer: 25
    - seller: 25

layers:                              # Which protocol layers to activate
  - transport
  - communication
  - identity
  - trust
  - payments
  - negotiation

task: >
  Buyers search for the best price.
  Sellers compete for buyers.
  Run until the market reaches equilibrium.

duration: 300                        # Max duration in seconds
metrics:                             # What to measure
  - convergence_time
  - avg_price
  - trust_distribution
  - messages_per_agent

output: traces/marketplace.jsonl     # Where to write the trace`}
            </CodeBlock>

            <h3 className="mb-4 mt-8 text-lg font-semibold text-warm-800">
              Scenario fields
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-warm-200">
                    <th className="pb-3 pr-6 text-left font-semibold text-warm-900">
                      Field
                    </th>
                    <th className="pb-3 text-left font-semibold text-warm-900">
                      Description
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-warm-100">
                  {[
                    ['name', 'Unique identifier for the scenario'],
                    ['tier', '1 for rule-based agents, 2 for LLM-backed agents'],
                    ['agents.count', 'Total number of agents to spawn'],
                    ['agents.brain', '"rule" (fast, deterministic) or "llm" (GPT/Claude-backed)'],
                    ['agents.roles', 'List of roles and how many agents get each role'],
                    ['layers', 'Protocol layers to activate (see The 12 Layers)'],
                    ['task', 'Plain-English description of what agents should do'],
                    ['duration', 'Maximum simulation time in seconds'],
                    ['metrics', 'List of metrics to collect during the run'],
                    ['output', 'File path for the trace output'],
                  ].map(([field, desc]) => (
                    <tr key={field}>
                      <td className="py-3 pr-6 font-mono text-sm text-crimson">
                        {field}
                      </td>
                      <td className="py-3 text-warm-600">{desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <h3 className="mb-4 mt-10 text-lg font-semibold text-warm-800">
              Available scenarios
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-warm-200">
                    <th className="pb-3 pr-6 text-left font-semibold text-warm-900">
                      Scenario
                    </th>
                    <th className="pb-3 text-left font-semibold text-warm-900">
                      Description
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-warm-100">
                  {[
                    ['marketplace', 'Buyers and sellers negotiate prices in a competitive market'],
                    ['auction', 'Agents bid on items using various auction strategies'],
                    ['voting', 'Agents vote on proposals with different preference models'],
                    ['consensus', 'Agents attempt to reach agreement on a shared state'],
                    ['supply_chain', 'Multi-tier supply chain with producers, distributors, and retailers'],
                    ['reputation', 'Agents build and evaluate reputation scores over repeated interactions'],
                  ].map(([name, desc]) => (
                    <tr key={name}>
                      <td className="py-3 pr-6 font-mono text-sm text-crimson">
                        {name}
                      </td>
                      <td className="py-3 text-warm-600">{desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>

          <div className="h-px bg-warm-200" />

          {/* ================================================== */}
          {/*  The 12 Layers                                      */}
          {/* ================================================== */}
          <Section id="layers" title="The 12 Layers">
            <p className="mb-6 text-base leading-relaxed text-warm-600">
              NEST organizes agent capabilities into 12 protocol layers. Each
              layer has a default plugin you can swap out, and you only activate
              the layers your scenario needs.
            </p>

            <div className="overflow-x-auto rounded-xl border border-warm-200">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-warm-200 bg-warm-50">
                    <th className="px-4 py-3 text-left font-semibold text-warm-900">
                      Layer
                    </th>
                    <th className="px-4 py-3 text-left font-semibold text-warm-900">
                      What it does
                    </th>
                    <th className="hidden px-4 py-3 text-left font-semibold text-warm-900 md:table-cell">
                      Default plugin
                    </th>
                    <th className="hidden px-4 py-3 text-left font-semibold text-warm-900 lg:table-cell">
                      Example use case
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-warm-100">
                  {[
                    ['Transport', 'Moves messages between agents', 'nest-zmq', 'Local or networked agent communication'],
                    ['Communication', 'Structures message formats and protocols', 'nest-acl', 'FIPA-ACL compliant messaging'],
                    ['Identity', 'Assigns and verifies agent identities', 'nest-did', 'Decentralized identity for each agent'],
                    ['Registry', 'Discovers and lists available agents', 'nest-registry', 'Service discovery in large swarms'],
                    ['Auth', 'Handles authentication and permissions', 'nest-auth', 'Role-based access between agents'],
                    ['Trust', 'Calculates and updates trust scores', 'nest-trust', 'Reputation-weighted interactions'],
                    ['Payments', 'Manages virtual currency and transfers', 'nest-ledger', 'Token-based marketplace economies'],
                    ['Coordination', 'Orchestrates multi-agent workflows', 'nest-coord', 'Task assignment and load balancing'],
                    ['Negotiation', 'Runs negotiation protocols', 'nest-negotiate', 'Price bargaining, SLA negotiation'],
                    ['Memory', 'Stores and retrieves agent memory', 'nest-memory', 'Learning from past interactions'],
                    ['Privacy', 'Enforces data-sharing boundaries', 'nest-privacy', 'Selective disclosure of agent data'],
                    ['Data Facts', 'Validates and attests to data claims', 'nest-facts', 'Provenance checking, fact verification'],
                  ].map(([layer, what, plugin, example]) => (
                    <tr key={layer} className="hover:bg-warm-50/50 transition-colors">
                      <td className="whitespace-nowrap px-4 py-3 font-semibold text-warm-900">
                        {layer}
                      </td>
                      <td className="px-4 py-3 text-warm-600">{what}</td>
                      <td className="hidden px-4 py-3 font-mono text-xs text-crimson md:table-cell">
                        {plugin}
                      </td>
                      <td className="hidden px-4 py-3 text-warm-500 lg:table-cell">
                        {example}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>

          <div className="h-px bg-warm-200" />

          {/* ================================================== */}
          {/*  Agent Templates                                     */}
          {/* ================================================== */}
          <Section id="templates" title="Agent Templates">
            <p className="mb-6 text-base leading-relaxed text-warm-600">
              Templates are YAML files that define how an agent behaves &mdash;
              its role, personality, decision logic, and which LLM provider to
              use. They make it easy to reuse and share agent configurations.
            </p>

            <h3 className="mb-3 text-lg font-semibold text-warm-800">
              List available templates
            </h3>
            <CodeBlock>nest templates list</CodeBlock>

            <h3 className="mb-3 mt-6 text-lg font-semibold text-warm-800">
              Inspect a template
            </h3>
            <CodeBlock>nest templates show marketplace-buyer</CodeBlock>

            <h3 className="mb-3 mt-6 text-lg font-semibold text-warm-800">
              Duplicate and customize
            </h3>
            <p className="mb-3 text-sm text-warm-600">
              Start from an existing template and make it your own.
            </p>
            <CodeBlock>nest templates duplicate marketplace-buyer my-buyer</CodeBlock>

            <h3 className="mb-3 mt-6 text-lg font-semibold text-warm-800">
              Create from scratch
            </h3>
            <p className="mb-3 text-sm text-warm-600">
              Create a brand-new template with a system prompt and LLM provider.
            </p>
            <CodeBlock>
{`nest templates create my-agent \\
  --prompt "You are a cautious buyer who never pays above market price." \\
  --provider openai`}
            </CodeBlock>
          </Section>

          <div className="h-px bg-warm-200" />

          {/* ================================================== */}
          {/*  Writing a Plugin                                    */}
          {/* ================================================== */}
          <Section id="plugins" title="Writing a Plugin">
            <p className="mb-6 text-base leading-relaxed text-warm-600">
              Plugins let you replace any of the 12 layers with your own
              implementation. A plugin is a Python class that implements a layer
              interface, packaged as a standard Python package.
            </p>

            <h3 className="mb-3 text-lg font-semibold text-warm-800">
              Minimal plugin example
            </h3>
            <CodeBlock title="my_trust_plugin/plugin.py">
{`from nest.layers import TrustLayer

class MyTrustPlugin(TrustLayer):
    """Custom trust layer that decays over time."""

    name = "my-trust"

    def initialize(self, config: dict) -> None:
        self.decay_rate = config.get("decay_rate", 0.95)
        self.scores: dict[str, float] = {}

    def query(self, agent_id: str) -> float:
        """Return the current trust score for an agent."""
        return self.scores.get(agent_id, 0.5)

    def update(self, agent_id: str, outcome: bool) -> None:
        """Update trust based on interaction outcome."""
        current = self.scores.get(agent_id, 0.5)
        delta = 0.1 if outcome else -0.2
        self.scores[agent_id] = max(0, min(1, current + delta))

    def tick(self) -> None:
        """Called each simulation step. Apply time decay."""
        for agent_id in self.scores:
            self.scores[agent_id] *= self.decay_rate`}
            </CodeBlock>

            <h3 className="mb-3 mt-8 text-lg font-semibold text-warm-800">
              Register via entry point
            </h3>
            <p className="mb-3 text-sm text-warm-600">
              Add the plugin to your{' '}
              <InlineCode>pyproject.toml</InlineCode> so NEST can discover it
              automatically.
            </p>
            <CodeBlock title="pyproject.toml">
{`[project]
name = "my-trust-plugin"
version = "0.1.0"

[project.entry-points."nest.plugins"]
my-trust = "my_trust_plugin.plugin:MyTrustPlugin"`}
            </CodeBlock>

            <h3 className="mb-3 mt-8 text-lg font-semibold text-warm-800">
              Test conformance
            </h3>
            <p className="mb-3 text-sm text-warm-600">
              NEST includes a conformance test suite to verify your plugin
              implements the layer interface correctly.
            </p>
            <CodeBlock>nest plugins conform my-trust-plugin</CodeBlock>
          </Section>

          <div className="h-px bg-warm-200" />

          {/* ================================================== */}
          {/*  CLI Reference                                       */}
          {/* ================================================== */}
          <Section id="cli" title="CLI Reference">
            <p className="mb-6 text-base leading-relaxed text-warm-600">
              All NEST operations are available through the{' '}
              <InlineCode>nest</InlineCode> command-line interface.
            </p>

            <div className="overflow-x-auto rounded-xl border border-warm-200">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-warm-200 bg-warm-50">
                    <th className="px-4 py-3 text-left font-semibold text-warm-900">
                      Command
                    </th>
                    <th className="px-4 py-3 text-left font-semibold text-warm-900">
                      Description
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-warm-100">
                  {[
                    ['nest run <scenario.yaml>', 'Run a scenario and produce a trace file'],
                    ['nest inspect <trace.jsonl>', 'Inspect a trace in an interactive terminal viewer'],
                    ['nest report <trace.jsonl>', 'Generate an HTML metrics report'],
                    ['nest dashboard [trace.jsonl]', 'Open the web dashboard (optionally preloading a trace)'],
                    ['nest init <name>', 'Scaffold a new scenario with default settings'],
                    ['nest doctor', 'Check your installation health and plugin status'],
                    ['nest version', 'Print the installed NEST version'],
                    ['nest plugins list', 'List all installed and available plugins'],
                    ['nest templates list', 'List available agent templates'],
                    ['nest templates show <name>', 'Display the contents of a template'],
                    ['nest templates create <name>', 'Create a new agent template'],
                    ['nest templates duplicate <src> <dest>', 'Duplicate an existing template'],
                  ].map(([cmd, desc]) => (
                    <tr key={cmd} className="hover:bg-warm-50/50 transition-colors">
                      <td className="whitespace-nowrap px-4 py-3 font-mono text-sm text-crimson">
                        {cmd}
                      </td>
                      <td className="px-4 py-3 text-warm-600">{desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>

          <div className="h-px bg-warm-200" />

          {/* ================================================== */}
          {/*  FAQ                                                 */}
          {/* ================================================== */}
          <Section id="faq" title="FAQ">
            <div className="rounded-xl border border-warm-200 bg-white px-6">
              <FaqItem
                question="Do I need an API key?"
                answer={
                  <p>
                    Only for <strong>Tier 2</strong> scenarios that use
                    LLM-backed agents. Tier 1 scenarios run entirely locally
                    with rule-based agents and require no API key or internet
                    connection.
                  </p>
                }
              />
              <FaqItem
                question="How many agents can NEST handle?"
                answer={
                  <p>
                    <strong>Tier 1</strong> (rule-based): 10,000+ agents on a
                    modern laptop. <strong>Tier 2</strong> (LLM-backed): 10
                    &ndash; 100 agents, limited by API rate limits and cost.
                  </p>
                }
              />
              <FaqItem
                question="Can I use my own LLM?"
                answer={
                  <p>
                    Yes. Set <InlineCode>llm_provider</InlineCode> and{' '}
                    <InlineCode>llm_model</InlineCode> in your scenario YAML or
                    agent template. NEST supports OpenAI, Anthropic, and any
                    OpenAI-compatible endpoint.
                  </p>
                }
              />
              <FaqItem
                question="Is NEST production-ready?"
                answer={
                  <p>
                    NEST is currently alpha/research software. It&rsquo;s
                    excellent for testing, benchmarking, and research, but it is
                    not intended for production workloads. APIs may change
                    between releases.
                  </p>
                }
              />
            </div>
          </Section>

          {/* ================================================== */}
          {/*  Footer CTA                                          */}
          {/* ================================================== */}
          <div className="mt-8 rounded-2xl border border-warm-200 bg-warm-50 p-8 text-center sm:p-12">
            <h3 className="text-2xl font-bold tracking-tight text-warm-900">
              Ready to start?
            </h3>
            <p className="mx-auto mt-3 max-w-md text-sm leading-relaxed text-warm-500">
              Install the CLI, pick a scenario, and run your first simulation in
              under two minutes.
            </p>
            <div className="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <a
                href="#installation"
                className="inline-flex items-center justify-center rounded-lg bg-crimson px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-crimson-dark"
              >
                Install NEST
              </a>
              <a
                href="https://github.com/mariagorskikh/nest"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center rounded-lg border border-warm-300 bg-white px-6 py-2.5 text-sm font-semibold text-warm-700 transition-colors hover:bg-warm-50"
              >
                View on GitHub
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
