from __future__ import annotations

import logging
from enum import Enum

from modbus_connection import ModbusError, ModbusUnit
from modbus_connection.model import Component, RegisterField, integer

__version__ = "0.3.2"

_LOGGER = logging.getLogger(__package__)

# Raw register value the ISG returns for an unavailable / unimplemented object.
UNAVAILABLE = 0x8000


class MagnitudeField(RegisterField[int]):
    """Consecutive registers summed by per-register weight (read-only).

    A Stiebel energy counter splits a total across registers of rising magnitude
    (e.g. kWh remainder + MWh whole); ``MagnitudeField(addr, (1, 1000))`` reads
    both and returns the total in the lowest unit. A word equal to ``nan`` (the
    unavailable sentinel) makes the whole counter decode to ``None``.
    """

    def __init__(self, address: int, magnitudes: tuple[int, ...], *, nan: int | None = None, unit: str | None = None) -> None:
        """Build the field over ``len(magnitudes)`` consecutive registers."""
        super().__init__(address, count=len(magnitudes), unit=unit)
        self._magnitudes = magnitudes
        self._nan = nan

    def decode(self, words: list[int], scale_exponent: int | None = None) -> int | None:
        """Sum each register word weighted by its magnitude, or None if unavailable."""
        if self._nan is not None and self._nan in words:
            return None
        return sum((word & 0xFFFF) * magnitude for word, magnitude in zip(words, self._magnitudes, strict=True))


def scaled_sum(address: int, magnitudes: tuple[int, ...] = (1, 1000, 1_000_000), *, unit: str | None = None) -> MagnitudeField:
    """Build a :class:`MagnitudeField` using the ISG unavailable sentinel."""
    return MagnitudeField(address, magnitudes, nan=UNAVAILABLE, unit=unit)


class StiebelEltronModbusError(Exception):
    """Exception during modbus communication."""

    def __init__(self) -> None:
        """Initialize the error."""
        super().__init__("Data error on the modbus")


class ControllerModel(Enum):
    """Controller model."""

    LWZ = 103
    LWZ_x04_SOL = 104

    WPM_3 = 390
    WPM_3i = 391
    WPMsystem = 449
    LWZ_R290 = 551


async def get_controller_model(unit: ModbusUnit) -> ControllerModel:
    """Read the model of the controller.

    LWA and LWZ controllers have model ids 103 and 104.
    WPM controllers have 390, 391 or 449.
    """
    try:
        registers = await unit.read_input_registers(5001, 1)
        return ControllerModel(registers[0])
    except (ModbusError, IndexError, ValueError) as err:
        raise StiebelEltronModbusError from err


class EnergyManagementSettings(Component):
    """SG Ready energy-management settings (holding registers, read/write)."""

    register_space = "holding"

    switch_sg_ready_on_and_off = integer(4000, signed=False, nan=UNAVAILABLE, writable=True)
    sg_ready_input_1 = integer(4001, signed=False, nan=UNAVAILABLE, writable=True)
    sg_ready_input_2 = integer(4002, signed=False, nan=UNAVAILABLE, writable=True)


class EnergySystemInformation(Component):
    """SG Ready / controller identification information (input registers)."""

    register_space = "input"

    sg_ready_operating_state = integer(5000, signed=False, nan=UNAVAILABLE)
    controller_identification = integer(5001, signed=False, nan=UNAVAILABLE)
