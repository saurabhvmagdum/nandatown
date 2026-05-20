# SPDX-License-Identifier: Apache-2.0
"""Deprecated shim package — use ``nest_core.cli`` instead.

This package no longer ships a console script; the ``nest`` binary is now
provided by ``nest-core``.  ``nest_cli.main:app`` still re-exports the
core CLI so legacy entry points continue to function.
"""

__version__ = "0.1.1"
