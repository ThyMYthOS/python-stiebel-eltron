from __future__ import annotations

import logging
from enum import Enum
from typing import Any

from modbus_connection import ModbusError, ModbusUnit
from modbus_connection.model import Component, RegisterField, WriteValidator, integer

__version__ = "0.5.0"

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


def in_range(minimum: float, maximum: float) -> WriteValidator:
    """A write validator rejecting values outside the register's ``[min, max]``.

    Passed as a writable field's ``writable=`` so a write never pushes a value the
    controller documents as invalid; the accepted value passes through unchanged.
    """

    def validate(value: Any) -> Any:
        if not minimum <= value <= maximum:
            raise ValueError(f"{value} outside the allowed range [{minimum}, {maximum}]")
        return value

    return validate


class StiebelEltronModbusError(Exception):
    """Exception during modbus communication."""

    def __init__(self) -> None:
        """Initialize the error."""
        super().__init__("Data error on the modbus")


class UnknownControllerModelError(Exception):
    """The controller reported a model id we don't recognize."""

    def __init__(self, model_id: int) -> None:
        """Initialize the error with the unrecognized ``model_id``."""
        self.model_id = model_id
        super().__init__(f"Unknown controller model id: {model_id}")


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
        model_id = registers[0]
    except (ModbusError, IndexError) as err:
        raise StiebelEltronModbusError from err
    try:
        return ControllerModel(model_id)
    except ValueError as err:
        raise UnknownControllerModelError(model_id) from err


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
