"""Replay the public WPM G poll without depending on a live gateway."""

import json
from pathlib import Path

import pytest
from modbus_connection.mock import MockModbusConnection

from pystiebeleltron.wpmg import WpmGAlarms, WpmGStiebelEltronAPI, WpmGSystemState, WpmGSystemValues

CAPTURE = Path(__file__).parent / "fixtures" / "wpmg_primary_capture.json"


@pytest.mark.asyncio()
async def test_public_wpmg_capture_replays_every_declared_field() -> None:
    capture = json.loads(CAPTURE.read_text(encoding="utf-8"))
    rows = capture["rows"]
    by_address = {address: (field, raw, expected) for address, field, raw, expected in rows}
    assert len(rows) == len(by_address) == 149
    assert {field for _, field, _, _ in rows} == {
        f"{component}.{name}"
        for component, model in (
            ("system_values", WpmGSystemValues),
            ("system_state", WpmGSystemState),
            ("alarms", WpmGAlarms),
        )
        for name in model.declared_fields
    }

    unit = MockModbusConnection().for_unit(1)
    unit.input.update({address: raw for address, _, raw, _ in rows})
    writes = []
    unit.on_write(writes.append)
    api = WpmGStiebelEltronAPI(unit)
    await api.async_update()

    report = api.polling_report
    assert report["status"] == "partial"  # Ten device sentinel values remain unavailable.
    assert report["function_code"] == 4
    assert report["requests"] == 11
    assert report["usable_registers"] == 139
    assert len(unit.read_events) == 11
    assert all(event.register_type == "input" for event in unit.read_events)
    read_addresses = {
        address
        for event in unit.read_events
        for address in range(event.address, event.address + event.count)
    }
    assert read_addresses == set(by_address)
    assert set(capture["scan_only_addresses"]).isdisjoint(read_addresses)
    assert len(capture["scan_only_addresses"]) == 14
    assert writes == []

    diagnostics = {row["wire_address"]: row for row in report["registers"]}
    assert set(diagnostics) == set(by_address)
    assert sum(row["status"] == "device_unavailable" for row in diagnostics.values()) == 10
    for address, field, raw, expected in rows:
        component, name = field.split(".", 1)
        actual = getattr(getattr(api, component), name)
        if expected is None or isinstance(expected, bool):
            assert actual is expected, field
        else:
            assert actual == pytest.approx(expected), field
        diagnostic = diagnostics[address]
        assert diagnostic["documented_reference"] == address + 30001, field
        assert diagnostic["field"] == field
        assert diagnostic["raw_u16"] == raw
        assert diagnostic["status"] == ("device_unavailable" if expected is None else "ok")

    # Explicit capture examples guard the wire offset, signed decoding, and scale.
    assert by_address[6020] == ("system_values.brine_inlet_temperature", 2370, 23.7)
    assert by_address[6105] == ("system_values.supercooling", 65201, -3.35)
    assert by_address[6114] == ("system_values.l1_l2_voltage", 0, 0.0)
    assert by_address[7505] == ("system_state.control_signal_brine_pump", 1, True)
    assert by_address[9046] == ("alarms.level_3_notification_heating_circuit_2_temperature", 1, True)
