# SPDX-License-Identifier: Apache-2.0
"""Smoke tests: verify that nest-cli imports correctly."""


def test_nest_cli_imports() -> None:
    """Importing nest_cli should succeed and expose a version string."""
    import nest_cli

    assert nest_cli.__version__ == "0.1.0"
