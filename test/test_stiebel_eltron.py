from __future__ import annotations

import pytest
from pymodbus.pdu.register_message import (
    ReadInputRegistersResponse,
)
from pytest_mock import MockerFixture

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
