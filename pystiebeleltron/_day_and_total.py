"""A day register plus its total, without counting the midnight transfer twice."""

from __future__ import annotations

import time
from collections.abc import Callable

# How long one half of a midnight transfer waits for the other half. A booking
# into the total that no reset of the day register follows is taken over after
# this time, so the counter cannot freeze; a reset that no booking follows stops
# releasing a later one.
TRANSFER_HOLD_LIMIT = 3600.0


class DayAndTotalCounter:
    """Combine a day register with the total it is booked into at midnight.

    At the day change the controller moves the day register into the total
    register and resets the day register. Both are not necessarily updated in
    the same poll. A WPMsystem has been seen to book the total first: for at
    least one poll the total already holds the day, and the day register still
    does too. Adding the two counts the day twice, and since the counter never
    goes down, the excess stays until the following days have caught up.

    The counter therefore holds a rise of the total back until the day register
    resets, and a reset releases every held rise. For ``TRANSFER_HOLD_LIMIT``
    seconds after a reset, rises of the total pass at once, which covers a
    reset that comes first and a booking in several steps. A reset is the day
    register falling to less than half of its previous reading, which also
    recognises one whose reading was missed while the registers were
    unavailable; a smaller dip is not a reset. A held rise is taken over after
    ``TRANSFER_HOLD_LIMIT`` seconds, which counts the day twice if its reset
    only comes later. A large dip of the day register that recovers would be
    taken for a reset; day registers have not been seen to do that.

    A total that falls below the highest total seen is not a booking, and its
    return to that level is not one either. The value never decreases while the
    object lives. After a restart it starts again from the registers, and a
    first reading taken in the middle of a transfer cannot be recognised.
    """

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        """Start without a value; the first reading sets it."""
        self._clock = clock
        self._highest_total: int | None = None
        self._last_day: int | None = None
        # Rises of the total waiting for their reset, with the time they came.
        self._held_bookings: list[tuple[int, float]] = []
        # When the day register last reset, while that still releases bookings.
        self._reset_at: float | None = None
        self.value: int | None = None

    def update(self, day: int, total: int) -> None:
        """Take one reading of both registers."""
        if self._highest_total is None or self._last_day is None:
            self._highest_total = total
        else:
            now = self._clock()
            self._expire(now)
            if day < self._last_day - day:
                self._held_bookings.clear()
                self._reset_at = now
            booked = total - self._highest_total
            if booked > 0:
                self._highest_total = total
                if self._reset_at is None:
                    self._held_bookings.append((booked, now))
        self._last_day = day
        combined = total + day - sum(amount for amount, _ in self._held_bookings)
        self.value = combined if self.value is None else max(self.value, combined)

    def _expire(self, now: float) -> None:
        self._held_bookings = [(amount, since) for amount, since in self._held_bookings if now - since < TRANSFER_HOLD_LIMIT]
        if self._reset_at is not None and now - self._reset_at >= TRANSFER_HOLD_LIMIT:
            self._reset_at = None
