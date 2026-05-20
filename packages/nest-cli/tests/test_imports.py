# SPDX-License-Identifier: Apache-2.0
"""Smoke tests: verify that the deprecated nest-cli shim still imports."""

import warnings


def test_nest_cli_imports() -> None:
    """Importing ``nest_cli`` should succeed and expose a version string."""
    import nest_cli

    assert isinstance(nest_cli.__version__, str)
    assert nest_cli.__version__.startswith("0.")


def test_nest_cli_main_app_reexport() -> None:
    """``nest_cli.main.app`` should re-export the live ``nest_core.cli.app``.

    The shim is expected to emit a DeprecationWarning at import time; we
    force a fresh import so we can observe it (the module may already be
    cached from another test).
    """
    import importlib
    import sys

    sys.modules.pop("nest_cli.main", None)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        module = importlib.import_module("nest_cli.main")
        from nest_core.cli import app as core_app

    assert module.app is core_app
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)
