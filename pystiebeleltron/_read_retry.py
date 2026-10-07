"""Bounded input-read retry for ISGs that reject an unsupported block start."""

from __future__ import annotations

from typing import Any

from modbus_connection import IllegalDataAddressError, ModbusUnit


class InputStartRetry:
    """Delegate I/O, retrying once from a start answered during this poll.

    This applies only to input reads. An accepted start is not evidence that
    every longer read from it succeeds, so retry errors still propagate.
    """

    def __init__(self, unit: ModbusUnit) -> None:
        self._unit = unit
        self._starts: set[int] = set()

    def begin_poll(self) -> None:
        """Forget preceding starts so a new poll must establish its own anchors."""
        self._starts.clear()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._unit, name)

    async def read_input_registers(self, address: int, count: int) -> list[int]:
        """Retry illegal-address responses without scanning or exceeding 125 words."""
        try:
            values = await self._unit.read_input_registers(address, count)
        except IllegalDataAddressError:
            candidates = [start for start in self._starts if start < address and address + count - start <= 125]
            if not candidates:
                raise
            start = max(candidates)
            values = await self._unit.read_input_registers(start, address + count - start)
            return values[address - start:]
        self._starts.add(address)
        return values
