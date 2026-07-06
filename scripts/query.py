#!/usr/bin/env python3
"""Query a Stiebel Eltron ISG heat pump over Modbus and print every value.

Connects over Modbus TCP (the ISG gateway) or a serial port, detects whether it
is a WPM or LWZ controller, reads the whole device once, and dumps every
sub-system's values to the terminal. Handy for checking a real heat pump without
Home Assistant.

The library only needs the connection *protocol*; this script picks the pymodbus
backend::

    python scripts/query.py tcp 192.168.1.20
    python scripts/query.py tcp 192.168.1.20 --unit 1
    python scripts/query.py serial /dev/ttyUSB0
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import sys
import time
from typing import cast

from modbus_connection import ModbusConnection, ModbusError, ModbusUnit
from modbus_connection.model import Component, RegisterField, RepeatingGroupField

from pystiebeleltron import StiebelEltronModbusError, get_controller_model
from pystiebeleltron.lwz import LwzStiebelEltronAPI
from pystiebeleltron.wpm import WpmStiebelEltronAPI

Api = WpmStiebelEltronAPI | LwzStiebelEltronAPI


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    summary = __doc__.splitlines()[0] if __doc__ else "Query a Stiebel Eltron heat pump over Modbus."
    parser = argparse.ArgumentParser(description=summary)
    sub = parser.add_subparsers(dest="transport", required=True)

    # Shared options available on each transport (so `--unit` can follow the host).
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--unit", type=int, default=1, help="Modbus unit/device id (default: 1)")
    common.add_argument("--model", choices=("wpm", "lwz"), help="force the controller family instead of auto-detecting")

    tcp = sub.add_parser("tcp", parents=[common], help="connect over Modbus TCP (the ISG gateway)")
    tcp.add_argument("host", help="hostname or IP of the ISG")
    tcp.add_argument("--port", type=int, default=502, help="TCP port (default: 502)")
    tcp.add_argument(
        "--framer",
        choices=("socket", "rtu"),
        default="socket",
        help="wire framing: 'socket' for native Modbus TCP (the ISG default) or 'rtu' for RTU-over-TCP gateways (default: socket)",
    )

    serial = sub.add_parser("serial", parents=[common], help="connect over a serial/USB port")
    serial.add_argument("device", help="serial device, e.g. /dev/ttyUSB0")
    serial.add_argument("--baudrate", type=int, default=19200, help="default: 19200")
    serial.add_argument("--parity", choices=("N", "E", "O"), default="N")
    serial.add_argument("--stopbits", type=int, choices=(1, 2), default=1)
    serial.add_argument("--bytesize", type=int, choices=(7, 8), default=8)

    return parser.parse_args(argv)


async def _open(args: argparse.Namespace) -> ModbusConnection:
    # Imported here so the module loads (and --help works) without a backend.
    from modbus_connection.pymodbus import connect_serial, connect_tcp

    if args.transport == "serial":
        return await connect_serial(args.device, baudrate=args.baudrate, parity=args.parity, stopbits=args.stopbits, bytesize=args.bytesize)
    return await connect_tcp(args.host, port=args.port, framer=args.framer)


class _CountingUnit:
    """Wraps a ModbusUnit to count the Modbus reads it performs."""

    def __init__(self, unit: ModbusUnit) -> None:
        self._unit = unit
        self.reads = 0

    async def read_input_registers(self, address: int, count: int) -> list[int]:
        self.reads += 1
        return await self._unit.read_input_registers(address, count)

    async def read_holding_registers(self, address: int, count: int) -> list[int]:
        self.reads += 1
        return await self._unit.read_holding_registers(address, count)

    async def read_coils(self, address: int, count: int) -> list[bool]:
        self.reads += 1
        return await self._unit.read_coils(address, count)

    def __getattr__(self, name: str) -> object:
        return getattr(self._unit, name)


async def _build_api(args: argparse.Namespace, unit: ModbusUnit) -> Api:
    if args.model == "wpm":
        return WpmStiebelEltronAPI(unit)
    if args.model == "lwz":
        return LwzStiebelEltronAPI(unit)
    model = await get_controller_model(unit)
    print(f"Detected controller: {model.name}")
    if model.name.startswith("LWZ"):
        return LwzStiebelEltronAPI(unit)
    return WpmStiebelEltronAPI(unit)


def _format(value: object) -> str:
    return "—" if value is None else str(value)


def _values(component: Component, prefix: str = "") -> list[tuple[str, str, str]]:
    """Public (name, value, unit) rows for a sub-system, alphabetically.

    Repeated sub-units (``repeating_group``) expand into one indexed row set per
    instance, e.g. ``heat_pumps[0].return_temperature``.
    """
    rows: list[tuple[str, str, str]] = []
    cls = type(component)
    for name in dir(component):
        if name.startswith("_"):
            continue
        static = inspect.getattr_static(cls, name, None)
        if isinstance(static, RepeatingGroupField):
            for index, instance in enumerate(getattr(component, name)):
                rows += _values(instance, f"{prefix}{name}[{index}].")
            continue
        # Keep register fields and derived @property values; skip everything else
        # (methods, the register_space marker, the ComponentGroup helpers).
        if not isinstance(static, (RegisterField, property)):
            continue
        unit = static.unit or "" if isinstance(static, RegisterField) else ""
        rows.append((f"{prefix}{name}", _format(getattr(component, name)), unit))
    return rows


def _components(api: Api) -> list[tuple[str, Component]]:
    """The API's sub-system components, in declaration order."""
    return [(name, value) for name, value in vars(api).items() if isinstance(value, Component)]


def _print(api: Api) -> None:
    for attr, component in _components(api):
        label = attr.replace("_", " ").capitalize()
        rows = _values(component)
        print(f"\n{label}")
        print("-" * len(label))
        width = max((len(name) for name, _, _ in rows), default=0)
        for name, value, unit in rows:
            suffix = f" {unit}" if unit and value != "—" else ""
            print(f"  {name:<{width}}  {value}{suffix}")


async def _run(args: argparse.Namespace) -> int:
    try:
        connection = await _open(args)
    except ModbusError as err:
        print(f"Could not connect: {err}", file=sys.stderr)
        return 1
    counting = _CountingUnit(connection.for_unit(args.unit))
    try:
        api = await _build_api(args, cast(ModbusUnit, counting))
        counting.reads = 0  # count only the full-device query below
        start = time.monotonic()
        await api.async_update()
        elapsed = time.monotonic() - start
    except (ModbusError, StiebelEltronModbusError) as err:
        print(f"Error reading device: {err}", file=sys.stderr)
        return 1
    finally:
        await connection.close()
    _print(api)
    print(f"\nQueried in {elapsed * 1000:.0f} ms ({counting.reads} Modbus reads)")
    return 0


def main() -> int:
    return asyncio.run(_run(_parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
