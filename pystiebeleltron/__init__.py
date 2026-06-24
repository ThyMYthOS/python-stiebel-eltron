"""Python API for Stiebel Eltron ISG heat pumps over Modbus.

Built on the ``modbus_connection`` device-model framework: each register block is
a :class:`~modbus_connection.model.Component` of typed fields, and a heat pump
(see :mod:`pystiebeleltron.wpm` / :mod:`pystiebeleltron.lwz`) groups its
components behind one pooled update.

See the ISG Modbus manual:
https://www.stiebel-eltron.de/content/dam/ste/de/de/home/services/Downloadlisten/ISG%20Modbus_Stiebel_Bedienungsanleitung.pdf
"""

from __future__ import annotations

import logging
from enum import Enum

from modbus_connection import ModbusError, ModbusUnit
from modbus_connection.model import Component, integer

__version__ = "0.3.2"

_LOGGER = logging.getLogger(__package__)

# Raw register value the ISG returns for an unavailable / unimplemented object.
UNAVAILABLE = 0x8000


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
    except ModbusError as err:
        raise StiebelEltronModbusError from err
    return ControllerModel(registers[0])


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
