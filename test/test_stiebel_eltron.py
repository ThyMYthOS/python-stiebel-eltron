from __future__ import annotations

import pytest
from modbus_connection.mock import MockModbusConnection, MockModbusUnit
from modbus_connection.model import Component

from pystiebeleltron import (
    ControllerModel,
    StiebelEltronModbusError,
    UnknownControllerModelError,
    get_controller_model,
)
from pystiebeleltron.lwz import LwzStiebelEltronAPI, OperatingMode
from pystiebeleltron.wpm import WpmStiebelEltronAPI


def _seed(unit: MockModbusUnit, *components: Component) -> None:
    """Seed each component's store so register ``i`` of a block reads back as ``i``.

    Mirrors the synthetic pattern the assertions are derived from: a block whose
    fields start at address ``base`` gets ``[0, 1, 2, ...]`` from ``base`` on, so a
    field at address ``base + n`` decodes the raw value ``n``.
    """
    for component in components:
        fields = component._register_fields.values()
        low = min(field.address for field in fields)
        high = max(field.address + field.count - 1 for field in fields)
        store = unit.input if component.register_space == "input" else unit.holding
        store[low] = list(range(high - low + 1))


@pytest.mark.asyncio()
async def test_wpm(mock_modbus_unit: MockModbusUnit) -> None:
    api = WpmStiebelEltronAPI(mock_modbus_unit)
    _seed(mock_modbus_unit, api.system_values, api.energy_data)

    await api.async_update()

    assert api.system_values.actual_temperature_fek == 0.2
    # vd_heating_day (10) + scaled_sum total (11 + 12 * 1000) = 12021
    assert api.energy_data.vd_heating_day_and_total_consumed == 12021


@pytest.mark.asyncio()
async def test_wpm_repeating_groups(mock_modbus_unit: MockModbusUnit) -> None:
    """Repeated sub-units read as typed lists, each instance at its strided address."""
    api = WpmStiebelEltronAPI(mock_modbus_unit)
    _seed(mock_modbus_unit, api.system_values)

    await api.async_update()

    heat_pumps = api.system_values.heat_pumps
    assert len(heat_pumps) == 6
    # return_temperature is at wire address 541 (raw 41) for HP1, +7 per instance.
    assert heat_pumps[0].return_temperature == 4.1
    assert heat_pumps[5].return_temperature == 7.6
    assert heat_pumps[0].low_pressure == 0.44  # 0.01-scaled

    room_temperatures = api.system_values.room_temperatures
    assert len(room_temperatures) == 5
    # actual_temperature is at wire address 583 (raw 83) for HC1, +4 per instance.
    assert room_temperatures[0].actual_temperature == 8.3
    assert room_temperatures[1].actual_temperature == 8.7

    cooling = api.system_values.room_temperatures_cooling
    assert len(cooling) == 5
    # set_temperature is at wire address 603 (raw 103) for COOLING1, +1 per instance.
    assert cooling[0].set_temperature == 10.3
    assert cooling[4].set_temperature == 10.7


@pytest.mark.asyncio()
async def test_write_out_of_range_rejected(mock_modbus_unit: MockModbusUnit) -> None:
    """A write validator rejects values outside the register's documented range."""
    api = WpmStiebelEltronAPI(mock_modbus_unit)

    # comfort_temperature_hk_1 is a 0.1-scaled holding register with range [5, 30].
    await api.system_parameters.write("comfort_temperature_hk_1", 22)
    assert mock_modbus_unit.holding[1501] == 220

    with pytest.raises(ValueError, match="outside the allowed range"):
        await api.system_parameters.write("comfort_temperature_hk_1", 40)
    # The rejected write must not have reached the device.
    assert mock_modbus_unit.holding[1501] == 220


@pytest.mark.asyncio()
async def test_wpm_power_consumption_registers(mock_modbus_unit: MockModbusUnit) -> None:
    api = WpmStiebelEltronAPI(mock_modbus_unit)
    _seed(mock_modbus_unit, api.power_consumption)

    await api.async_update()

    consumption = api.power_consumption
    assert consumption.heating_24h == 0
    assert consumption.heating_12m_fraction == 2
    assert consumption.heating_12m_whole == 3
    assert consumption.cooling_24h_fraction == 6
    assert consumption.cooling_24h_whole == 7
    assert consumption.cooling_12m == 8
    assert consumption.dhw_24h_fraction == 12
    assert consumption.dhw_24h_whole == 13
    assert consumption.dhw_12m_fraction == 14
    assert consumption.dhw_12m_whole == 15


@pytest.mark.asyncio()
async def test_lwz(mock_modbus_unit: MockModbusUnit) -> None:
    api = LwzStiebelEltronAPI(mock_modbus_unit)
    _seed(mock_modbus_unit, api.system_values, api.system_parameters, api.system_state, api.energy_data)

    await api.async_update()

    assert api.system_values.relative_humidity_hc1 == 0.2
    # heat_meter_htg_day (0) + scaled_sum total (1 + 2 * 1000) = 2001
    assert api.energy_data.heat_meter_htg_day_and_total == 2001

    assert api.get_current_humidity() == 0.2
    assert api.get_current_temp() == 0.0
    assert api.get_target_temp() == 0.1

    assert api.get_operation() == OperatingMode.EMERGENCY_OPERATION

    # compressor_starts_hi (30) * 1000 + compressor_starts_low (33) = 30033
    assert api.system_values.compressor_starts == 30033


@pytest.mark.asyncio()
async def test_write_register(mock_modbus_unit: MockModbusUnit) -> None:
    api = LwzStiebelEltronAPI(mock_modbus_unit)

    await api.set_target_temp(21.5)

    # room_temperature_day_hk1 is a 0.1-scaled holding register at wire address 1001.
    assert mock_modbus_unit.holding[1001] == 215


@pytest.mark.parametrize(
    ("model_id", "expected"),
    [
        (103, ControllerModel.LWZ),
        (104, ControllerModel.LWZ_x04_SOL),
        (390, ControllerModel.WPM_3),
        (391, ControllerModel.WPM_3i),
        (449, ControllerModel.WPMsystem),
        (551, ControllerModel.LWZ_R290),
    ],
)
@pytest.mark.asyncio()
async def test_get_controller_model(mock_modbus_unit: MockModbusUnit, model_id: int, expected: ControllerModel) -> None:
    """Test get_controller_model maps a model id register to its ControllerModel."""
    mock_modbus_unit.input[5001] = model_id
    model = await get_controller_model(mock_modbus_unit)
    assert model == expected


@pytest.mark.asyncio()
async def test_get_controller_model_error_response(mock_modbus_connection: MockModbusConnection) -> None:
    """Test get_controller_model raises error when the modbus read fails."""
    await mock_modbus_connection.close()
    with pytest.raises(StiebelEltronModbusError):
        await get_controller_model(mock_modbus_connection.for_unit(1))


@pytest.mark.asyncio()
async def test_get_controller_model_unknown_id(mock_modbus_unit: MockModbusUnit) -> None:
    """An unrecognized model id surfaces as UnknownControllerModelError, not a comms error."""
    mock_modbus_unit.input[5001] = 999
    with pytest.raises(UnknownControllerModelError) as exc_info:
        await get_controller_model(mock_modbus_unit)
    assert exc_info.value.model_id == 999
    assert not isinstance(exc_info.value, StiebelEltronModbusError)


@pytest.mark.asyncio()
async def test_energy_counter_unavailable(mock_modbus_unit: MockModbusUnit) -> None:
    """A magnitude counter with an unavailable (0x8000) word decodes to None."""
    api = LwzStiebelEltronAPI(mock_modbus_unit)
    _seed(mock_modbus_unit, api.energy_data)
    mock_modbus_unit.input[3002] = 0x8000  # the MWh word of heat_meter_htg_ttl

    await api.async_update()

    assert api.energy_data.heat_meter_htg_ttl is None
    assert api.energy_data.heat_meter_htg_day_and_total is None
