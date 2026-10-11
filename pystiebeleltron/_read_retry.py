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

    A refused read that a retry recovered is remembered with the start that
    served it, so later polls read from that start straight away instead of
    sending the refused request again. If the controller refuses the
    remembered read, it is forgotten and the read takes the normal path.
    """

    def __init__(self, unit: ModbusUnit) -> None:
        self._unit = unit
        self._input_starts: set[int] = set()
        self._holding_starts: set[int] = set()
        self._input_recovered: dict[tuple[int, int], int] = {}
        self._holding_recovered: dict[tuple[int, int], int] = {}

    def begin_poll(self) -> None:
        """Forget both spaces' anchors so each new poll establishes its own.

        Recovered reads stay remembered across polls.
        """
        self._input_starts.clear()
        self._holding_starts.clear()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._unit, name)

    async def read_input_registers(self, address: int, count: int) -> list[int]:
        return await self._read(self._unit.read_input_registers, self._input_starts, self._input_recovered, address, count)

    async def read_holding_registers(self, address: int, count: int) -> list[int]:
        return await self._read(self._unit.read_holding_registers, self._holding_starts, self._holding_recovered, address, count)

    async def _read(
        self,
        read: Callable[[int, int], Awaitable[list[int]]],
        starts: set[int],
        recovered: dict[tuple[int, int], int],
        address: int,
        count: int,
    ) -> list[int]:
        """Retry only illegal-address responses, without scans or over 125 words."""
        remembered = recovered.get((address, count))
        if remembered is not None:
            try:
                values = await read(remembered, address + count - remembered)
            except IllegalDataAddressError:
                del recovered[(address, count)]
            else:
                return values[address - remembered :]
        try:
            values = await read(address, count)
        except IllegalDataAddressError:
            candidates = [start for start in starts if start < address and address + count - start <= 125]
            if not candidates:
                raise
            start = max(candidates)
            values = await read(start, address + count - start)
            recovered[(address, count)] = start
            return values[address - start :]
        starts.add(address)
        return values
