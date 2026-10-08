#!/usr/bin/env python3
"""Run bounded WPM library polls without changing a Home Assistant installation."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from importlib.metadata import version
from pathlib import Path

from modbus_connection import ModbusTcpParams, ModbusUnit

import pystiebeleltron._read_retry as retry_module
from pystiebeleltron.wpm import WpmStiebelEltronAPI
from pystiebeleltron.wpm3 import Wpm3StiebelEltronAPI
from pystiebeleltron.wpm3i import Wpm3iStiebelEltronAPI


class ReadOnlyUnit:
    """Expose only FC03/FC04; reject every other operation before forwarding."""

    def __init__(self, unit: ModbusUnit) -> None:
        self._unit = unit

    def __getattr__(self, name: str):
        raise RuntimeError("The probe permits only input and holding register reads")

    async def read_input_registers(self, address: int, count: int) -> list[int]:
        return await self._read("input", address, count)

    async def read_holding_registers(self, address: int, count: int) -> list[int]:
        return await self._read("holding", address, count)

    async def _read(self, space: str, address: int, count: int) -> list[int]:
        event = {"space": space, "address": address, "count": count}
        try:
            values = await getattr(self._unit, f"read_{space}_registers")(address, count)
        except Exception as error:
            print(json.dumps({**event, "result": type(error).__name__}), flush=True)
            raise
        print(json.dumps({**event, "result": "OK"}), flush=True)
        return values


async def run_probe(unit: ModbusUnit, family: str, polls: int = 1, raw: bool = False) -> None:
    """Read at most three polls; never log raw values, host addresses or device IDs."""
    if polls not in (1, 2, 3):
        raise ValueError("Select one to three polls")
    api_class = {"wpm": WpmStiebelEltronAPI, "wpm3": Wpm3StiebelEltronAPI, "wpm3i": Wpm3iStiebelEltronAPI}[family]
    api = api_class(ReadOnlyUnit(unit))
    for poll in range(polls):
        await asyncio.wait_for(api.async_read_raw() if raw else api.async_update(), timeout=90)
        print(json.dumps({"poll": poll + 1, "result": "OK"}), flush=True)


async def main(args: argparse.Namespace) -> None:
    from modbus_connection.tmodbus import ModbusConnection

    fingerprint = hashlib.sha256(Path(retry_module.__file__).read_bytes()).hexdigest()
    print(json.dumps({"library": version("pystiebeleltron"), "backend": version("modbus-connection"), "retry_sha256": fingerprint}), flush=True)
    connection = ModbusConnection(ModbusTcpParams(host=args.host, port=args.port))
    try:
        await run_probe(connection.for_unit(args.unit), args.family, args.polls, args.raw)
    finally:
        await connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", help="ISG host, kept out of the output")
    parser.add_argument("--family", choices=("wpm", "wpm3", "wpm3i"), required=True)
    parser.add_argument("--port", type=int, default=502)
    parser.add_argument("--unit", type=int, default=1)
    parser.add_argument("--polls", type=int, choices=(1, 2, 3), default=1)
    parser.add_argument("--raw", action="store_true", help="Exercise the raw API without printing register values")
    parser.add_argument("--confirm-read-only", action="store_true", required=True, help="Explicitly confirm the read-only device test")
    args = parser.parse_args()
    try:
        asyncio.run(main(args))
    except Exception as error:
        print(json.dumps({"result": "FAILED", "error": type(error).__name__}), flush=True)
        raise SystemExit(1) from None
