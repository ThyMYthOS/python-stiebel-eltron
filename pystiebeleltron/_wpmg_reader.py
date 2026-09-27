"""Bounded FC04 fault isolation for the experimental ISG WPM G API."""

from __future__ import annotations

from asyncio import CancelledError
from copy import deepcopy
from datetime import UTC, datetime
from time import monotonic
from typing import Any

from modbus_connection import IllegalDataAddressError, ModbusProtocolError, ModbusUnit

from . import UNAVAILABLE


class WpmGReader:
    """Adapt input reads without changing the component decoder or its cache.

    Only illegal addresses are isolated. Transport, busy and other device errors
    still fail the poll. Replacing rejected words with the documented sentinel
    clears previously valid values through the normal public decoding path.
    """

    MAX_EXTRA_READS = 32
    RETRY_SECONDS = 300

    def __init__(self, unit: ModbusUnit, ranges: tuple[tuple[int, int], ...]) -> None:
        self._unit = unit
        self._retry_at: dict[int, float] = {}
        self._split_blocks: dict[tuple[int, int], float] = {}
        self._registers: dict[int, dict[str, Any]] = {}
        self._extra_reads = 0
        self._requests = 0
        self._poll: dict[str, Any] = {"status": "not_started"}
        for first, last in ranges:
            for address in range(first, last + 1):
                self._record(address, "not_read")

    @property
    def connected(self) -> bool:
        return self._unit.connected

    def start_poll(self) -> None:
        self._started = monotonic()
        self._extra_reads = self.MAX_EXTRA_READS
        self._requests = 0
        self._poll = {"status": "running", "started_utc": datetime.now(UTC).isoformat()}
        for row in self._registers.values():
            row["status"] = "not_read"
            row["raw_u16"] = None

    def finish_poll(self, error: BaseException | None = None) -> None:
        self._poll.update(
            status="error" if error else "completed",
            finished_utc=datetime.now(UTC).isoformat(),
            requests=self._requests,
            duration_seconds=round(monotonic() - self._started, 3),
        )
        if error is not None:
            self._poll["error_type"] = type(error).__name__
        elif any(row["status"] != "ok" for row in self._registers.values()):
            self._poll["status"] = "partial"

    def retry_failed_registers(self) -> None:
        """Allow immediate re-probing on the next regular poll."""
        self._retry_at.clear()
        self._split_blocks.clear()

    @property
    def report(self) -> dict[str, Any]:
        return deepcopy(
            {
                **self._poll,
                "function_code": 4,
                "retry_seconds": self.RETRY_SECONDS,
                "max_extra_reads": self.MAX_EXTRA_READS,
                "split_blocks": [{"wire_address": address, "count": count, "exception_code": 2} for address, count in sorted(self._split_blocks)],
                "registers": [self._registers[address] for address in sorted(self._registers)],
            }
        )

    def _record(self, address: int, status: str, raw: int | None = None) -> None:
        now = datetime.now(UTC).isoformat()
        row = self._registers.setdefault(
            address,
            {
                "wire_address": address,
                "documented_reference": address + 30001,
                "failure_count": 0,
            },
        )
        row.update(status="device_unavailable" if status == "ok" and raw == UNAVAILABLE else status, raw_u16=raw)
        if status == "ok":
            row["last_success_utc"] = now
            row.pop("error_type", None)
            row.pop("exception_code", None)
        elif status == "unsupported":
            row.setdefault("first_failure_utc", now)
            row.update(last_failure_utc=now, failure_count=row["failure_count"] + 1, error_type="IllegalDataAddressError", exception_code=2)

    async def read_input_registers(self, address: int, count: int) -> list[int]:
        """Read a planned block, preserving neighbours around rejected words."""
        # A known bad word is skipped temporarily, never dropped permanently.
        for rejected in range(address, address + count):
            if self._retry_at.get(rejected, 0) > monotonic():
                before = await self.read_input_registers(address, rejected - address) if rejected > address else []
                self._record(rejected, "retry_pending")
                after_count = address + count - rejected - 1
                after = await self.read_input_registers(rejected + 1, after_count) if after_count else []
                return [*before, UNAVAILABLE, *after]
        return await self._read(address, count, extra=False)

    async def _read(self, address: int, count: int, *, extra: bool) -> list[int]:
        # Reuse learned subdivision. A block rejection is not proof that any
        # one word is bad (some gateways reject long reads). This also advances
        # discovery on later polls instead of exhausting the budget in the same
        # parent blocks forever. At most one normal request per declared word,
        # plus MAX_EXTRA_READS exploratory requests, can reach the device.
        if self._split_blocks.get((address, count), 0) > monotonic():
            midpoint = count // 2
            left = await self._read(address, midpoint, extra=False)
            right = await self._read(address + midpoint, count - midpoint, extra=False)
            return [*left, *right]
        if count == 1 and self._retry_at.get(address, 0) > monotonic():
            self._record(address, "retry_pending")
            return [UNAVAILABLE]
        if extra:
            if self._extra_reads == 0:
                for word in range(address, address + count):
                    self._record(word, "not_probed_budget")
                return [UNAVAILABLE] * count
            self._extra_reads -= 1
        self._requests += 1
        try:
            words = await self._unit.read_input_registers(address, count)
            if len(words) != count:
                raise ModbusProtocolError("Unexpected FC04 response length")
        except IllegalDataAddressError:
            if count == 1:
                self._retry_at[address] = monotonic() + self.RETRY_SECONDS
                self._record(address, "unsupported")
                return [UNAVAILABLE]
            self._split_blocks[address, count] = monotonic() + self.RETRY_SECONDS
            midpoint = count // 2
            left = await self._read(address, midpoint, extra=True)
            right = await self._read(address + midpoint, count - midpoint, extra=True)
            return [*left, *right]
        except (Exception, CancelledError) as error:
            self._poll["failed_request"] = {"wire_address": address, "count": count, "error_type": type(error).__name__, "exception_code": getattr(error, "exception_code", None)}
            raise
        for block in list(self._split_blocks):
            if address <= block[0] and block[0] + block[1] <= address + count:
                del self._split_blocks[block]
        for offset, word in enumerate(words):
            self._retry_at.pop(address + offset, None)
            self._record(address + offset, "ok", word)
        return words
