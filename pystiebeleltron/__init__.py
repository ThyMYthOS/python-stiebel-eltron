from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

from modbus_connection import ModbusError, ModbusUnit

__version__ = "0.3.2"

_LOGGER = logging.getLogger(__package__)

ENERGY_DATA_BLOCK_NAME = "Energy Data"
VIRTUAL_REGISTER_OFFSET = 100000
VIRTUAL_TOTAL_AND_DAY_REGISTER_OFFSET = 200000


class IsgRegisters(Enum):
    """ISG Register base class."""


class IsgRegistersNone(IsgRegisters):
    """Dummy registers."""

    NONE = -1


class EnergyManagementSettingsRegisters(IsgRegisters):
    """Energy Management settings registers."""

    SWITCH_SG_READY_ON_AND_OFF = 4001
    SG_READY_INPUT_1 = 4002
    SG_READY_INPUT_2 = 4003


class EnergySystemInformationRegisters(IsgRegisters):
    """Energy Management information registers."""

    SG_READY_OPERATING_STATE = 5001
    CONTROLLER_IDENTIFICATION = 5002


@dataclass
class ModbusRegister:
    """Register data class."""

    address: int
    name: str
    unit: str
    min: float | None
    max: float | None
    data_type: int
    key: IsgRegisters

    @property
    def is_virtual_register(self) -> bool:
        """Registers with an address above"""
        return self.address > VIRTUAL_REGISTER_OFFSET


class RegisterType(Enum):
    """Register type enum."""

    INPUT_REGISTER = 1
    HOLDING_REGISTER = 2


@dataclass
class ModbusRegisterBlock:
    """Register block data class."""

    base_address: int
    count: int
    name: str
    registers: dict[IsgRegisters, ModbusRegister]
    register_type: RegisterType


ENERGY_MANAGEMENT_SETTINGS_REGISTERS: dict[IsgRegisters, ModbusRegister] = {
    EnergyManagementSettingsRegisters.SWITCH_SG_READY_ON_AND_OFF: ModbusRegister(
        address=4001, name="SWITCH SG READY ON AND OFF", unit="", min=0.0, max=1.0, data_type=6, key=EnergyManagementSettingsRegisters.SWITCH_SG_READY_ON_AND_OFF
    ),
    EnergyManagementSettingsRegisters.SG_READY_INPUT_1: ModbusRegister(
        address=4002, name="SG READY INPUT 1", unit="", min=0.0, max=1.0, data_type=6, key=EnergyManagementSettingsRegisters.SG_READY_INPUT_1
    ),
    EnergyManagementSettingsRegisters.SG_READY_INPUT_2: ModbusRegister(
        address=4003, name="SG READY INPUT 2", unit="", min=0.0, max=1.0, data_type=6, key=EnergyManagementSettingsRegisters.SG_READY_INPUT_2
    ),
}

ENERGY_SYSTEM_INFORMATION_REGISTERS: dict[IsgRegisters, ModbusRegister] = {
    EnergySystemInformationRegisters.SG_READY_OPERATING_STATE: ModbusRegister(
        address=5001, name="SG READY OPERATING STATE", unit="", min=1.0, max=4.0, data_type=6, key=EnergySystemInformationRegisters.SG_READY_OPERATING_STATE
    ),
    EnergySystemInformationRegisters.CONTROLLER_IDENTIFICATION: ModbusRegister(
        address=5002, name="CONTROLLER IDENTIFICATION", unit="", min=None, max=None, data_type=6, key=EnergySystemInformationRegisters.CONTROLLER_IDENTIFICATION
    ),
}


def get_register_descriptor(descriptors: list[ModbusRegister], address: int) -> ModbusRegister | None:
    """Find the descriptor with a given address."""
    for descriptor in descriptors:
        if descriptor.address == address:
            return descriptor
    return None


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


def _to_int16(register: int) -> int:
    """Interpret a raw 16-bit register value as a signed integer."""
    return register - 0x10000 if register >= 0x8000 else register


def _to_uint16(value: int) -> int:
    """Encode an integer as a raw 16-bit register value."""
    return value & 0xFFFF


class StiebelEltronAPI:
    """Stiebel Eltron API."""

    def __init__(
        self,
        register_blocks: list[ModbusRegisterBlock],
        unit: ModbusUnit,
    ) -> None:
        """Initialize Stiebel Eltron communication.

        The ``unit`` is an already-bound ``ModbusUnit`` from the
        ``modbus_connection`` library. The owner of the underlying connection is
        responsible for its lifecycle (connecting, closing, reconnecting).
        """
        self._unit = unit
        self._register_blocks = register_blocks
        self._data: dict[IsgRegisters, float | int | None] = {}
        self._previous_data: dict[IsgRegisters, float | int | None] = {}
        self._modbus_data: dict[str, list[int] | None] = {}  # store raw data from modbus for debug purpose

    @property
    def is_connected(self) -> bool:
        """Check modbus connection status."""
        return self._unit.connected

    def get_register_descriptor(self, register: IsgRegisters) -> ModbusRegister | None:
        """Get the descriptor of a register."""
        for registerblock in self._register_blocks:
            descriptor = get_register_descriptor(
                list(registerblock.registers.values()),
                register.value,
            )
            if descriptor is not None:
                return descriptor
        return None

    def get_register_value(self, register: IsgRegisters) -> float | int | None:
        """Get a value form the registers. The async_udpate needs to be called first."""
        return self._data[register]

    def has_register_value(self, register: IsgRegisters) -> bool:
        """Check if a value for the registers has been read. The async_udpate needs to be called first."""
        return register in self._data and self._data[register] is not None

    async def write_register_value(self, register: IsgRegisters, value: int | float) -> None:
        """Writes a modbus register."""
        descriptor = self.get_register_descriptor(register)
        if descriptor is not None:
            await self._unit.write_register(descriptor.address - 1, self.convert_value_to_modbus(value, descriptor))
        else:
            raise ValueError("invalid register")

    async def read_input_registers(self, address: int, count: int) -> list[int]:
        """Read input registers."""
        _LOGGER.debug(f"Reading {count} input registers from {address}")
        return await self._unit.read_input_registers(address, count)

    async def read_holding_registers(self, address: int, count: int) -> list[int]:
        """Read holding registers."""
        _LOGGER.debug(f"Reading {count} holding registers from {address}")
        return await self._unit.read_holding_registers(address, count)

    def convert_value_from_modbus(self, register: int, register_description: ModbusRegister) -> float | int | None:
        """Convert a modbus value to a python value."""
        if register_description.data_type == 2:
            value = _to_int16(register)
            if value == -32768:
                return None
            return float(value) * 0.1
        elif register_description.data_type == 6:
            if register == 32768:
                return None
            return register
        elif register_description.data_type == 7:
            value = _to_int16(register)
            if value == -32768:
                return None
            return value * 0.01
        elif register_description.data_type == 8:
            if register == 32768:
                return None
            return register
        raise ValueError("invalid register.")

    def convert_value_to_modbus(self, value: int | float, register_description: ModbusRegister) -> int:
        """Convert a python value to a modbus register value."""
        if register_description.data_type == 2:
            return _to_uint16(int(value * 10))
        elif register_description.data_type == 6:
            return _to_uint16(int(value))
        elif register_description.data_type == 7:
            return _to_uint16(int(value * 100))
        elif register_description.data_type == 8:
            return _to_uint16(int(value))
        else:
            raise ValueError("invalid register type")

    async def async_update(self) -> None:
        """Request current values from heat pump."""
        result: dict[IsgRegisters, float | int | None] = {}
        for registerblock in self._register_blocks:
            try:
                if registerblock.register_type == RegisterType.INPUT_REGISTER:
                    registers = await self.read_input_registers(registerblock.base_address, registerblock.count)
                elif registerblock.register_type == RegisterType.HOLDING_REGISTER:
                    registers = await self.read_holding_registers(registerblock.base_address, registerblock.count)
                else:
                    continue
            except ModbusError:
                self._modbus_data[registerblock.name] = None
                continue

            self._modbus_data[registerblock.name] = registers
            for i in range(0, registerblock.count):
                descriptor = get_register_descriptor(
                    list(registerblock.registers.values()),
                    i + registerblock.base_address + 1,
                )
                if descriptor is not None:
                    result[descriptor.key] = self.convert_value_from_modbus(registers[i], descriptor)
        self._previous_data = self._data
        self._data = result
