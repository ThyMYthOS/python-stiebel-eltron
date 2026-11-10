"""Every writable register validates a write before it reaches the controller."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from modbus_connection.mock import MockModbusUnit

from pystiebeleltron.lwz import LwzStiebelEltronAPI
from pystiebeleltron.wpm import WpmStiebelEltronAPI

ROOT = Path(__file__).parents[1]

spec = importlib.util.spec_from_file_location("generate_script_write_validation", ROOT / "scripts/generate.py")
assert spec is not None and spec.loader is not None
generate = importlib.util.module_from_spec(spec)
# The script's dataclasses resolve their postponed annotations through sys.modules.
sys.modules[spec.name] = generate
spec.loader.exec_module(generate)


def _row(data_type: str, low: str = "", high: str = "") -> list[str]:
    """A writable WPM row: documentation address, name, blanks, range, type, unit, w/r, suffix."""
    return ["1554", "COMFORT TEMPERATURE", "x", "", "", "", low, high, data_type, "", "w/r", "HK 4"]


@pytest.mark.parametrize(
    ("data_type", "expected"),
    [
        ("2", "in_range(-3276.7, 3276.7)"),
        ("7", "in_range(-327.67, 327.67)"),
        ("6", "whole_in_range(0, 65535)"),
        ("8", "whole_in_range(0, 65535)"),
    ],
)
def test_a_row_without_a_documented_range_is_bounded_by_its_register(data_type: str, expected: str) -> None:
    """Without a range from the manual, what the register can hold is the range."""
    assert f"writable={expected}" in generate._field_factory(_row(data_type), generate.WPM_COLUMNS, writable=True)


def test_a_documented_range_is_kept_and_a_whole_number_register_says_so() -> None:
    assert "writable=in_range(5, 30)" in generate._field_factory(_row("2", "5", "30"), generate.WPM_COLUMNS, writable=True)
    assert "writable=whole_in_range(0, 5)" in generate._field_factory(_row("8", "0", "5"), generate.WPM_COLUMNS, writable=True)
    assert "writable=whole_in_range(0, 1)" in generate._field_factory(_row("6", "0", "1"), generate.WPM_COLUMNS, writable=True)


@pytest.mark.parametrize("module", ["wpm", "wpm3", "wpm3i", "lwz"])
def test_no_generated_register_is_writable_without_a_validator(module: str) -> None:
    assert "writable=True" not in (ROOT / f"pystiebeleltron/{module}.py").read_text()


@pytest.mark.asyncio()
async def test_a_setpoint_without_a_documented_range_cannot_wrap_on_the_wire(mock_modbus_unit: MockModbusUnit) -> None:
    """The manual gives no range for heating circuit 4, so 4000 used to be written as 40000 and read back as -2553.6."""
    api = WpmStiebelEltronAPI(mock_modbus_unit)

    await api.system_parameters.write("comfort_temperature_hk_4", 22)
    assert mock_modbus_unit.holding[1553] == 220

    for value in (4000, 3276.8, -3276.8):
        with pytest.raises(ValueError, match="outside the allowed range"):
            await api.system_parameters.write("comfort_temperature_hk_4", value)
        assert mock_modbus_unit.holding[1553] == 220


@pytest.mark.asyncio()
async def test_a_whole_number_register_rejects_a_fraction(mock_modbus_unit: MockModbusUnit) -> None:
    """The field encodes with int(), so 1.9 used to be written as 1."""
    api = LwzStiebelEltronAPI(mock_modbus_unit)

    for value in (3, 3.0):
        await api.system_parameters.write("operating_mode", value)
        assert mock_modbus_unit.holding[1000] == 3

    for value in (1.9, 3.5):
        with pytest.raises(ValueError, match="is not a whole number"):
            await api.system_parameters.write("operating_mode", value)
        assert mock_modbus_unit.holding[1000] == 3


@pytest.mark.asyncio()
async def test_a_flag_rejects_a_fraction(mock_modbus_unit: MockModbusUnit) -> None:
    """0.9 lies inside the documented 0..1 and used to be written as 0."""
    api = WpmStiebelEltronAPI(mock_modbus_unit)

    await api.energy_management_settings.write("sg_ready_input_1", True)
    with pytest.raises(ValueError, match="is not a whole number"):
        await api.energy_management_settings.write("sg_ready_input_1", 0.9)
    assert mock_modbus_unit.holding[4001] == 1
