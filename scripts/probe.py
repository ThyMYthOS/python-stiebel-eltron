#!/usr/bin/env python3
"""Probe which registers a Stiebel Eltron ISG answers and save a shareable report.

Runs one poll of the detected (or given) controller family, then reads every
address of the chosen register maps on its own, and writes the raw outcome of
each request to a JSON file: the words, the Modbus exception code, or the
unavailable marker. Only input and holding registers are read; nothing is
written. The report contains no host address. Check it before sharing.

    python scripts/probe.py 192.168.1.20
    python scripts/probe.py 192.168.1.20 --maps lwz wpm --output lwz-r290.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from modbus_connection import ModbusError
from modbus_connection.cli_helper import add_connection_args, connect_from_args

from pystiebeleltron import ControllerModel, StiebelEltronModbusError, UnknownControllerModelError, get_controller_model
from pystiebeleltron.probe import REGISTER_MAPS, ProbeLimits, probe

_CONNECTIONS = (("tcp", "socket"), ("tcp", "rtu"), ("serial", "rtu"))

# Time close() gets beyond --max-duration. It waits for a reconnect the
# backend shields from cancellation, which could otherwise outlast the limit.
CLOSE_GRACE = 1.0

# The family each controller is polled with, matching how its API is chosen.
_FAMILY = {
    ControllerModel.LWZ: "lwz",
    ControllerModel.LWZ_x04_SOL: "lwz",
    ControllerModel.WPM_3: "wpm3",
    ControllerModel.WPM_3i: "wpm3i",
    ControllerModel.WPMsystem: "wpm",
    ControllerModel.LWZ_R290: "wpm",
}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    summary = __doc__.splitlines()[0] if __doc__ else "Probe a Stiebel Eltron ISG."
    parser = argparse.ArgumentParser(description=summary)
    add_connection_args(parser, connections=_CONNECTIONS)
    parser.set_defaults(baudrate=19200)
    parser.add_argument("--unit", type=int, default=1, help="Modbus unit/device id (default: 1)")
    parser.add_argument("--maps", nargs="+", choices=sorted(REGISTER_MAPS), help="register maps to read singly (default: the polled family)")
    parser.add_argument("--poll", choices=(*sorted(REGISTER_MAPS), "none"), help="family to poll once (default: detected)")
    parser.add_argument("--output", type=Path, default=Path("isg-probe-report.json"), help="report file; an existing file is never overwritten")
    parser.add_argument("--max-duration", type=float, default=ProbeLimits.max_duration, help="stop after this many seconds")
    return parser.parse_args(argv)


async def _close(connection: Any, timeout: float) -> None:
    """Close the connection, but give up waiting after ``timeout`` seconds."""
    try:
        await asyncio.wait_for(connection.close(), timeout=timeout)
    except TimeoutError:
        print("Closing the connection took too long; leaving it to exit.", file=sys.stderr)


async def _run(args: argparse.Namespace, output: object) -> int:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + args.max_duration
    try:
        connection = await asyncio.wait_for(connect_from_args(args), timeout=args.max_duration)
    except TimeoutError:
        print("Could not connect within --max-duration.", file=sys.stderr)
        return 1
    except ModbusError as err:
        print(f"Could not connect: {type(err).__name__}", file=sys.stderr)
        return 1
    try:
        unit = connection.for_unit(args.unit)
        poll = args.poll
        model = None
        if poll is None:
            try:
                model = await asyncio.wait_for(get_controller_model(unit), timeout=max(deadline - loop.time(), 0))
            except TimeoutError:
                print("No answer to the controller model read within --max-duration.", file=sys.stderr)
                return 1
            except UnknownControllerModelError as err:
                print(f"Unknown controller model {err.model_id}; pass --poll and --maps.", file=sys.stderr)
                return 1
            except StiebelEltronModbusError:
                print("Could not read the controller model; pass --poll and --maps.", file=sys.stderr)
                return 1
            poll = _FAMILY[model]
            print(f"Detected controller: {model.name}, polling as {poll}")
        poll = None if poll == "none" else poll
        maps = args.maps or ([poll] if poll else [])
        report = await probe(unit, maps, poll=poll, limits=ProbeLimits(max_duration=max(deadline - loop.time(), 0)))
    finally:
        await _close(connection, max(deadline - loop.time(), 0) + CLOSE_GRACE)

    data = {"controller_model": None if model is None else model.value, **report.as_dict()}
    json.dump(data, output, indent=2)  # type: ignore[arg-type]
    answered = sum(row["status"] == "ok" for row in report.registers)
    print(f"{report.status}: {answered}/{len(report.registers)} registers answered")
    return 0


def main() -> int:
    args = _parse_args()
    # Refuse an existing file before contacting the device.
    try:
        output = args.output.open("x", encoding="utf-8")
    except OSError:
        print(f"Cannot create {args.output}; choose a new --output path.", file=sys.stderr)
        return 1
    with output:
        code = asyncio.run(_run(args, output))
    if code:
        args.output.unlink()
    else:
        print(f"Report saved to {args.output}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
