# SPDX-License-Identifier: Apache-2.0
"""Deprecated shim — re-exports the CLI from nest-core.

This module exists so that legacy installs that imported
``nest_cli.main:app`` (or referenced it as a console script entry point)
keep working.  All new code should use ``nest_core.cli:app`` directly.

Example::

    # Old, deprecated:
    from nest_cli.main import app
    # New:
    from nest_core.cli import app
"""

from __future__ import annotations

from warnings import warn

from nest_core.cli import app

warn(
    "nest_cli.main is deprecated; import nest_core.cli instead. "
    "The nest-cli package is a no-op shim retained for backwards compatibility.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["app"]


if __name__ == "__main__":
    app()
