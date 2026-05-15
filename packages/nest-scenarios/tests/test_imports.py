# SPDX-License-Identifier: Apache-2.0
"""Smoke tests: verify that nest-scenarios imports correctly."""


def test_nest_scenarios_imports() -> None:
    """Importing nest_scenarios should succeed and expose a version string."""
    import nest_scenarios

    assert nest_scenarios.__version__ == "0.1.0"
