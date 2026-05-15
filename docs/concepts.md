# Concepts

## What is NEST?

NEST (Network Environment for Swarm Testing) is an open-source sandbox for testing agent protocols at scale. It is part of NANDA, the Internet of AI Agents.

## The 12 layers

NEST decomposes the agent stack into 12 pluggable layers. Each layer has a stable Python interface. Plugins implement these interfaces.

1. **Transport** — How bytes move between agents
2. **Communication** — Message format and request/response semantics
3. **Identity** — Agent identity and verification
4. **Registry** — How agents find each other
5. **Auth** — Authentication and authorization
6. **Trust** — Reputation and attestation
7. **Payments** — How value moves
8. **Coordination** — How groups decide
9. **Negotiation** — Bargaining between agents
10. **Memory** — Shared state
11. **Privacy** — Encryption and zero-knowledge proofs
12. **Data Facts** — Dataset metadata and exchange

## Three fidelity tiers

- **Tier 1** — Pure simulation with state-machine agents and virtual clock. Scales to 10k+ agents. Deterministic.
- **Tier 2** — Shell agent backed by a real LLM (via litellm). 10–100 agents.
- **Tier 3** — Bring your own Docker container. (Post-MVP)

## Scenarios

A scenario is a YAML file that defines an experiment: how many agents, which plugins for each layer, what task to run, and what failures to inject.

## Plugins

A plugin is a Python package that implements one layer interface. Plugins register via entry points and can declare requirements on other layers.
