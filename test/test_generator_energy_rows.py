"""The generator refuses an energy CSV whose counter rows are out of order."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("generate_script", Path(__file__).parents[1] / "scripts/generate.py")
assert spec is not None and spec.loader is not None
generate = importlib.util.module_from_spec(spec)
# The script's dataclasses resolve their postponed annotations through sys.modules.
sys.modules[spec.name] = generate
spec.loader.exec_module(generate)

BLOCK = generate.Block("Energy Data", "unused.csv", "input", energy=True)


def _row(address: int, name: str, suffix: str = "", unit: str = "kWh") -> list[str]:
    """A WPM energy row: documentation address, name, blanks, type 6, unit, read-only, suffix."""
    return [str(address), name, "x", "x", "x", "", "0", "65535", "6", unit, "r", suffix]


def test_day_low_and_hi_rows_in_order_build_a_counter() -> None:
    rows = [_row(3501, "VD HEATING DAY"), _row(3502, "VD HEATING TOTAL", "LOW"), _row(3503, "VD HEATING TOTAL", "HI", "MWh")]

    component = generate._energy_component(BLOCK, rows, generate.WPM)

    assert component.fields == ['vd_heating_day = integer(3500, signed=False, nan=UNAVAILABLE, unit="kWh")', 'vd_heating_total = scaled_sum(3501, (1, 1000), unit="kWh")']
    assert component.day_and_total == [("vd_heating_day", "vd_heating_total", "vd_heating_day_and_total")]


@pytest.mark.parametrize(
    "rows",
    [
        pytest.param([_row(3501, "VD HEATING DAY")], id="day-is-the-last-row"),
        pytest.param([_row(3501, "VD HEATING DAY"), _row(3502, "VD HEATING TOTAL", "HI", "MWh")], id="day-followed-by-hi"),
        pytest.param([_row(3501, "VD HEATING DAY"), _row(3503, "VD HEATING TOTAL", "LOW"), _row(3504, "VD HEATING TOTAL", "HI", "MWh")], id="low-not-adjacent-to-day"),
        pytest.param([_row(3502, "VD HEATING TOTAL", "LOW")], id="low-is-the-last-row"),
        pytest.param([_row(3502, "VD HEATING TOTAL", "LOW"), _row(3503, "VD DHW DAY")], id="low-followed-by-day"),
        pytest.param([_row(3502, "VD HEATING TOTAL", "LOW"), _row(3504, "VD HEATING TOTAL", "HI", "MWh")], id="hi-not-adjacent-to-low"),
    ],
)
def test_a_counter_row_without_its_neighbour_is_refused(rows: list[list[str]]) -> None:
    """Pairing by position must fail loudly rather than combine the wrong registers."""
    with pytest.raises(ValueError, match="must be followed by its"):
        generate._energy_component(BLOCK, rows, generate.WPM)
