"""Read-only survey of which registers a controller answers.

Decoded values cannot tell a register the controller refuses (exception 2,
illegal data address) from one it answers with the unavailable marker 0x8000.
The probe records the raw outcome of every request instead: first the block
requests one real poll sends, then every known address read on its own, since
a refused single read does not prove the register is missing from a block and
an answered block does not prove every address in it exists.

Only FC03 and FC04 reads leave the probe; any other operation raises before it
reaches the unit. A run is bounded in requests and duration and stops after
repeated transport errors. Callers that also poll the same unit must not run a
probe at the same time.

The probe sees the unit, not the wire. A backend that repeats a request on its
own is invisible to it: the tmodbus backend of modbus_connection retries a
device busy answer (exception 6) for up to 60 seconds, so such a request
counts once against ``max_requests`` and is recorded with its final outcome
only. ``max_duration`` still bounds it.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass, field
from typing import Any, Literal

from modbus_connection import ModbusError, ModbusExceptionError, ModbusProtocolError, ModbusUnit

from . import UNAVAILABLE, __version__
from .lwz import LWZ_HOLDING_RANGES, LWZ_INPUT_RANGES, LwzStiebelEltronAPI
from .wpm import WPM_HOLDING_RANGES, WPM_INPUT_RANGES, WpmStiebelEltronAPI
from .wpm3 import WPM3_HOLDING_RANGES, WPM3_INPUT_RANGES, Wpm3StiebelEltronAPI
from .wpm3i import WPM3I_HOLDING_RANGES, WPM3I_INPUT_RANGES, Wpm3iStiebelEltronAPI

Space = Literal["input", "holding"]

REPORT_FORMAT_VERSION = 1

# Wire addresses per family, taken from the generated register maps.
REGISTER_MAPS: dict[str, dict[Space, tuple[tuple[int, int], ...]]] = {
    "lwz": {"input": LWZ_INPUT_RANGES, "holding": LWZ_HOLDING_RANGES},
    "wpm": {"input": WPM_INPUT_RANGES, "holding": WPM_HOLDING_RANGES},
    "wpm3": {"input": WPM3_INPUT_RANGES, "holding": WPM3_HOLDING_RANGES},
    "wpm3i": {"input": WPM3I_INPUT_RANGES, "holding": WPM3I_HOLDING_RANGES},
}

_POLL_APIS: dict[str, Callable[[ModbusUnit], Any]] = {
    "lwz": LwzStiebelEltronAPI,
    "wpm": WpmStiebelEltronAPI,
    "wpm3": Wpm3StiebelEltronAPI,
    "wpm3i": Wpm3iStiebelEltronAPI,
}


@dataclass(frozen=True)
class ProbeLimits:
    """Bounds of one probe run."""

    # Calls to the unit; repeats a backend makes on its own are not counted.
    max_requests: int = 1000
    max_duration: float = 600.0
    max_consecutive_transport_errors: int = 3
    # Pause between single reads, so the probe never floods the ISG.
    pause: float = 0.2


@dataclass
class ProbeReport:
    """Outcome of one probe run; ``as_dict`` is safe to share."""

    maps: list[str]
    poll: str | None
    status: str = "completed"
    poll_result: dict[str, Any] | None = None
    poll_requests: list[dict[str, Any]] = field(default_factory=list)
    registers: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        """Return the report as JSON-serialisable data without host details."""
        return {
            "format_version": REPORT_FORMAT_VERSION,
            "library": __version__,
            "maps": self.maps,
            "poll": self.poll,
            "status": self.status,
            "poll_result": self.poll_result,
            "poll_requests": self.poll_requests,
            "registers": self.registers,
        }


class _ShortResponseError(ModbusProtocolError):
    """The unit returned fewer or more words than requested."""


class ProbeStopped(Exception):
    """A limit of the run was reached; ``status`` names which one."""

    def __init__(self, status: str) -> None:
        super().__init__(status)
        self.status = status


def build_plan(maps: Iterable[str]) -> list[tuple[Space, int, list[str]]]:
    """Return every address of ``maps`` once, inputs first, tagged with its maps."""
    owners: dict[tuple[Space, int], list[str]] = {}
    for name in maps:
        for space, ranges in REGISTER_MAPS[name].items():
            for first, last in ranges:
                for address in range(first, last + 1):
                    tags = owners.setdefault((space, address), [])
                    if name not in tags:
                        tags.append(name)
    order = {"input": 0, "holding": 1}
    return [(space, address, owners[(space, address)]) for space, address in sorted(owners, key=lambda key: (order[key[0]], key[1]))]


def _outcome(words: list[int]) -> dict[str, Any]:
    outcome: dict[str, Any] = {"status": "ok", "words": list(words)}
    unavailable = [offset for offset, word in enumerate(words) if word == UNAVAILABLE]
    if unavailable:
        outcome["unavailable_offsets"] = unavailable
    return outcome


def _failure(err: ModbusError) -> dict[str, Any]:
    """Keep the exception code or error type; never the message, which may name the host."""
    if isinstance(err, _ShortResponseError):
        return {"status": "invalid_response"}
    if isinstance(err, ModbusExceptionError):
        code = err.exception_code
        return {"status": "exception", "exception_code": None if code is None else int(code)}
    return {"status": "transport_error", "error_type": type(err).__name__}


class _ProbeUnit:
    """Forward FC03/FC04 reads within the run's limits and record each outcome."""

    def __init__(
        self,
        unit: ModbusUnit,
        limits: ProbeLimits,
        clock: Callable[[], float],
    ) -> None:
        self._unit = unit
        self._limits = limits
        self._clock = clock
        self._deadline = clock() + limits.max_duration
        self._requests = 0
        self._transport_errors = 0
        self.log: list[dict[str, Any]] = []

    def remaining(self) -> float:
        """Seconds left before the run's deadline."""
        return max(self._deadline - self._clock(), 0.0)

    def __getattr__(self, name: str) -> Any:
        raise AttributeError(f"The probe only reads input and holding registers, not {name}")

    async def read_input_registers(self, address: int, count: int) -> list[int]:
        return await self._read("input", self._unit.read_input_registers, address, count)

    async def read_holding_registers(self, address: int, count: int) -> list[int]:
        return await self._read("holding", self._unit.read_holding_registers, address, count)

    async def _read(self, space: Space, read: Callable[[int, int], Awaitable[list[int]]], address: int, count: int) -> list[int]:
        if self._transport_errors >= self._limits.max_consecutive_transport_errors:
            raise ProbeStopped("stopped_after_transport_errors")
        if self._requests >= self._limits.max_requests:
            raise ProbeStopped("stopped_at_request_limit")
        if self._clock() >= self._deadline:
            raise ProbeStopped("stopped_at_time_limit")
        self._requests += 1
        entry: dict[str, Any] = {"space": space, "address": address, "count": count}
        self.log.append(entry)
        try:
            # A read the backend would let run past the deadline ends the run.
            words = await asyncio.wait_for(read(address, count), timeout=self.remaining())
        except ModbusError as err:
            entry.update(_failure(err))
            self._transport_errors = self._transport_errors + 1 if entry["status"] == "transport_error" else 0
            raise
        except TimeoutError:
            entry["status"] = "stopped_at_time_limit"
            raise ProbeStopped("stopped_at_time_limit") from None
        self._transport_errors = 0
        if len(words) != count:
            # Passing a short answer on would fail the poll's decoding outside the report.
            entry.update(status="invalid_response", words=list(words))
            raise _ShortResponseError(f"{len(words)} words for {count} requested")
        entry.update(_outcome(words))
        return words


async def probe(
    unit: ModbusUnit,
    maps: Iterable[str],
    *,
    poll: str | None = None,
    limits: ProbeLimits | None = None,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> ProbeReport:
    """Run one poll of the ``poll`` family, then read every address of ``maps`` singly.

    Modbus exceptions are results, not errors: the run continues past them. It
    ends early when a limit is reached, and ``status`` says which.
    """
    names = list(dict.fromkeys(maps))
    for name in (*names, *([poll] if poll else [])):
        if name not in REGISTER_MAPS:
            raise ValueError(f"Unknown register map {name!r}")
    limits = limits or ProbeLimits()
    report = ProbeReport(maps=names, poll=poll)
    guard = _ProbeUnit(unit, limits, clock)

    try:
        if poll:
            api = _POLL_APIS[poll](guard)
            try:
                await api.async_read_raw()
            except ModbusError as err:
                report.poll_result = _failure(err)
            else:
                report.poll_result = {"status": "ok"}
            finally:
                report.poll_requests = guard.log
                guard.log = []

        for index, (space, address, owners) in enumerate(build_plan(names)):
            if index:
                await sleep(min(limits.pause, guard.remaining()))
            read = guard.read_input_registers if space == "input" else guard.read_holding_registers
            try:
                await read(address, 1)
            except ModbusError:
                pass
            finally:
                # Empty when a limit stopped the run before this request was sent.
                if guard.log:
                    report.registers.append({"maps": owners, **guard.log.pop()})
    except ProbeStopped as stop:
        report.status = stop.status
        if poll and report.poll_result is None:
            report.poll_result = {"status": "not_finished"}
    return report
