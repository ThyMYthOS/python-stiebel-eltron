"""Bounded register-read retry for ISGs that reject an unsupported block start."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from modbus_connection import IllegalDataAddressError, ModbusUnit


class ReadStartRetry:
    """Delegate I/O, retrying once from a start answered in the same space/poll.

    An accepted start does not guarantee that a longer read succeeds. Retry
    errors still propagate, and recovered target starts never become anchors.
    Writes and other operations are forwarded without retry.
    """

    def __init__(self, unit: ModbusUnit) -> None:
        self._unit = unit
        self._input_starts: set[int] = set()
        self._holding_starts: set[int] = set()

    def begin_poll(self) -> None:
        """Forget both spaces so each new poll establishes its own anchors."""
        self._input_starts.clear()
        self._holding_starts.clear()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._unit, name)

    async def read_input_registers(self, address: int, count: int) -> list[int]:
        return await self._read(self._unit.read_input_registers, self._input_starts, address, count)

    async def read_holding_registers(self, address: int, count: int) -> list[int]:
        return await self._read(self._unit.read_holding_registers, self._holding_starts, address, count)

    async def _read(self, read: Callable[[int, int], Awaitable[list[int]]], starts: set[int], address: int, count: int) -> list[int]:
        """Retry only illegal-address responses, without scans or over 125 words."""
        try:
            values = await read(address, count)
        except IllegalDataAddressError:
            candidates = [start for start in starts if start < address and address + count - start <= 125]
            if not candidates:
                raise
            start = max(candidates)
            values = await read(start, address + count - start)
            return values[address - start:]
        starts.add(address)
        return values
