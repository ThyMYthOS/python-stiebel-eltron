"""Generate the model-based Stiebel Eltron heat pump modules from the CSV maps.

Each register block in ``api/*.csv`` becomes a ``modbus_connection.model``
``Component`` of typed fields; a heat pump groups its components behind one
``ComponentGroup``. Run from the repo root: ``python scripts/generate.py``.
"""

from __future__ import annotations

import csv
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# Raw register value the ISG returns for an unavailable object (matches
# pystiebeleltron.UNAVAILABLE); emitted as the field ``nan`` sentinel.
UNAVAILABLE = 0x8000


@dataclass
class Columns:
    """CSV column indices, which differ between the WPM and LWZ exports."""

    name: int
    data_type: int
    unit: int
    writable: int
    suffix: int


WPM_COLUMNS = Columns(name=1, data_type=8, unit=9, writable=10, suffix=11)
LWZ_COLUMNS = Columns(name=1, data_type=7, unit=8, writable=9, suffix=10)


@dataclass
class Block:
    """One register block: a CSV file mapped to a Component."""

    name: str  # e.g. "System Values"
    path: str  # relative to api/
    space: str  # "input" or "holding"
    energy: bool = False  # apply the LOW/HI + day-and-total energy handling


@dataclass
class HeatPump:
    """A heat pump's component layout plus per-type extras."""

    type: str  # "Wpm" / "Lwz"
    columns: Columns
    blocks: list[Block]
    operating_mode: bool = False  # emit the OperatingMode enum + helpers (LWZ)
    compressor_starts: bool = False  # emit the combined compressor_starts (LWZ)
    extra_imports: list[str] = field(default_factory=list)


WPM = HeatPump(
    type="Wpm",
    columns=WPM_COLUMNS,
    blocks=[
        Block("System Values", "wpm_system_values.csv", "input"),
        Block("System Parameters", "wpm_system_parameters.csv", "holding"),
        Block("System State", "wpm_system_state.csv", "input"),
        Block("Energy Data", "wpm_energy_data.csv", "input", energy=True),
        Block("Power Consumption", "wpm_power_consumption.csv", "input"),
    ],
)

LWZ = HeatPump(
    type="Lwz",
    columns=LWZ_COLUMNS,
    blocks=[
        Block("System Values", "lwz_system_values.csv", "input"),
        Block("System Parameters", "lwz_system_parameters.csv", "holding"),
        Block("System State", "lwz_system_state.csv", "input"),
        Block("Energy Data", "lwz_energy_data.csv", "input", energy=True),
    ],
    operating_mode=True,
    compressor_starts=True,
)


def python_name(name: str, suffix: str = "") -> str:
    """A register's enum/attribute stem, suffix-disambiguated (pre-lowercasing)."""
    result = name.strip() if suffix == "" else name + "_" + suffix.strip()
    return result.replace(" ", "_")


def attr(name: str, suffix: str = "") -> str:
    """The snake_case attribute name for a register."""
    return python_name(name, suffix).lower()


def class_name(block_name: str) -> str:
    """The Component subclass suffix for a block (e.g. 'System Values' -> 'SystemValues')."""
    return block_name.replace(" ", "")


def field_attr(block_name: str) -> str:
    """The API attribute holding a block's component (e.g. 'system_values')."""
    return block_name.lower().replace(" ", "_")


def _field_line(name: str, data_type: str, wire: int, unit: str, writable: bool) -> str:
    """Render a field assignment for one register row."""
    unit_arg = f', unit="{unit}"' if unit else ""
    writable_arg = ", writable=True" if writable else ""
    if data_type == "2":
        return f"gauge({wire}, 0.1, nan=UNAVAILABLE{unit_arg}{writable_arg})"
    if data_type == "7":
        return f"gauge({wire}, 0.01, nan=UNAVAILABLE{unit_arg}{writable_arg})"
    if data_type in ("6", "8"):
        return f"integer({wire}, signed=False, nan=UNAVAILABLE{unit_arg}{writable_arg})"
    raise ValueError(f"unhandled data type {data_type!r} for {name!r}")


# The two shared components from pystiebeleltron/__init__.py, as (low, high) wire
# address ranges, so they join their space's device-wide ranges.
SHARED_INPUT_RANGE = (5000, 5001)  # EnergySystemInformation
SHARED_HOLDING_RANGE = (4000, 4002)  # EnergyManagementSettings


@dataclass
class Component:
    """A rendered component: field/property source lines plus energy metadata."""

    block_name: str  # e.g. "System Values"
    class_suffix: str  # e.g. "SystemValues"
    space: str
    low: int = 0  # first wire address the block covers
    high: int = 0  # last wire address the block covers
    fields: list[str] = field(default_factory=list)  # "attr = factory(...)"
    day_and_total: list[tuple[str, str, str]] = field(default_factory=list)


def _read_rows(api_path: Path, block: Block, cols: Columns) -> list[list[str]]:
    with (api_path / block.path).open() as handle:
        return list(csv.reader(handle))[1:]


def _span(rows: list[list[str]]) -> tuple[int, int]:
    """The block's (low, high) wire address range, covering every row read."""
    addresses = [int(row[0]) - 1 for row in rows]
    return min(addresses), max(addresses)


def _plain_component(block: Block, rows: list[list[str]], cols: Columns) -> Component:
    low, high = _span(rows)
    component = Component(block.name, class_name(block.name), block.space, low, high)
    seen: set[str] = set()
    for row in rows:
        name, suffix = row[cols.name], row[cols.suffix]
        wire = int(row[0]) - 1
        attribute = attr(name, suffix)
        if attribute in seen:
            raise ValueError(f"duplicate attribute {attribute!r} in {block.name}")
        seen.add(attribute)
        factory = _field_line(name, row[cols.data_type], wire, row[cols.unit], "w" in row[cols.writable])
        component.fields.append(f"{attribute} = {factory}")
    return component


def _energy_component(block: Block, rows: list[list[str]], cols: Columns) -> Component:
    """Energy block: LOW/HI pairs combine in a @property; DAY rows gain a running total."""
    low, high = _span(rows)
    component = Component(block.name, class_name(block.name), block.space, low, high)
    seen: set[str] = set()

    def add(attribute: str, source: str) -> None:
        if attribute in seen:
            raise ValueError(f"duplicate attribute {attribute!r} in {block.name}")
        seen.add(attribute)
        component.fields.append(f"{attribute} = {source}")

    for index, row in enumerate(rows):
        name, suffix = row[cols.name], row[cols.suffix]
        wire, unit = int(row[0]) - 1, row[cols.unit]
        if suffix[:2] == "HI":
            continue  # consumed by the preceding LOW row's scaled_sum
        if suffix[:3] == "LOW":
            # kWh (LOW) + MWh (HI) summed into a single counter, in kWh.
            add(attr(name, suffix[3:].strip()), f'scaled_sum({wire}, (1, 1000), unit="{unit}")')
            continue
        attribute = attr(name, suffix)
        add(attribute, _field_line(name, row[cols.data_type], wire, unit, False))
        if name[-3:] == "DAY":
            following = rows[index + 1]
            total = attr(following[cols.name], following[cols.suffix][3:].strip())
            running = attr(name + "_AND_TOTAL", suffix)
            component.day_and_total.append((attribute, total, running))
    return component


def _ranges_const(heatpump: HeatPump, space: str) -> str:
    """The module-level range-constant name for a heat pump's register space."""
    return f"{heatpump.type.upper()}_{space.upper()}_RANGES"


def _ranges_by_space(components: list[Component]) -> dict[str, tuple[tuple[int, int], ...]]:
    """The device-wide readable ranges per space (block spans plus the shared blocks)."""
    shared = {"input": SHARED_INPUT_RANGE, "holding": SHARED_HOLDING_RANGE}
    spans: dict[str, set[tuple[int, int]]] = {}
    for component in components:
        spans.setdefault(component.space, set()).add((component.low, component.high))
    for space, ranges in spans.items():
        ranges.add(shared[space])
    return {space: tuple(sorted(ranges)) for space, ranges in spans.items()}


def _render_component(component: Component, heatpump: HeatPump) -> str:
    lines = [
        f"class {heatpump.type}{component.class_suffix}(Component):",
        f'    register_space = "{component.space}"',
        f"    register_ranges = {_ranges_const(heatpump, component.space)}",
        "",
    ]
    lines += [f"    {line}" for line in component.fields]

    if heatpump.compressor_starts and component.class_suffix == "SystemValues":
        lines += [
            "",
            "    @property",
            "    def compressor_starts(self) -> int | None:",
            '        """Total compressor starts, combined from the HI/LOW registers."""',
            "        high = self.compressor_starts_hi",
            "        if high is None:",
            "            return None",
            "        low = self.compressor_starts_low",
            "        return high * 1000 + (low or 0)",
        ]

    if component.day_and_total:
        pairs = ",\n".join(f"        ({day!r}, {total!r}, {running!r})" for day, total, running in component.day_and_total)
        lines += [
            "",
            "    _DAY_AND_TOTAL = (",
            pairs + ",",
            "    )",
            "",
            "    def __init__(self, unit: ModbusUnit, index: int = 1) -> None:",
            "        super().__init__(unit, index)",
            "        self._running_totals: dict[str, int] = {}",
            "",
            "    def notify(self) -> None:",
            '        """Refresh the monotonic day-and-total counters, then notify listeners."""',
            "        for day_attr, total_attr, key in self._DAY_AND_TOTAL:",
            "            day = getattr(self, day_attr)",
            "            total = getattr(self, total_attr)",
            "            if day is not None and total is not None:",
            "                combined = day + total",
            "                previous = self._running_totals.get(key)",
            "                self._running_totals[key] = combined if previous is None else max(combined, previous)",
            "        super().notify()",
        ]
        for _day, _total, running in component.day_and_total:
            lines += [
                "",
                "    @property",
                f"    def {running}(self) -> int | None:",
                f"        return self._running_totals.get({running!r})",
            ]
    return "\n".join(lines)


def _render_api(heatpump: HeatPump, components: list[Component]) -> str:
    lines = [f"class {heatpump.type}StiebelEltronAPI:", '    """Stiebel Eltron heat pump API over a modbus_connection ModbusUnit."""', "", "    def __init__(self, unit: ModbusUnit) -> None:"]
    members: list[str] = []
    for component in components:
        member = field_attr(component.block_name)
        members.append(member)
        lines.append(f"        self.{member} = {heatpump.type}{component.class_suffix}(unit)")
    holding, inputs = _ranges_const(heatpump, "holding"), _ranges_const(heatpump, "input")
    lines.append("        self.energy_management_settings = EnergyManagementSettings(unit)")
    lines.append(f"        self.energy_management_settings.register_ranges = {holding}")
    lines.append("        self.energy_system_information = EnergySystemInformation(unit)")
    lines.append(f"        self.energy_system_information.register_ranges = {inputs}")
    members += ["energy_management_settings", "energy_system_information"]
    lines.append("        self._group = ComponentGroup(")
    lines.append("            unit,")
    lines.append("            [")
    lines += [f"                self.{member}," for member in members]
    lines.append("            ],")
    lines.append("        )")
    lines += [
        "",
        "    async def async_update(self) -> None:",
        '        """Read every component in one pooled set of block reads."""',
        "        await self._group.async_update()",
    ]
    if heatpump.operating_mode:
        lines += _LWZ_HELPERS.splitlines()
    return "\n".join(lines)


# Convenience accessors carried over from the hand-written LWZ API.
_LWZ_HELPERS = '''
    def get_current_temp(self) -> float | None:
        """Get the current room temperature."""
        return self.system_values.actual_room_t_hc1

    def get_target_temp(self) -> float | None:
        """Get the target room temperature."""
        return self.system_parameters.room_temperature_day_hk1

    async def set_target_temp(self, temp: float) -> None:
        """Set the target room temperature (day)(HC1)."""
        await self.system_parameters.write("room_temperature_day_hk1", temp)

    def get_current_humidity(self) -> float | None:
        """Get the current room humidity."""
        return self.system_values.relative_humidity_hc1

    def get_operation(self) -> OperatingMode:
        """Return the current mode of operation."""
        op_mode = self.system_parameters.operating_mode
        if op_mode is None:
            return OperatingMode.EMERGENCY_OPERATION
        return OperatingMode(int(op_mode))

    async def set_operation(self, mode: OperatingMode) -> None:
        """Set the operation mode."""
        await self.system_parameters.write("operating_mode", mode.value)

    def get_heating_status(self) -> bool:
        """Return heater status."""
        value = self.system_state.operating_status
        if value is None:
            return False
        return bool(int(value) & (1 << 2))

    def get_cooling_status(self) -> bool:
        """Cooling status."""
        value = self.system_state.operating_status
        if value is None:
            return False
        return bool(int(value) & (1 << 3))

    def get_filter_alarm_status(self) -> bool:
        """Return filter alarm."""
        value = self.system_state.operating_status
        if value is None:
            return False
        filter_mask = (1 << 8) | (1 << 12) | (1 << 13)
        return bool(int(value) & filter_mask)'''


_OPERATING_MODE = '''class OperatingMode(Enum):
    """Enum for the operation mode of the heat pump."""

    AUTOMATIC = 11  # AUTOMATIK
    STANDBY = 1  # BEREITSCHAFT
    DAY_MODE = 3  # TAGBETRIEB
    SETBACK_MODE = 4  # ABSENKBETRIEB
    DHW = 5  # WARMWASSER
    MANUAL_MODE = 14  # HANDBETRIEB
    EMERGENCY_OPERATION = 0  # NOTBETRIEB'''


def generate(heatpump: HeatPump, root: Path) -> None:
    """Render and write a heat pump module."""
    api_path = root / "api"
    components: list[Component] = []
    for block in heatpump.blocks:
        rows = _read_rows(api_path, block, heatpump.columns)
        if block.energy:
            component = _energy_component(block, rows, heatpump.columns)
        else:
            component = _plain_component(block, rows, heatpump.columns)
        components.append(component)

    header = [
        '"""Modbus api for stiebel eltron heat pumps. This file is generated. Do not modify it manually."""',
        "",
        "from __future__ import annotations",
        "",
    ]
    if heatpump.operating_mode:
        header.append("from enum import Enum")
        header.append("")
    header += [
        "from modbus_connection import ModbusUnit",
        "from modbus_connection.model import Component, ComponentGroup, gauge, integer",
        "",
        "from . import UNAVAILABLE, EnergyManagementSettings, EnergySystemInformation, scaled_sum",
    ]

    ranges = _ranges_by_space(components)
    range_lines = [f"{_ranges_const(heatpump, space)} = {ranges[space]!r}" for space in sorted(ranges)]

    sections = ["\n".join(header), "\n".join(range_lines)]
    if heatpump.operating_mode:
        sections.append(_OPERATING_MODE)
    sections += [_render_component(component, heatpump) for component in components]
    sections.append(_render_api(heatpump, components))

    output = "\n\n\n".join(sections) + "\n"
    (root / f"pystiebeleltron/{heatpump.type.lower()}.py").write_text(output)


def main() -> None:
    """Generate every heat pump module, then format it with ruff."""
    root = Path.cwd()
    paths = []
    for heatpump in (WPM, LWZ):
        generate(heatpump, root)
        paths.append(str(root / f"pystiebeleltron/{heatpump.type.lower()}.py"))
    subprocess.run(["ruff", "format", *paths], check=True)
    subprocess.run(["ruff", "check", "--fix", "--quiet", *paths], check=True)
    print("Done!")


if __name__ == "__main__":
    main()
