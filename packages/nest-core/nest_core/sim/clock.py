# SPDX-License-Identifier: Apache-2.0
"""Virtual clock for the Tier 1 discrete-event simulator.

Example::

    clock = VirtualClock()
    clock.advance_to(10.0)
    assert clock.now == 10.0
"""

from __future__ import annotations


class VirtualClock:
    """Monotonically advancing virtual clock.

    Example::

        clock = VirtualClock()
        clock.advance_to(5.0)
        assert clock.now == 5.0
    """

    __slots__ = ("_now",)

    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    @property
    def now(self) -> float:
        """Current simulation time.

        Example::

            t = clock.now
        """
        return self._now

    def advance_to(self, t: float) -> None:
        """Advance clock to time *t*. Must be >= current time.

        Example::

            clock.advance_to(42.0)
        """
        if t < self._now:
            msg = f"Cannot move clock backwards: {t} < {self._now}"
            raise ValueError(msg)
        self._now = t
