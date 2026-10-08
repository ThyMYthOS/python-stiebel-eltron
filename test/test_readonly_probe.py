"""Verify the hardware probe's write guard using mocks only."""

import argparse
import importlib.util
import sys
import types
from pathlib import Path

import pytest
from modbus_connection import ModbusError
from modbus_connection.mock import MockModbusConnection, MockModbusUnit

from pystiebeleltron.wpm import WpmStiebelEltronAPI

spec = importlib.util.spec_from_file_location("readonly_probe", Path(__file__).parents[1] / "examples/wpm-readonly-check.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["write_register", "write_registers", "write_coil", "write_coils", "mask_write_register", "read_write_registers", "write_file_record"])
async def test_probe_rejects_all_write_operations_before_forwarding(method: str) -> None:
    unit = MockModbusUnit(MockModbusConnection(), 1)
    writes = []
    unit.on_write(writes.append)
    guard = probe.ReadOnlyUnit(unit)
    with pytest.raises(RuntimeError, match="only input and holding"):
        getattr(guard, method)
    assert not writes


@pytest.mark.asyncio
@pytest.mark.parametrize("raw", [False, True])
async def test_probe_completes_bounded_mock_polls_without_writes_or_values(capsys, raw: bool) -> None:
    unit = MockModbusUnit(MockModbusConnection(), 1)
    writes = []
    unit.on_write(writes.append)
    unit.input[506] = 12345
    await probe.run_probe(unit, "wpm", polls=2, raw=raw)
    assert not writes
    output = capsys.readouterr().out
    assert '"poll": 2' in output
    assert "12345" not in output
    assert '"space": "holding"' in output


@pytest.mark.asyncio
async def test_probe_rejects_unbounded_poll_count() -> None:
    unit = MockModbusUnit(MockModbusConnection(), 1)
    writes = []
    unit.on_write(writes.append)
    with pytest.raises(ValueError):
        await probe.run_probe(unit, "wpm", polls=4)
    assert not unit.read_events and not writes


@pytest.mark.asyncio
async def test_probe_blocks_component_write_end_to_end() -> None:
    unit = MockModbusUnit(MockModbusConnection(), 1)
    writes = []
    unit.on_write(writes.append)
    api = WpmStiebelEltronAPI(probe.ReadOnlyUnit(unit))
    with pytest.raises(RuntimeError, match="only input and holding"):
        await api.system_parameters.write("comfort_temperature_hk_3", 23)
    assert not writes


@pytest.mark.asyncio
async def test_probe_main_closes_connection_on_failure_without_logging_host(monkeypatch, capsys) -> None:
    unit = MockModbusUnit(MockModbusConnection(), 1)
    unit.fail_read(1500, ModbusError(), register_type="holding")
    closed = []
    private_host = "private-host-not-to-log.invalid"

    class Connection:
        def __init__(self, params):
            assert params.host == private_host

        def for_unit(self, device):
            assert device == 1
            return unit

        async def close(self):
            closed.append(True)

    transport = types.ModuleType("modbus_connection.tmodbus")
    transport.ModbusConnection = Connection
    monkeypatch.setitem(sys.modules, "modbus_connection.tmodbus", transport)
    monkeypatch.setattr(probe, "version", lambda name: "test-version")
    args = argparse.Namespace(host=private_host, port=502, unit=1, family="wpm", polls=1, raw=False)
    with pytest.raises(ModbusError):
        await probe.main(args)
    assert closed == [True]
    output = capsys.readouterr().out
    assert private_host not in output
    assert '"result": "ModbusError"' in output
