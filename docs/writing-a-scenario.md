# Writing a scenario

## Overview

A scenario is a YAML file that defines an experiment. It specifies agents, layer plugins, tasks, failure injection, and metrics.

## Scenario structure

```yaml
name: my-scenario
description: What this scenario tests.

tier: 1                    # 1, 2, or 3
agents:
  count: 100
  brain: state-machine     # or a model name for Tier 2

layers:
  transport: in_memory
  comms: nest_native
  identity: did_key
  registry: in_memory
  auth: jwt
  trust: score_average
  payments: prepaid_credits
  coordination: contract_net
  negotiation: alternating_offers
  memory: blackboard
  privacy: noop
  datafacts: datafacts_v1

task:
  type: marketplace
  config:
    rounds: 50

failures:
  message_drop: 0.05

duration: ticks: 10000

metrics:
  - success_rate
  - mean_latency

output:
  trace: ./traces/output.jsonl
```

## Task types

- `marketplace` — Buyers and sellers exchange goods
- More to come in future phases

## Failure types

- `message_drop` — Probability of dropping a message
- `byzantine_agents` — Fraction of agents that misbehave
- `network_partition` — Split the network at a specific tick
