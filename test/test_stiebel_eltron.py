from __future__ import annotations

import pytest
from modbus_connection.mock import MockModbusConnection, MockModbusUnit

from pystiebeleltron import ControllerModel, RegisterType, StiebelEltronAPI, StiebelEltronModbusError, get_controller_model
from pystiebeleltron.lwz import LwzEnergyDataRegisters, LwzStiebelEltronAPI, LwzSystemValuesRegisters, OperatingMode
from pystiebeleltron.wpm import WpmEnergyDataRegisters, WpmPowerConsumptionRegisters, WpmStiebelEltronAPI, WpmSystemValuesRegisters


def _seed_sequential(unit: MockModbusUnit, api: StiebelEltronAPI) -> None:
    """Seed each register block so a block read returns ``[0, 1, ..., count - 1]``.

    Register ``i`` within a block then reads back as the value ``i``, which is the
    synthetic pattern the assertions below are derived from.
    """
    for block in api._register_blocks:
        store = unit.input if block.register_type == RegisterType.INPUT_REGISTER else unit.holding
        store[block.base_address] = list(range(block.count))


@pytest.mark.asyncio()
async def test_wpm(mock_modbus_unit: MockModbusUnit) -> None:
    api = WpmStiebelEltronAPI(mock_modbus_unit)
    _seed_sequential(mock_modbus_unit, api)

    assert api.is_connected

    await api.async_update()

    assert api.get_register_value(WpmSystemValuesRegisters.ACTUAL_TEMPERATURE_FEK) == 0.2

    assert api.get_register_value(WpmEnergyDataRegisters.VD_HEATING_DAY_AND_TOTAL_CONSUMED) == 12021


@pytest.mark.asyncio()
async def test_wpm_power_consumption_registers(mock_modbus_unit: MockModbusUnit) -> None:
    api = WpmStiebelEltronAPI(mock_modbus_unit)
    _seed_sequential(mock_modbus_unit, api)

    await api.async_update()

    # Block base_address=3707, count=16 → registers[i] = i for i in 0..15
    # Address = base_address + 1 + i, so register at address 3708 is index 0 → value 0
    assert api.get_register_value(WpmPowerConsumptionRegisters.HEATING_24H) == 0
    assert api.get_register_value(WpmPowerConsumptionRegisters.HEATING_12M_FRACTION) == 2
    assert api.get_register_value(WpmPowerConsumptionRegisters.HEATING_12M_WHOLE) == 3
    assert api.get_register_value(WpmPowerConsumptionRegisters.COOLING_24H_FRACTION) == 6
    assert api.get_register_value(WpmPowerConsumptionRegisters.COOLING_24H_WHOLE) == 7
    assert api.get_register_value(WpmPowerConsumptionRegisters.COOLING_12M) == 8
    assert api.get_register_value(WpmPowerConsumptionRegisters.DHW_24H_FRACTION) == 12
    assert api.get_register_value(WpmPowerConsumptionRegisters.DHW_24H_WHOLE) == 13
    assert api.get_register_value(WpmPowerConsumptionRegisters.DHW_12M_FRACTION) == 14
    assert api.get_register_value(WpmPowerConsumptionRegisters.DHW_12M_WHOLE) == 15


@pytest.mark.asyncio()
async def test_lwz(mock_modbus_unit: MockModbusUnit) -> None:
    api = LwzStiebelEltronAPI(mock_modbus_unit)
    _seed_sequential(mock_modbus_unit, api)

    assert api.is_connected

    await api.async_update()

    assert api.get_register_value(LwzSystemValuesRegisters.RELATIVE_HUMIDITY_HC1) == 0.2

    assert api.get_register_value(LwzEnergyDataRegisters.HEAT_METER_HTG_DAY_AND_TOTAL) == 2001

    assert api.get_current_humidity() == 0.2
    assert api.get_current_temp() == 0.0
    assert api.get_target_temp() == 0.1

    assert api.get_operation() == OperatingMode.EMERGENCY_OPERATION

    assert api.get_register_value(LwzSystemValuesRegisters.COMPRESSOR_STARTS) == 30033


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
