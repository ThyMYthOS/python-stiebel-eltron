"""The ISG WPM G subset reads only the six documented temperatures."""

import pytest
from modbus_connection import IllegalDataAddressError, ModbusConnectionError
from modbus_connection.mock import MockModbusConnection, ReadEvent

from pystiebeleltron.wpmg import WpmGStiebelEltronAPI, WpmGSystemValues


@pytest.mark.asyncio()
async def test_wpmg_decoding_and_bounded_reads() -> None:
    unit = MockModbusConnection().for_unit(1)
    unit.input.update({6020: 0xFF9C, 6021: 2720, 6023: 0x8000, 6024: 2938, 6099: 1500, 6100: 5562})
    writes = []
    unit.on_write(writes.append)
    api = WpmGStiebelEltronAPI(unit)
    await api.async_update()
    values = api.system_values
    assert values.brine_inlet_temperature == -1.0
    assert values.brine_outlet_temperature == 27.2
    assert values.condenser_inlet_temperature is None
    assert values.condenser_outlet_temperature == 29.38
    assert values.outside_temperature_averaged == 15.0
    assert values.dhw_temperature_weighted == 55.62
    assert unit.read_events == [ReadEvent("input", 6020, 2), ReadEvent("input", 6023, 2), ReadEvent("input", 6099, 2)]
    assert not writes
    assert len(WpmGSystemValues.declared_fields) == 6
    assert all(not field.writable for field in WpmGSystemValues.declared_fields.values())


@pytest.mark.parametrize("error", [IllegalDataAddressError, ModbusConnectionError])
@pytest.mark.asyncio()
async def test_wpmg_failed_poll_is_reported_and_retried(error) -> None:
    unit = MockModbusConnection().for_unit(1)
    api = WpmGStiebelEltronAPI(unit)
    unit.fail_read(6020, error(), register_type="input")
    with pytest.raises(error):
        await api.async_update()
    unit.fail_read(6020, None, register_type="input")
    unit.input[6020] = 1234
    await api.async_update()
    assert api.system_values.brine_inlet_temperature == 12.34
