from __future__ import annotations

import pytest
from pymodbus.pdu.register_message import (
    ReadInputRegistersResponse,
)
from pytest_mock import MockerFixture

from pystiebeleltron import ControllerModel, StiebelEltronModbusError, get_controller_model
from pystiebeleltron.lwz import LwzEnergyDataRegisters, LwzStiebelEltronAPI, LwzSystemValuesRegisters, OperatingMode
from pystiebeleltron.wpm import WpmEnergyDataRegisters, WpmStiebelEltronAPI, WpmSystemValuesRegisters


async def read_registers(client: object, address: int, *, count: int = 1, device_id: int = 0, no_response_expected: bool = False) -> ReadInputRegistersResponse:
    """Read a slice from the input register."""
    return ReadInputRegistersResponse(address=address, count=count, registers=list(range(count)))


@pytest.mark.asyncio()
async def test_wpm(mocker: MockerFixture) -> None:
    api = WpmStiebelEltronAPI("localhost")
    mock_connect = mocker.patch("pymodbus.client.AsyncModbusTcpClient.connect")
    mock_close = mocker.patch("pymodbus.client.AsyncModbusTcpClient.close")
    mocker.patch("pymodbus.client.AsyncModbusTcpClient.read_holding_registers", read_registers)
    mocker.patch("pymodbus.client.AsyncModbusTcpClient.read_input_registers", read_registers)

    await api.connect()
    mock_connect.assert_called_once()

    await api.async_update()

    assert api.get_register_value(WpmSystemValuesRegisters.ACTUAL_TEMPERATURE_FEK) == 0.2

    assert api.get_register_value(WpmEnergyDataRegisters.VD_HEATING_DAY_AND_TOTAL_CONSUMED) == 12021

    await api.close()
    mock_close.assert_called_once()


@pytest.mark.asyncio()
async def test_lwz(mocker: MockerFixture) -> None:
    api = LwzStiebelEltronAPI("localhost")
    mock_connect = mocker.patch("pymodbus.client.AsyncModbusTcpClient.connect")
    mock_close = mocker.patch("pymodbus.client.AsyncModbusTcpClient.close")
    mocker.patch("pymodbus.client.AsyncModbusTcpClient.read_holding_registers", read_registers)
    mocker.patch("pymodbus.client.AsyncModbusTcpClient.read_input_registers", read_registers)

    await api.connect()
    mock_connect.assert_called_once()

    await api.async_update()

    assert api.get_register_value(LwzSystemValuesRegisters.RELATIVE_HUMIDITY_HC1) == 0.2

    assert api.get_register_value(LwzEnergyDataRegisters.HEAT_METER_HTG_DAY_AND_TOTAL) == 2001

    assert api.get_current_humidity() == 0.2
    assert api.get_current_temp() == 0.0
    assert api.get_target_temp() == 0.1

    assert api.get_operation() == OperatingMode.EMERGENCY_OPERATION

    assert api.get_register_value(LwzSystemValuesRegisters.COMPRESSOR_STARTS) == 30033

    await api.close()
    mock_close.assert_called_once()


@pytest.mark.asyncio()
async def test_get_controller_model_lwz(mocker: MockerFixture) -> None:
    """Test get_controller_model returns ControllerModel.LWZ for model id 103."""

    async def mock_read_input_registers(self: object, address: int, *, count: int = 1, device_id: int = 0) -> ReadInputRegistersResponse:
        return ReadInputRegistersResponse(address=address, count=count, registers=[103])

    mocker.patch("pymodbus.client.AsyncModbusTcpClient.connect")
    mocker.patch("pymodbus.client.AsyncModbusTcpClient.close")
    mocker.patch("pymodbus.client.AsyncModbusTcpClient.read_input_registers", mock_read_input_registers)

    model = await get_controller_model("localhost", 502)
    assert model == ControllerModel.LWZ


@pytest.mark.asyncio()
async def test_get_controller_model_lwz_x04_sol(mocker: MockerFixture) -> None:
    """Test get_controller_model returns ControllerModel.LWZ_x04_SOL for model id 104."""

    async def mock_read_input_registers(self: object, address: int, *, count: int = 1, device_id: int = 0) -> ReadInputRegistersResponse:
        return ReadInputRegistersResponse(address=address, count=count, registers=[104])

    mocker.patch("pymodbus.client.AsyncModbusTcpClient.connect")
    mocker.patch("pymodbus.client.AsyncModbusTcpClient.close")
    mocker.patch("pymodbus.client.AsyncModbusTcpClient.read_input_registers", mock_read_input_registers)

    model = await get_controller_model("localhost", 502)
    assert model == ControllerModel.LWZ_x04_SOL


@pytest.mark.asyncio()
async def test_get_controller_model_wpm_3(mocker: MockerFixture) -> None:
    """Test get_controller_model returns ControllerModel.WPM_3 for model id 390."""

    async def mock_read_input_registers(self: object, address: int, *, count: int = 1, device_id: int = 0) -> ReadInputRegistersResponse:
        return ReadInputRegistersResponse(address=address, count=count, registers=[390])

    mocker.patch("pymodbus.client.AsyncModbusTcpClient.connect")
    mocker.patch("pymodbus.client.AsyncModbusTcpClient.close")
    mocker.patch("pymodbus.client.AsyncModbusTcpClient.read_input_registers", mock_read_input_registers)

    model = await get_controller_model("localhost", 502)
    assert model == ControllerModel.WPM_3


@pytest.mark.asyncio()
async def test_get_controller_model_wpm_3i(mocker: MockerFixture) -> None:
    """Test get_controller_model returns ControllerModel.WPM_3i for model id 391."""

    async def mock_read_input_registers(self: object, address: int, *, count: int = 1, device_id: int = 0) -> ReadInputRegistersResponse:
        return ReadInputRegistersResponse(address=address, count=count, registers=[391])

    mocker.patch("pymodbus.client.AsyncModbusTcpClient.connect")
    mocker.patch("pymodbus.client.AsyncModbusTcpClient.close")
    mocker.patch("pymodbus.client.AsyncModbusTcpClient.read_input_registers", mock_read_input_registers)

    model = await get_controller_model("localhost", 502)
    assert model == ControllerModel.WPM_3i


@pytest.mark.asyncio()
async def test_get_controller_model_wpm_system(mocker: MockerFixture) -> None:
    """Test get_controller_model returns ControllerModel.WPMsystem for model id 449."""

    async def mock_read_input_registers(self: object, address: int, *, count: int = 1, device_id: int = 0) -> ReadInputRegistersResponse:
        return ReadInputRegistersResponse(address=address, count=count, registers=[449])

    mocker.patch("pymodbus.client.AsyncModbusTcpClient.connect")
    mocker.patch("pymodbus.client.AsyncModbusTcpClient.close")
    mocker.patch("pymodbus.client.AsyncModbusTcpClient.read_input_registers", mock_read_input_registers)

    model = await get_controller_model("localhost", 502)
    assert model == ControllerModel.WPMsystem


@pytest.mark.asyncio()
async def test_get_controller_model_lwz_r290(mocker: MockerFixture) -> None:
    """Test get_controller_model returns ControllerModel.LWZ_R290 for model id 551."""

    async def mock_read_input_registers(self: object, address: int, *, count: int = 1, device_id: int = 0) -> ReadInputRegistersResponse:
        return ReadInputRegistersResponse(address=address, count=count, registers=[551])

    mocker.patch("pymodbus.client.AsyncModbusTcpClient.connect")
    mocker.patch("pymodbus.client.AsyncModbusTcpClient.close")
    mocker.patch("pymodbus.client.AsyncModbusTcpClient.read_input_registers", mock_read_input_registers)

    model = await get_controller_model("localhost", 502)
    assert model == ControllerModel.LWZ_R290


@pytest.mark.asyncio()
async def test_get_controller_model_error_response(mocker: MockerFixture) -> None:
    """Test get_controller_model raises error when modbus returns error."""

    async def mock_read_input_registers_error(self: object, address: int, *, count: int = 1, device_id: int = 0) -> ReadInputRegistersResponse:
        response = ReadInputRegistersResponse(address=address, count=count, registers=[0])
        response.isError = lambda: True
        return response

    mocker.patch("pymodbus.client.AsyncModbusTcpClient.connect")
    mocker.patch("pymodbus.client.AsyncModbusTcpClient.close")
    mocker.patch("pymodbus.client.AsyncModbusTcpClient.read_input_registers", mock_read_input_registers_error)

    with pytest.raises(StiebelEltronModbusError):
        await get_controller_model("localhost", 502)
