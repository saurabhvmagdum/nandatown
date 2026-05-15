# SPDX-License-Identifier: Apache-2.0
"""Smoke tests: verify that nest-mocks imports correctly."""


def test_nest_mocks_imports() -> None:
    """Importing nest_mocks should succeed and expose a version string."""
    import nest_mocks

    assert nest_mocks.__version__ == "0.1.0"
