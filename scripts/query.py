#!/usr/bin/env python3
"""Query a Stiebel Eltron ISG heat pump over Modbus and print every value.

Connects over Modbus TCP (the ISG gateway) or a serial port, detects whether it
is a WPM or LWZ controller, reads the whole device once, and dumps every
sub-system's values to the terminal. Handy for checking a real heat pump without
Home Assistant.

Connection handling comes from ``modbus_connection.cli_helper``, which uses
whichever backend is installed (tmodbus if present, otherwise pymodbus)::

    python scripts/query.py 192.168.1.20
    python scripts/query.py 192.168.1.20 --unit 1 --model lwz
    python scripts/query.py /dev/ttyUSB0 --transport serial
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time

from modbus_connection import ModbusError, ModbusUnit
from modbus_connection.cli_helper import CountingUnit, add_connection_args, connect_from_args, print_component
from modbus_connection.model import Component

from pystiebeleltron import StiebelEltronModbusError, UnknownControllerModelError, get_controller_model
from pystiebeleltron.lwz import LwzStiebelEltronAPI
from pystiebeleltron.wpm import WpmStiebelEltronAPI
from pystiebeleltron.wpm3i import Wpm3iStiebelEltronAPI

Api = WpmStiebelEltronAPI | Wpm3iStiebelEltronAPI | LwzStiebelEltronAPI

# The connections an ISG speaks: native Modbus TCP (socket framing), RTU over a
# TCP gateway, or a direct serial line — no UDP/TLS.
_CONNECTIONS = (("tcp", "socket"), ("tcp", "rtu"), ("serial", "rtu"))


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    summary = __doc__.splitlines()[0] if __doc__ else "Query a Stiebel Eltron heat pump over Modbus."
    parser = argparse.ArgumentParser(description=summary)
    add_connection_args(parser, connections=_CONNECTIONS)
    parser.set_defaults(baudrate=19200)  # the ISG serial default, not the 9600 fallback
    parser.add_argument("--unit", type=int, default=1, help="Modbus unit/device id (default: 1)")
    parser.add_argument("--model", choices=("wpm", "wpm3i", "lwz"), help="force the controller family instead of auto-detecting")
    return parser.parse_args(argv)


async def _build_api(args: argparse.Namespace, unit: ModbusUnit) -> Api:
    if args.model == "wpm":
        return WpmStiebelEltronAPI(unit)
    if args.model == "wpm3i":
        return Wpm3iStiebelEltronAPI(unit)
    if args.model == "lwz":
        return LwzStiebelEltronAPI(unit)
    model = await get_controller_model(unit)
    print(f"Detected controller: {model.name}")
    if model.name.startswith("LWZ"):
        return LwzStiebelEltronAPI(unit)
    if model.name.startswith("WPM_3i"):
        return Wpm3iStiebelEltronAPI(unit)
    return WpmStiebelEltronAPI(unit)


def _print(api: Api) -> None:
    """Dump every component; print_component indents the repeating groups itself."""
    for attr, component in vars(api).items():
        if not isinstance(component, Component):
            continue
        print()
        print_component(component, title=attr.replace("_", " ").capitalize())


async def _run(args: argparse.Namespace) -> int:
    try:
        connection = await connect_from_args(args)
    except ModbusError as err:
        print(f"Could not connect: {err}", file=sys.stderr)
        return 1
    counting = CountingUnit(connection.for_unit(args.unit))
    try:
        api = await _build_api(args, counting)
        counting.reads = 0  # count only the full-device query below
        start = time.monotonic()
        await api.async_update()
        elapsed = time.monotonic() - start
    except (ModbusError, StiebelEltronModbusError, UnknownControllerModelError) as err:
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
