"""Generate the model-based Stiebel Eltron heat pump modules from the CSV maps.

Each register block in ``api/*.csv`` becomes a ``modbus_connection.model``
``Component`` of typed fields; a controller groups its components behind one
``ComponentGroup``. Contiguous repeated sub-units (a WPM's heat-pump modules and
per-circuit room temperatures) are emitted as ``repeating_group`` sub-components.
The module text is rendered from ``scripts/templates/module.py.j2``. Run from the
repo root: ``python scripts/generate.py``.
"""

from __future__ import annotations

import csv
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

TEMPLATES = Path(__file__).parent / "templates"


@dataclass
class Columns:
    """Indices of the CSV columns we read, which differ between WPM and LWZ exports."""

    name_col: int
    min_col: int
    max_col: int
    data_type_col: int
    unit_col: int
    writable_col: int
    suffix_col: int


WPM_COLUMNS = Columns(name_col=1, min_col=6, max_col=7, data_type_col=8, unit_col=9, writable_col=10, suffix_col=11)
LWZ_COLUMNS = Columns(name_col=1, min_col=5, max_col=6, data_type_col=7, unit_col=8, writable_col=9, suffix_col=10)


@dataclass
class Repeat:
    """A contiguous run of identical sub-units sharing a numbered suffix.

    Rows whose suffix is ``prefix`` followed by an index (``HP1`` .. ``HP6``) become
    one ``component_class`` sub-component, exposed on the parent as a list attribute.
    """

    prefix: str  # suffix stem before the index, e.g. "HP" or "ROOM TEMP HC"
    attr: str  # the parent list attribute, e.g. "heat_pumps"
    class_suffix: str  # the sub-component class suffix, e.g. "HeatPumpModule"
    stride: int  # registers per instance (the address step between instances)


@dataclass
class Block:
    """One register block: a CSV file mapped to a Component."""

    name: str  # e.g. "System Values"
    path: str  # relative to api/
    space: str  # "input" or "holding"
    energy: bool = False  # apply the LOW/HI + day-and-total energy handling
    repeats: list[Repeat] = field(default_factory=list)  # sub-units to fold out


@dataclass
class Controller:
    """A controller's component layout plus per-type extras.

    ``type`` is the class prefix and module stem ("Wpm" / "Lwz"); an LWZ is a
    Luft-Wärme-Zentrale (a ventilation/heat central), not only a heat pump.
    """

    type: str  # "Wpm" / "Lwz"
    columns: Columns
    blocks: list[Block]
    operating_mode: bool = False  # emit the OperatingMode enum + helpers (LWZ)
    compressor_starts: bool = False  # emit the combined compressor_starts (LWZ)


WPM = Controller(
    type="Wpm",
    columns=WPM_COLUMNS,
    blocks=[
        Block(
            "System Values",
            "wpm_system_values.csv",
            "input",
            repeats=[
                Repeat("HP", "heat_pumps", "HeatPumpModule", stride=7),
                Repeat("ROOM TEMP HC", "room_temperatures", "RoomTemperature", stride=4),
                Repeat("ROOM TEMP COOLING", "room_temperatures_cooling", "RoomTemperatureCooling", stride=1),
            ],
        ),
        Block("System Parameters", "wpm_system_parameters.csv", "holding"),
        Block("System State", "wpm_system_state.csv", "input"),
        Block("Energy Data", "wpm_energy_data.csv", "input", energy=True),
        Block("Power Consumption", "wpm_power_consumption.csv", "input"),
    ],
)

LWZ = Controller(
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

# The two shared components from pystiebeleltron/__init__.py, as (low, high) wire
# address ranges, so they join their space's device-wide ranges.
SHARED_INPUT_RANGE = (5000, 5001)  # EnergySystemInformation
SHARED_HOLDING_RANGE = (4000, 4002)  # EnergyManagementSettings


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


def _number(text: str) -> float | int | None:
    """Parse a CSV min/max cell into a number, or None when blank."""
    text = text.strip()
    if not text:
        return None
    value = float(text)
    return int(value) if value.is_integer() else value


def _field_factory(row: list[str], cols: Columns, *, writable: bool) -> str:
    """Render the field factory call for one register row."""
    name, data_type, unit = row[cols.name_col], row[cols.data_type_col], row[cols.unit_col]
    unit_arg = f', unit="{unit}"' if unit else ""
    if writable:
        low, high = _number(row[cols.min_col]), _number(row[cols.max_col])
        writable_arg = f", writable=in_range({low}, {high})" if low is not None and high is not None else ", writable=True"
    else:
        writable_arg = ""
    wire = int(row[0]) - 1
    if data_type == "2":
        return f"gauge({wire}, 0.1, nan=UNAVAILABLE{unit_arg}{writable_arg})"
    if data_type == "7":
        return f"gauge({wire}, 0.01, nan=UNAVAILABLE{unit_arg}{writable_arg})"
    if data_type in ("6", "8"):
        return f"integer({wire}, signed=False, nan=UNAVAILABLE{unit_arg}{writable_arg})"
    raise ValueError(f"unhandled data type {data_type!r} for {name!r}")


@dataclass
class SubComponent:
    """A repeated sub-unit rendered as its own Component class."""

    class_name: str
    register_space: str
    fields: list[str] = field(default_factory=list)


@dataclass
class Component:
    """A rendered component: field/repeat/property source plus energy metadata."""

    class_name: str
    member: str  # the API attribute holding this component
    register_space: str
    ranges_const: str = ""
    low: int = 0  # first wire address the block covers
    high: int = 0  # last wire address the block covers
    fields: list[str] = field(default_factory=list)  # "attr = factory(...)"
    repeats: list[str] = field(default_factory=list)  # "attr = repeating_group(...)"
    compressor_starts: bool = False
    day_and_total: list[tuple[str, str, str]] = field(default_factory=list)


def _read_rows(api_path: Path, block: Block) -> list[list[str]]:
    with (api_path / block.path).open() as handle:
        return list(csv.reader(handle))[1:]


def _span(rows: list[list[str]]) -> tuple[int, int]:
    """The block's (low, high) wire address range, covering every row read."""
    addresses = [int(row[0]) - 1 for row in rows]
    return min(addresses), max(addresses)


def _match_repeat(suffix: str, repeats: list[Repeat]) -> tuple[Repeat, int] | None:
    """Return the repeat a row's suffix belongs to (with its index), if any."""
    suffix = suffix.strip()
    for repeat in repeats:
        match = re.fullmatch(re.escape(repeat.prefix) + r"\s*(\d+)", suffix)
        if match:
            return repeat, int(match.group(1))
    return None


def _repeating_sub_component(repeat: Repeat, by_index: dict[int, list[list[str]]], controller: Controller, space: str) -> tuple[SubComponent, str]:
    """Build the sub-component class and the parent's ``repeating_group`` line."""
    indices = sorted(by_index)
    if indices != list(range(indices[0], indices[0] + len(indices))):
        raise ValueError(f"{repeat.prefix!r} instances are not consecutive: {indices}")
    instance_zero = sorted(by_index[indices[0]], key=lambda row: int(row[0]))
    base = int(instance_zero[0][0]) - 1
    # Every later instance must sit a whole ``stride`` past the first.
    for offset, index in enumerate(indices):
        start = min(int(row[0]) - 1 for row in by_index[index])
        if start != base + offset * repeat.stride:
            raise ValueError(f"{repeat.prefix}{index} starts at {start}, expected stride {repeat.stride}")

    sub_class = f"{controller.type}{repeat.class_suffix}"
    sub = SubComponent(sub_class, space)
    seen: set[str] = set()
    for row in instance_zero:
        attribute = attr(row[controller.columns.name_col])
        if attribute in seen:
            raise ValueError(f"duplicate attribute {attribute!r} in {sub_class}")
        seen.add(attribute)
        sub.fields.append(f"{attribute} = {_field_factory(row, controller.columns, writable=False)}")
    line = f"{repeat.attr} = repeating_group({len(indices)}, {sub_class}, stride={repeat.stride})"
    return sub, line


def _plain_component(block: Block, rows: list[list[str]], controller: Controller) -> tuple[Component, list[SubComponent]]:
    cols = controller.columns
    low, high = _span(rows)
    component = Component(
        f"{controller.type}{class_name(block.name)}",
        field_attr(block.name),
        block.space,
        low=low,
        high=high,
    )
    groups: dict[str, dict[int, list[list[str]]]] = {repeat.attr: {} for repeat in block.repeats}
    seen: set[str] = set()
    for row in rows:
        hit = _match_repeat(row[cols.suffix_col], block.repeats)
        if hit is not None:
            repeat, index = hit
            groups[repeat.attr].setdefault(index, []).append(row)
            continue
        attribute = attr(row[cols.name_col], row[cols.suffix_col])
        if attribute in seen:
            raise ValueError(f"duplicate attribute {attribute!r} in {block.name}")
        seen.add(attribute)
        writable = "w" in row[cols.writable_col]
        component.fields.append(f"{attribute} = {_field_factory(row, cols, writable=writable)}")

    sub_components: list[SubComponent] = []
    for repeat in block.repeats:
        sub, line = _repeating_sub_component(repeat, groups[repeat.attr], controller, block.space)
        sub_components.append(sub)
        component.repeats.append(line)

    component.compressor_starts = controller.compressor_starts and block.name == "System Values"
    return component, sub_components


def _energy_component(block: Block, rows: list[list[str]], controller: Controller) -> Component:
    """Energy block: LOW/HI pairs combine in a scaled_sum; DAY rows gain a running total."""
    cols = controller.columns
    low, high = _span(rows)
    component = Component(
        f"{controller.type}{class_name(block.name)}",
        field_attr(block.name),
        block.space,
        low=low,
        high=high,
    )
    seen: set[str] = set()

    def add(attribute: str, source: str) -> None:
        if attribute in seen:
            raise ValueError(f"duplicate attribute {attribute!r} in {block.name}")
        seen.add(attribute)
        component.fields.append(f"{attribute} = {source}")

    for index, row in enumerate(rows):
        name, suffix = row[cols.name_col], row[cols.suffix_col]
        wire, unit = int(row[0]) - 1, row[cols.unit_col]
        if suffix[:2] == "HI":
            continue  # consumed by the preceding LOW row's scaled_sum
        if suffix[:3] == "LOW":
            # kWh (LOW) + MWh (HI) summed into a single counter, in kWh.
            add(attr(name, suffix[3:].strip()), f'scaled_sum({wire}, (1, 1000), unit="{unit}")')
            continue
        add(attr(name, suffix), _field_factory(row, cols, writable=False))
        if name[-3:] == "DAY":
            following = rows[index + 1]
            total = attr(following[cols.name_col], following[cols.suffix_col][3:].strip())
            running = attr(name + "_AND_TOTAL", suffix)
            component.day_and_total.append((attr(name, suffix), total, running))
    return component


def _ranges_const(controller: Controller, space: str) -> str:
    """The module-level range-constant name for a controller's register space."""
    return f"{controller.type.upper()}_{space.upper()}_RANGES"


def _ranges_by_space(components: list[Component]) -> dict[str, tuple[tuple[int, int], ...]]:
    """The device-wide readable ranges per space (block spans plus the shared blocks)."""
    shared = {"input": SHARED_INPUT_RANGE, "holding": SHARED_HOLDING_RANGE}
    spans: dict[str, set[tuple[int, int]]] = {}
    for component in components:
        spans.setdefault(component.register_space, set()).add((component.low, component.high))
    for space, ranges in spans.items():
        ranges.add(shared[space])
    return {space: tuple(sorted(ranges)) for space, ranges in spans.items()}


def _imports(controller: Controller, components: list[Component]) -> list[str]:
    """The import lines the rendered module needs, given what it uses."""
    model = ["Component", "ComponentGroup", "gauge", "integer"]
    if any(component.repeats for component in components):
        model.append("repeating_group")
    local = ["EnergyManagementSettings", "EnergySystemInformation", "UNAVAILABLE"]
    if any(block.energy for block in controller.blocks):
        local.append("scaled_sum")
    if any("in_range(" in line for component in components for line in component.fields):
        local.append("in_range")

    lines = []
    if controller.operating_mode:
        lines += ["from enum import Enum", ""]
    lines.append("from modbus_connection import ModbusUnit")
    lines.append(f"from modbus_connection.model import {', '.join(sorted(model))}")
    lines.append("")
    lines.append(f"from . import {', '.join(sorted(local))}")
    return lines


def build(controller: Controller, root: Path) -> dict[str, object]:
    """Assemble the render context for a controller module."""
    api_path = root / "api"
    components: list[Component] = []
    sub_components: list[SubComponent] = []
    for block in controller.blocks:
        rows = _read_rows(api_path, block)
        if block.energy:
            components.append(_energy_component(block, rows, controller))
        else:
            component, subs = _plain_component(block, rows, controller)
            components.append(component)
            sub_components += subs

    ranges = _ranges_by_space(components)
    for component in components:
        component.ranges_const = _ranges_const(controller, component.register_space)

    return {
        "imports": _imports(controller, components),
        "range_lines": [f"{_ranges_const(controller, space)} = {ranges[space]!r}" for space in sorted(ranges)],
        "operating_mode": controller.operating_mode,
        "lwz_helpers": controller.operating_mode,
        "sub_components": sub_components,
        "components": components,
        "api_class": f"{controller.type}StiebelEltronAPI",
        "members": [(component.member, component.class_name) for component in components],
        "holding_ranges_const": _ranges_const(controller, "holding"),
        "input_ranges_const": _ranges_const(controller, "input"),
    }


def generate(controller: Controller, root: Path, env: Environment) -> None:
    """Render and write a controller module."""
    output = env.get_template("module.py.j2").render(**build(controller, root))
    (root / f"pystiebeleltron/{controller.type.lower()}.py").write_text(output)


def main() -> None:
    """Generate every controller module, then format it with ruff."""
    root = Path.cwd()
    env = Environment(loader=FileSystemLoader(TEMPLATES), trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
    paths = []
    for controller in (WPM, LWZ):
        generate(controller, root, env)
        paths.append(str(root / f"pystiebeleltron/{controller.type.lower()}.py"))
    subprocess.run(["ruff", "format", *paths], check=True)
    subprocess.run(["ruff", "check", "--fix", "--quiet", *paths], check=True)
    print("Done!")


if __name__ == "__main__":
    main()
