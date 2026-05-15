# Contributing to NEST

Thank you for your interest in contributing to NEST! This document provides guidelines for contributing.

## Development setup

```bash
# Clone the repo
git clone https://github.com/projnanda/nest.git
cd nest

# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync all packages
uv sync

# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Run type checking
uv run pyright
```

## Project structure

NEST is a monorepo managed by `uv` workspaces. Each package in `packages/` is an independent Python package that can be installed separately.

## How to contribute

### Reporting bugs

Open an issue with:
- Steps to reproduce
- Expected behavior
- Actual behavior
- NEST version (`nest doctor`)

### Proposing a new plugin

1. Open an issue using the "new plugin proposal" template.
2. Describe the layer, the protocol, and why it's useful.
3. Once approved, implement the layer interface from `nest-sdk`.
4. Add conformance tests.
5. Submit a PR.

### Proposing a new scenario

1. Open an issue using the "new scenario proposal" template.
2. Describe what the scenario tests and which layers it exercises.
3. Once approved, add the scenario YAML and any supporting code.
4. Submit a PR.

### Code style

- Python code is formatted and linted with `ruff`.
- Type annotations are checked with `pyright` in strict mode.
- Every public class and function needs a docstring.
- Every file starts with `# SPDX-License-Identifier: Apache-2.0`.

### Testing

- Run `uv run pytest` before submitting a PR.
- Use `hypothesis` for property-based tests on protocol invariants.
- Aim for high coverage on layer interfaces and core runtime.

### Commit messages

Use conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `chore:`.

## License

By contributing, you agree that your contributions will be licensed under Apache 2.0.
