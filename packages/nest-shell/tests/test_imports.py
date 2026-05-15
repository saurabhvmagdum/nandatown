# SPDX-License-Identifier: Apache-2.0
"""Smoke tests: verify that nest-shell imports correctly."""


def test_nest_shell_imports() -> None:
    """Importing nest_shell should succeed and expose a version string."""
    import nest_shell

    assert nest_shell.__version__ == "0.1.0"
