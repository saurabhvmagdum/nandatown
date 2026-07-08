# SPDX-License-Identifier: Apache-2.0
"""Adversarial validators shipped alongside reference plugins.

Each validator targets a specific failure mode the corresponding reference
plugin would silently allow.  They are designed to **fail against the
reference plugin** and **pass against the hardened plugin** the validator
ships next to.

Example::

    from nest_plugins_reference.validators import (
        check_no_cross_partition_leak,
        check_converged,
        check_no_conflicting_commits,
        check_no_equivocation,
        check_no_forged_quorum,
        check_no_stuck_view,
    )
"""

from __future__ import annotations

from nest_plugins_reference.validators.gossip_validators import (
    ConvergenceFailureError,
    PartitionLeakError,
    ValidatorReport,
    check_converged,
    check_no_partition_view_leak,
)

from nest_plugins_reference.validators.bft_validators import (
    BftValidationError,
    BftValidatorReport,
    check_no_conflicting_commits,
    check_no_equivocation,
    check_no_forged_quorum,
    check_no_stuck_view,
)

__all__ = [
    "ConvergenceFailureError",
    "PartitionLeakError",
    "ValidatorReport",
    "check_converged",
    "check_no_partition_view_leak",
    "BftValidationError",
    "BftValidatorReport",
    "check_no_conflicting_commits",
    "check_no_equivocation",
    "check_no_forged_quorum",
    "check_no_stuck_view",
]

