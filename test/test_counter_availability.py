"""Availability transitions of derived counters, independently of their history."""

import pytest
from modbus_connection.mock import MockModbusUnit

from pystiebeleltron import UNAVAILABLE
from pystiebeleltron.lwz import LwzStiebelEltronAPI
from pystiebeleltron.wpm import WpmStiebelEltronAPI
from pystiebeleltron.wpm3 import Wpm3StiebelEltronAPI
from pystiebeleltron.wpm3i import Wpm3iStiebelEltronAPI


@pytest.mark.parametrize(
    ("api_class", "address", "counter"),
    [
        (WpmStiebelEltronAPI, 3500, "vd_heating_day_and_total"),
        (Wpm3StiebelEltronAPI, 3500, "vd_heating_day_and_total"),
        (Wpm3iStiebelEltronAPI, 3500, "vd_heating_day_and_total"),
        (LwzStiebelEltronAPI, 3000, "heat_meter_htg_day_and_total"),
    ],
)
@pytest.mark.parametrize("unavailable_word", [0, 1, 2], ids=["day", "total-low", "total-high"])
@pytest.mark.asyncio()
async def test_energy_counter_availability_and_recovery(
    mock_modbus_unit: MockModbusUnit,
    api_class: type[WpmStiebelEltronAPI | Wpm3StiebelEltronAPI | Wpm3iStiebelEltronAPI | LwzStiebelEltronAPI],
    address: int,
    counter: str,
    unavailable_word: int,
) -> None:
    """An unavailable input hides the value, but preserves the monotonic history."""
    api = api_class(mock_modbus_unit)
    component = api.energy_data
    observed: list[int | None] = []
    component.add_update_listener(lambda: observed.append(getattr(component, counter)))
    assert getattr(component, counter) is None

    unavailable = [2, 10, 1]
    unavailable[unavailable_word] = UNAVAILABLE
    for words, expected in [
        (unavailable, None),
        ([2, 10, 1], 1012),
        (unavailable, None),
        ([1, 9, 1], 1012),  # Recovery must retain the previous high-water mark.
        ([5, 10, 1], 1015),
    ]:
        mock_modbus_unit.input[address] = words
        await api.async_update()
        assert getattr(component, counter) == expected
        assert observed[-1] == expected
    assert observed == [None, 1012, None, 1012, 1015]


@pytest.mark.parametrize(
    ("high", "low", "expected"),
    [(0, 0, 0), (2, 0, 2000), (2, 9, 2009), (UNAVAILABLE, 9, None), (2, UNAVAILABLE, None), (UNAVAILABLE, UNAVAILABLE, None)],
)
@pytest.mark.asyncio()
async def test_compressor_starts_require_both_words(
    mock_modbus_unit: MockModbusUnit,
    high: int,
    low: int,
    expected: int | None,
) -> None:
    """Neither missing word is zero; an actual zero remains a valid reading."""
    api = LwzStiebelEltronAPI(mock_modbus_unit)
    mock_modbus_unit.input[30] = 2
    mock_modbus_unit.input[33] = 9
    await api.async_update()
    assert api.system_values.compressor_starts == 2009

    mock_modbus_unit.input[30] = high
    mock_modbus_unit.input[33] = low
    await api.async_update()
    assert api.system_values.compressor_starts == expected

    mock_modbus_unit.input[30] = 0
    mock_modbus_unit.input[33] = 0
    await api.async_update()
    assert api.system_values.compressor_starts == 0
