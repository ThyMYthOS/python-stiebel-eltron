"""The ISG WPM G subset reads the documented unambiguous primary registers."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from modbus_connection import GatewayPathUnavailableError, IllegalDataAddressError, ModbusConnectionError, ModbusProtocolError, ServerDeviceBusyError
from modbus_connection.mock import MockModbusConnection

from pystiebeleltron.wpmg import WpmGAlarms, WpmGStiebelEltronAPI, WpmGSystemState, WpmGSystemValues


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
    assert [(event.address, event.count) for event in unit.read_events] == [(6000, 34), (6099, 21), (6123, 5), (7499, 9), (7599, 5), (7649, 4), (7654, 3), (7659, 2), (7662, 1), (7699, 1), (8999, 64)]
    assert all(event.register_type == "input" for event in unit.read_events)
    assert not writes
    assert sum(len(component.declared_fields) for component in (WpmGSystemValues, WpmGSystemState, WpmGAlarms)) == 149
    assert all(not field.writable for component in (WpmGSystemValues, WpmGSystemState, WpmGAlarms) for field in component.declared_fields.values())


@pytest.mark.parametrize("error", [GatewayPathUnavailableError, ModbusConnectionError, ModbusProtocolError, ServerDeviceBusyError])
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


@pytest.mark.parametrize("raw, expected", [(0, False), (1, True), (2, None), (0xFFFF, None), (0x8000, None)])
@pytest.mark.asyncio()
async def test_wpmg_strict_status_and_alarm_values(raw, expected) -> None:
    unit = MockModbusConnection().for_unit(1)
    unit.input.update({6030: raw, 7505: raw, 8999: raw, 9062: raw})
    api = WpmGStiebelEltronAPI(unit)
    await api.async_update()
    assert api.system_values.sg_ready_input_1 is expected
    assert api.system_state.control_signal_brine_pump is expected
    assert api.alarms.level_1_notification is expected
    assert api.alarms.level_3_notification_external_alarm is expected


@pytest.mark.asyncio()
async def test_wpmg_electrical_pressure_and_difference_units() -> None:
    unit = MockModbusConnection().for_unit(1)
    unit.input.update({6104: 0xFFFF, 6105: 325, 6106: 1234, 6108: 123, 6111: 23012, 6114: 4001, 6117: 40000, 6125: 3, 6127: 75})
    api = WpmGStiebelEltronAPI(unit)
    await api.async_update()
    values = api.system_values
    assert values.superheating == -0.01
    assert values.supercooling == 3.25
    assert values.pressure_low_pressure_side == 12.34
    assert values.l1_current == 1.23
    assert values.l1_n_voltage == 230.12
    assert values.l1_l2_voltage == pytest.approx(400.1)
    assert values.l1_power_consumption == 40000
    assert values.current_output_stage_compressor == 3
    assert values.percentage_compressor_speed == 75


@pytest.mark.asyncio()
async def test_rejected_word_isolated_cleared_and_retried() -> None:
    unit = MockModbusConnection().for_unit(1)
    unit.input.update({6020: 1200, 6021: 1300, 6099: 1400})
    api = WpmGStiebelEltronAPI(unit)
    await api.async_update()
    unit.fail_read(6020, IllegalDataAddressError(), register_type="input")
    unit.input[6021] = 1500
    with patch("pystiebeleltron._wpmg_reader.monotonic", return_value=100):
        await api.async_update()
    assert api.system_values.brine_inlet_temperature is None
    assert api.system_values.brine_outlet_temperature == 15
    assert api.system_values.outside_temperature_averaged == 14
    row = next(row for row in api.polling_report["registers"] if row["wire_address"] == 6020)
    assert row["status"] == "unsupported"
    assert row["exception_code"] == 2
    assert row["failure_count"] == 1
    unit.fail_read(6020, None, register_type="input")
    with patch("pystiebeleltron._wpmg_reader.monotonic", return_value=200):
        await api.async_update()
    assert api.system_values.brine_inlet_temperature is None
    assert next(row for row in api.polling_report["registers"] if row["wire_address"] == 6020)["status"] == "retry_pending"
    with patch("pystiebeleltron._wpmg_reader.monotonic", return_value=401):
        await api.async_update()
    assert api.system_values.brine_inlet_temperature == 12
    assert next(row for row in api.polling_report["registers"] if row["wire_address"] == 6020)["status"] == "ok"


@pytest.mark.asyncio()
async def test_probe_budget_preserves_later_healthy_blocks_and_progresses() -> None:
    unit = MockModbusConnection().for_unit(1)
    for address in range(6000, 6034):
        unit.fail_read(address, IllegalDataAddressError(), register_type="input")
    unit.input[6099] = 1500
    api = WpmGStiebelEltronAPI(unit)
    await api.async_update()
    assert api.system_values.outside_temperature_averaged == 15
    assert any(row["status"] == "not_probed_budget" for row in api.polling_report["registers"])
    for _ in range(4):
        await api.async_update()
        assert api.polling_report["requests"] <= 181
    assert all(row["status"] in {"unsupported", "retry_pending"} for row in api.polling_report["registers"] if 6000 <= row["wire_address"] <= 6033)


@pytest.mark.asyncio()
async def test_long_block_rejection_does_not_mark_individual_words_unsupported() -> None:
    async def read(address, count):
        if count > 1:
            raise IllegalDataAddressError()
        return [1234]

    api = WpmGStiebelEltronAPI(SimpleNamespace(read_input_registers=read))
    for _ in range(12):
        await api.async_update()
        assert api.polling_report["requests"] <= 181
    assert api.system_values.brine_inlet_temperature == 12.34
    assert api.system_values.outside_temperature_averaged == 12.34
    assert all(row["status"] == "ok" for row in api.polling_report["registers"] if row["field"] == "system_values.brine_inlet_temperature")
    assert not any(row["status"] == "unsupported" for row in api.polling_report["registers"])


@pytest.mark.asyncio()
async def test_all_registers_rejected_still_produces_diagnostics() -> None:
    api = WpmGStiebelEltronAPI(SimpleNamespace(read_input_registers=AsyncMock(side_effect=IllegalDataAddressError())))
    await api.async_update()
    assert api.polling_report["status"] == "partial"
    assert len(api.polling_report["registers"]) == 149
    assert api.system_values.brine_inlet_temperature is None
    api.retry_failed_registers()


@pytest.mark.parametrize("error", [TimeoutError, asyncio.CancelledError])
@pytest.mark.asyncio()
async def test_timeout_and_cancellation_propagate(error) -> None:
    api = WpmGStiebelEltronAPI(SimpleNamespace(read_input_registers=AsyncMock(side_effect=error())))
    with pytest.raises(error):
        await api.async_update()
    assert api.polling_report["status"] == "error"


@pytest.mark.asyncio()
async def test_short_response_is_not_hidden_by_fallback() -> None:
    api = WpmGStiebelEltronAPI(SimpleNamespace(read_input_registers=AsyncMock(return_value=[])))
    with pytest.raises(ModbusProtocolError):
        await api.async_update()


@pytest.mark.asyncio()
async def test_diagnostics_distinguish_device_sentinel_and_invalid_boolean() -> None:
    unit = MockModbusConnection().for_unit(1)
    unit.input.update({6020: 0x8000, 6030: 2})
    api = WpmGStiebelEltronAPI(unit)
    await api.async_update()
    rows = {row["wire_address"]: row for row in api.polling_report["registers"]}
    assert rows[6020]["status"] == "device_unavailable"
    assert rows[6030]["status"] == "invalid_value"
    assert rows[6030]["raw_u16"] == 2


@pytest.mark.asyncio()
async def test_real_poll_deadline_keeps_failed_request_context() -> None:
    async def read(_address, _count):
        await asyncio.Event().wait()

    api = WpmGStiebelEltronAPI(SimpleNamespace(read_input_registers=read))
    with patch("pystiebeleltron.wpmg.timeout", side_effect=lambda _seconds: asyncio.timeout(0.01)):
        with pytest.raises(TimeoutError):
            await api.async_update()
    assert api.polling_report["error_type"] == "TimeoutError"
    assert api.polling_report["failed_request"] == {"wire_address": 6000, "count": 34, "error_type": "CancelledError", "exception_code": None}


@pytest.mark.parametrize("manual_retry", [False, True])
@pytest.mark.asyncio()
async def test_recovered_blocks_return_to_eleven_reads(manual_retry) -> None:
    refusing = True

    async def read(address, count):
        if refusing:
            raise IllegalDataAddressError()
        return [1234] * count

    api = WpmGStiebelEltronAPI(SimpleNamespace(read_input_registers=read))
    with patch("pystiebeleltron._wpmg_reader.monotonic", return_value=100):
        for _ in range(12):
            await api.async_update()
    refusing = False
    if manual_retry:
        api.retry_failed_registers()
    with patch("pystiebeleltron._wpmg_reader.monotonic", return_value=101 if manual_retry else 401):
        await api.async_update()
    assert api.polling_report["requests"] == 11
    assert api.polling_report["split_blocks"] == []
    assert api.polling_report["duration_seconds"] >= 0
    assert api.system_values.brine_inlet_temperature == 12.34
    assert not any("exception_code" in row for row in api.polling_report["registers"])
