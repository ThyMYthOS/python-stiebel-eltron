"""The midnight transfer of a day register into its total is counted once."""

from __future__ import annotations

import pytest
from modbus_connection.mock import MockModbusUnit

from pystiebeleltron._day_and_total import TRANSFER_HOLD_LIMIT, DayAndTotalCounter
from pystiebeleltron.lwz import LwzStiebelEltronAPI
from pystiebeleltron.wpm import WpmStiebelEltronAPI
from pystiebeleltron.wpm3 import Wpm3StiebelEltronAPI
from pystiebeleltron.wpm3i import Wpm3iStiebelEltronAPI


class _Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def _replay(readings: list[tuple[int, int]]) -> list[int | None]:
    """Feed readings 30 seconds apart, as a poll would."""
    return _replay_timed([(index * 30.0, day, total) for index, (day, total) in enumerate(readings)])


def _replay_timed(readings: list[tuple[float, int, int]]) -> list[int | None]:
    clock = _Clock()
    counter = DayAndTotalCounter(clock)
    values = []
    for now, day, total in readings:
        clock.now = now
        counter.update(day, total)
        values.append(counter.value)
    return values


_HOUR = 3600.0
_DAY = 24 * _HOUR


def test_total_booked_before_the_day_resets_is_not_counted_twice() -> None:
    """The sequence behind pail23/stiebel_eltron_isg_component#738, as (day, total).

    Three days of 7, 10 and 17 kWh. The total is booked one poll before the day
    register goes back, so the plain sum jumped by a whole day at every midnight
    and the old high-water mark kept that excess.
    """
    readings = [
        (-_HOUR, 7, 72),  # Saturday evening
        (0, 7, 79),  # Sunday 00:00, total booked, day not yet reset
        (30, 0, 79),  # day reset
        (_DAY - _HOUR, 10, 79),  # Sunday evening
        (_DAY, 10, 89),  # Monday 00:00
        (_DAY + 30, 0, 89),
        (2 * _DAY - _HOUR, 17, 89),  # Monday evening
        (2 * _DAY, 17, 106),  # Tuesday 00:00
        (2 * _DAY + 30, 0, 106),
    ]

    assert _replay_timed(readings) == [79, 79, 79, 89, 89, 89, 106, 106, 106]


def test_day_reset_before_the_total_is_booked() -> None:
    """The reverse order needs no hold: the total is taken over as it rises."""
    readings = [(7, 72), (0, 72), (0, 79), (3, 79)]

    assert _replay(readings) == [79, 79, 79, 82]


def test_transfer_in_one_reading() -> None:
    """Both registers changing in the same reading leaves the sum alone.

    This is what the history of one WPM 3i shows at every midnight.
    """
    assert _replay([(7, 72), (0, 79), (2, 79)]) == [79, 79, 81]


def test_a_booking_without_a_day_reset_is_taken_over_after_the_hold_limit() -> None:
    """The counter must not freeze on a controller that never resets the day."""
    clock = _Clock()
    counter = DayAndTotalCounter(clock)
    counter.update(7, 72)
    counter.update(7, 79)
    assert counter.value == 79

    clock.now = TRANSFER_HOLD_LIMIT - 1
    counter.update(8, 79)
    assert counter.value == 80

    clock.now = TRANSFER_HOLD_LIMIT
    counter.update(8, 79)
    assert counter.value == 87


def test_a_late_reset_after_the_hold_limit_does_not_spoil_the_next_midnight() -> None:
    """The reset that comes too late is not matched against the next booking."""
    clock = _Clock()
    counter = DayAndTotalCounter(clock)
    for now, day, total in [
        (0, 7, 72),
        (1, 7, 79),  # booking held
        (TRANSFER_HOLD_LIMIT + 1, 7, 79),  # taken over: 86
        (TRANSFER_HOLD_LIMIT + 2, 0, 79),  # the late reset
        (TRANSFER_HOLD_LIMIT + 3, 5, 79),
        (3 * TRANSFER_HOLD_LIMIT, 5, 84),  # next midnight, total first
        (3 * TRANSFER_HOLD_LIMIT + 1, 0, 84),
    ]:
        clock.now = now
        counter.update(day, total)

    # 86 is the overcount the hold limit accepts; the next midnight adds nothing.
    assert counter.value == 86


def test_a_dip_of_the_day_register_is_not_a_reset() -> None:
    """A day register that goes back a little does not release the next booking."""
    assert _replay([(7, 72), (6, 72), (7, 72), (7, 79), (0, 79)]) == [79, 79, 79, 79, 79]


def test_a_reset_missed_while_unavailable_still_releases_the_booking() -> None:
    """The reading of the reset itself may be lost; the next one shows it."""
    assert _replay([(7, 72), (7, 79), (1, 79), (2, 79)]) == [79, 79, 80, 81]


def test_a_reset_with_a_further_booking_releases_the_held_one() -> None:
    """A booking in two steps whose second step comes with the reset."""
    assert _replay([(7, 72), (7, 75), (0, 79), (2, 79)]) == [79, 79, 79, 81]


def test_a_booking_step_after_the_reset_passes() -> None:
    """A booking in two steps with the reset between them."""
    assert _replay([(7, 72), (7, 75), (0, 75), (0, 79), (2, 79)]) == [79, 79, 79, 79, 81]


def test_a_small_dip_while_a_booking_is_held_keeps_it_held() -> None:
    assert _replay([(7, 72), (7, 79), (6, 79), (7, 79), (0, 79)]) == [79, 79, 79, 79, 79]


def test_an_unpaired_reset_expires() -> None:
    """A reset too long before a booking does not release it."""
    clock = _Clock()
    counter = DayAndTotalCounter(clock)
    for now, day, total in [(0, 7, 72), (1, 0, 72), (TRANSFER_HOLD_LIMIT + 1, 0, 79), (TRANSFER_HOLD_LIMIT + 2, 0, 79)]:
        clock.now = now
        counter.update(day, total)

    assert counter.value == 79


def test_each_held_booking_expires_on_its_own() -> None:
    """A later booking keeps its full hold time when an earlier one expires."""
    clock = _Clock()
    counter = DayAndTotalCounter(clock)
    for now, day, total in [(0, 7, 72), (1, 7, 75), (3500, 7, 79), (3601, 7, 79)]:
        clock.now = now
        counter.update(day, total)

    # The first booking of 3 is taken over, the second of 4 still waits.
    assert counter.value == 82

    clock.now = 3602
    counter.update(0, 79)
    assert counter.value == 82


def test_a_new_booking_after_a_settled_one_waits_again() -> None:
    """Each midnight is judged on its own; an old reset does not carry over."""
    readings = [(0, 5, 50), (30, 5, 55), (60, 0, 55), (_DAY - _HOUR, 4, 55), (_DAY, 4, 59), (_DAY + 30, 0, 59)]

    assert _replay_timed(readings) == [55, 55, 55, 59, 59, 59]


def test_a_booking_shortly_after_a_reset_passes_but_the_next_midnight_is_held() -> None:
    """The window a reset opens closes long before the next day change."""
    readings = [(0, 7, 72), (30, 0, 72), (60, 0, 79), (_DAY - _HOUR, 4, 79), (_DAY, 4, 83), (_DAY + 30, 0, 83)]

    assert _replay_timed(readings) == [79, 79, 79, 83, 83, 83]


def test_a_total_that_goes_back_is_not_a_booking_when_it_returns() -> None:
    """The return to the highest total seen must not be held back."""
    assert _replay([(7, 72), (7, 71), (7, 72), (8, 72)]) == [79, 79, 79, 80]


def test_a_total_that_goes_back_never_lowers_the_value() -> None:
    assert _replay([(2, 1010), (1, 1009), (5, 1010)]) == [1012, 1012, 1015]


@pytest.mark.parametrize(
    ("api_class", "address", "counter"),
    [
        (WpmStiebelEltronAPI, 3510, "vd_heating_day_and_total_consumed"),
        (Wpm3StiebelEltronAPI, 3510, "vd_heating_day_and_total_consumed"),
        (Wpm3iStiebelEltronAPI, 3510, "vd_heating_day_and_total_consumed"),
        (LwzStiebelEltronAPI, 3021, "pwr_con_htg_day_and_total"),
    ],
)
@pytest.mark.asyncio()
async def test_every_controller_counts_the_transfer_once(
    mock_modbus_unit: MockModbusUnit,
    api_class: type[WpmStiebelEltronAPI | Wpm3StiebelEltronAPI | Wpm3iStiebelEltronAPI | LwzStiebelEltronAPI],
    address: int,
    counter: str,
) -> None:
    """The generated components hand their registers to the counter."""
    api = api_class(mock_modbus_unit)
    component = api.energy_data
    values = []
    for day, total in [(7, 72), (7, 79), (0, 79), (10, 79)]:
        mock_modbus_unit.input[address] = [day, total, 0]
        await api.async_update()
        values.append(getattr(component, counter))

    assert values == [79, 79, 79, 89]
