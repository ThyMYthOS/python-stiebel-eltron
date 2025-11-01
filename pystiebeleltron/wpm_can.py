"""CAN bus API for Stiebel Eltron WPM heat pumps.

This module provides a python-can based interface to communicate with
Stiebel Eltron WPM heat pumps via CAN bus.

Based on the OneESP32ToRuleThemAll project:
https://github.com/kr0ner/OneESP32ToRuleThemAll
"""

from __future__ import annotations

import asyncio
import logging
import struct
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Callable, Generic, Optional, TypeVar

import can

_LOGGER = logging.getLogger(__name__)

T = TypeVar('T')


class CANMember(IntEnum):
    """CAN bus member identifiers."""
    PYCLIENT = 0x680
    MANAGER = 0x600
    KESSEL = 0x180  # Heat pump controller
    HK1 = 0x301  # Heating circuit 1
    HK2 = 0x302  # Heating circuit 2
    FET = 0x402  # FET (room controller)
    MFG = 0x700  # MFG (manufacturer?)
    WPM2 = 0x480  # WPM2


class MessageType(IntEnum):
    """CAN message types."""
    WRITE = 0x000
    READ = 0x100
    RESPONSE = 0x200
    UNKNOWN = 0x300


class PropertyType(ABC, Generic[T]):
    """Base class for property type converters."""

    @abstractmethod
    def deserialize(self, raw_value: int) -> T:
        """Convert raw uint16 value to typed value."""
        pass

    @abstractmethod
    def serialize(self, value: T) -> int:
        """Convert typed value to raw uint16."""
        pass


class DefaultType(PropertyType[int]):
    """No conversion - raw uint16 value."""

    def deserialize(self, raw_value: int) -> int:
        return raw_value

    def serialize(self, value: int) -> int:
        return int(value) & 0xFFFF


class DecimalType(PropertyType[float]):
    """Decimal value with 0.1 precision (value × 0.1)."""

    def deserialize(self, raw_value: int) -> float:
        # Handle signed values
        signed_value = raw_value - 0x10000 if raw_value > 0x7FFF else raw_value
        return signed_value * 0.1

    def serialize(self, value: float) -> int:
        raw = int(round(value * 10))
        # Handle negative values (two's complement)
        if raw < 0:
            raw = raw + 0x10000
        return raw & 0xFFFF


class CentimalType(PropertyType[float]):
    """Centimal value with 0.01 precision (value × 0.01)."""

    def deserialize(self, raw_value: int) -> float:
        # Handle signed values
        signed_value = raw_value - 0x10000 if raw_value > 0x7FFF else raw_value
        return signed_value * 0.01

    def serialize(self, value: float) -> int:
        raw = int(round(value * 100))
        # Handle negative values (two's complement)
        if raw < 0:
            raw = raw + 0x10000
        return raw & 0xFFFF


class BoolType(PropertyType[bool]):
    """Boolean value (0 or 1)."""

    def deserialize(self, raw_value: int) -> bool:
        return bool(raw_value)

    def serialize(self, value: bool) -> int:
        return 1 if value else 0


class ByteType(PropertyType[int]):
    """Single byte value (0-255)."""

    def deserialize(self, raw_value: int) -> int:
        return raw_value & 0xFF

    def serialize(self, value: int) -> int:
        return int(value) & 0xFF


class LittleEndianType(PropertyType[int]):
    """Little endian uint16 (byte-swapped)."""

    def deserialize(self, raw_value: int) -> int:
        # Swap bytes for little endian
        return ((raw_value & 0xFF) << 8) | ((raw_value >> 8) & 0xFF)

    def serialize(self, value: int) -> int:
        # Swap bytes for little endian
        val_int = int(value)
        return (((val_int & 0xFF) << 8) | ((val_int >> 8) & 0xFF)) & 0xFFFF


class LittleBoolType(PropertyType[bool]):
    """Little endian boolean."""

    def deserialize(self, raw_value: int) -> bool:
        # Swap bytes then convert to bool
        swapped = ((raw_value & 0xFF) << 8) | ((raw_value >> 8) & 0xFF)
        return bool(swapped)

    def serialize(self, value: bool) -> int:
        raw = 1 if value else 0
        return ((raw & 0xFF) << 8) | ((raw >> 8) & 0xFF)


class BetriebsartType(PropertyType[int]):
    """Operating mode value."""

    def deserialize(self, raw_value: int) -> int:
        return raw_value

    def serialize(self, value: int) -> int:
        return int(value) & 0xFFFF


@dataclass
class Property(Generic[T]):
    """Represents a CAN bus property with type-safe serialization.

    Args:
        name: Property name
        id: Property ID (CAN identifier)
        type_converter: PropertyType instance for serialization/deserialization
    """
    name: str
    id: int
    type_converter: PropertyType[T]

    def deserialize(self, raw_value: int) -> T:
        """Deserialize raw value to typed value."""
        return self.type_converter.deserialize(raw_value)

    def serialize(self, value: T) -> int:
        """Serialize typed value to raw value."""
        return self.type_converter.serialize(value)


class WPMProperties:
    """Common properties for WPM heat pumps."""

    # System temperatures
    AUSSENTEMP: Property[float] = Property("AUSSENTEMP", 0x000c, DecimalType())
    SPEICHERISTTEMP: Property[float] = Property("SPEICHERISTTEMP", 0x000e, DecimalType())
    SPEICHERSOLLTEMP: Property[float] = Property("SPEICHERSOLLTEMP", 0x0003, DecimalType())
    VORLAUFSOLLTEMP: Property[float] = Property("VORLAUFSOLLTEMP", 0x0004, DecimalType())
    VORLAUFISTTEMP: Property[float] = Property("VORLAUFISTTEMP", 0xfdf3, DecimalType())
    RUECKLAUFISTTEMP: Property[float] = Property("RUECKLAUFISTTEMP", 0x0016, DecimalType())
    RAUMISTTEMP: Property[float] = Property("RAUMISTTEMP", 0x0011, DecimalType())
    RAUMSOLLTEMP: Property[float] = Property("RAUMSOLLTEMP", 0x4ece, DecimalType())
    KOMFORTTEMPERATUR: Property[float] = Property("KOMFORTTEMPERATUR", 0x4eb8, DecimalType())
    ECOTEMPERATUR: Property[float] = Property("ECOTEMPERATUR", 0x4eb9, DecimalType())

    # Heat pump status
    BETRIEBS_STATUS: Property[int] = Property("BETRIEBS_STATUS", 0x0176, DefaultType())
    PROGRAMMSCHALTER: Property[int] = Property("PROGRAMMSCHALTER", 0x0112, BetriebsartType())
    FEHLERMELDUNG: Property[int] = Property("FEHLERMELDUNG", 0x0001, DefaultType())

    # Heating circuit
    STEIGUNG_HEIZKURVE: Property[float] = Property("STEIGUNG_HEIZKURVE", 0x4f2b, DecimalType())
    STEIGUNG_HK1: Property[float] = Property("STEIGUNG_HK1", 0x010e, CentimalType())
    FUSSPUNKT_HK1: Property[float] = Property("FUSSPUNKT_HK1", 0x059e, DecimalType())

    # Pressures and volumes
    HEIZUNGSDRUCK: Property[float] = Property("HEIZUNGSDRUCK", 0x4f46, CentimalType())
    VOLUMENSTROM: Property[float] = Property("VOLUMENSTROM", 0x01da, DecimalType())
    DRUCK_HOCHDRUCK: Property[float] = Property("DRUCK_HOCHDRUCK", 0x07a6, DecimalType())
    DRUCK_NIEDERDRUCK: Property[float] = Property("DRUCK_NIEDERDRUCK", 0x07a7, DecimalType())
    QUELLENDRUCK: Property[float] = Property("QUELLENDRUCK", 0x4fa8, DecimalType())

    # Compressor
    VERDICHTERDREHZAHL: Property[int] = Property("VERDICHTERDREHZAHL", 0x069e, DefaultType())
    VERDICHTER_STARTS: Property[int] = Property("VERDICHTER_STARTS", 0x4ef1, DefaultType())
    HEISSGASTEMP: Property[float] = Property("HEISSGASTEMP", 0x0265, DecimalType())
    VERDAMPFERTEMP: Property[float] = Property("VERDAMPFERTEMP", 0x0014, DecimalType())

    # Energy consumption (using default for now, double word would need special handling)
    EL_ENERGIEAUFNAHME_WW_TAG_WH: Property[int] = Property("EL_ENERGIEAUFNAHME_WW_TAG_WH", 0x091a, DefaultType())
    EL_ENERGIEAUFNAHME_WW_TAG_KWH: Property[int] = Property("EL_ENERGIEAUFNAHME_WW_TAG_KWH", 0x091b, DefaultType())
    EL_ENERGIEAUFNAHME_HEIZ_TAG_WH: Property[int] = Property("EL_ENERGIEAUFNAHME_HEIZ_TAG_WH", 0x091e, DefaultType())
    EL_ENERGIEAUFNAHME_HEIZ_TAG_KWH: Property[int] = Property("EL_ENERGIEAUFNAHME_HEIZ_TAG_KWH", 0x091f, DefaultType())
    WAERMEERTRAG_WW_TAG_WH: Property[int] = Property("WAERMEERTRAG_WW_TAG_WH", 0x092a, DefaultType())
    WAERMEERTRAG_WW_TAG_KWH: Property[int] = Property("WAERMEERTRAG_WW_TAG_KWH", 0x092b, DefaultType())
    WAERMEERTRAG_HEIZ_TAG_WH: Property[int] = Property("WAERMEERTRAG_HEIZ_TAG_WH", 0x092e, DefaultType())
    WAERMEERTRAG_HEIZ_TAG_KWH: Property[int] = Property("WAERMEERTRAG_HEIZ_TAG_KWH", 0x092f, DefaultType())

    # Cooling
    KUEHLMODE: Property[bool] = Property("KUEHLMODE", 0x0287, BoolType())
    KUEHL_RAUMSOLL_TAG: Property[float] = Property("KUEHL_RAUMSOLL_TAG", 0x0569, DecimalType())

    # Time
    JAHR: Property[int] = Property("JAHR", 0x0124, LittleEndianType())
    MONAT: Property[int] = Property("MONAT", 0x0123, LittleEndianType())
    TAG: Property[int] = Property("TAG", 0x0122, LittleEndianType())
    STUNDE: Property[int] = Property("STUNDE", 0x0125, LittleEndianType())
    MINUTE: Property[int] = Property("MINUTE", 0x0126, LittleEndianType())
    WOCHENTAG: Property[int] = Property("WOCHENTAG", 0x0121, LittleEndianType())


class WPMCanAPI:
    """Async CAN bus API for Stiebel Eltron WPM heat pumps."""

    def __init__(
        self,
        interface: str,
        bustype: str = "socketcan",
        bitrate: int = 20000,
        client_id: CANMember = CANMember.PYCLIENT,
        target_id: CANMember = CANMember.KESSEL,
    ):
        """Initialize the CAN bus API.

        Args:
            interface: CAN interface name (e.g., 'can0', 'vcan0')
            bustype: CAN bus type (e.g., 'socketcan', 'pcan', 'usb2can')
            bitrate: CAN bus bitrate in bits/s (default: 20000 for Stiebel Eltron)
            client_id: CAN ID to use for this client
            target_id: Target device CAN ID (usually KESSEL for heat pump)
        """
        self.interface = interface
        self.bustype = bustype
        self.bitrate = bitrate
        self.client_id = client_id
        self.target_id = target_id
        self.bus: Optional[can.BusABC] = None
        self._data: dict[int, Any] = {}
        self._callbacks: dict[int, list[Callable[[int, int], None]]] = {}
        self._reader_task: Optional[asyncio.Task[None]] = None
        self._running = False

    async def connect(self) -> None:
        """Connect to the CAN bus asynchronously."""
        try:
            self.bus = can.Bus(
                interface=self.interface,
                bustype=self.bustype,
                bitrate=self.bitrate
            )
            _LOGGER.info(f"Connected to CAN bus on {self.interface}")
        except Exception as e:
            _LOGGER.error(f"Failed to connect to CAN bus: {e}")
            raise

    async def close(self) -> None:
        """Close the CAN bus connection asynchronously."""
        await self.stop_listening()
        if self.bus:
            self.bus.shutdown()
            self.bus = None
            _LOGGER.info("Disconnected from CAN bus")

    def _encode_message_id(self, can_id: int, message_type: MessageType) -> int:
        """Encode CAN ID and message type into the write/read/response ID.

        The encoding scheme:
        - Write:    base write ID = ((can_id & 0x7c0) << 5) | (can_id & 0x3f)
        - Read:     write ID | 0x100
        - Response: write ID | 0x200
        """
        write_id = ((can_id & 0x7c0) << 5) | (can_id & 0x3f)
        return write_id | message_type

    def _decode_message_id(self, external_id: int) -> tuple[int, MessageType]:
        """Decode external ID into CAN ID and message type."""
        message_type = MessageType.WRITE
        write_id = external_id & ~0x300
        message_type = MessageType(external_id & 0x300)

        can_id = ((write_id >> 5) & 0x7c0) | (write_id & 0x3f)
        return can_id, message_type

    def _parse_can_message(self, msg: can.Message) -> Optional[tuple[int, int, int]]:
        """Parse a CAN message and extract property ID and value.

        Returns:
            Tuple of (can_id, property_id, raw_value) or None if invalid
        """
        if len(msg.data) < 7:
            return None

        # Decode the message ID to get CAN ID and type
        can_id, msg_type = self._decode_message_id(msg.arbitration_id)

        # We only process responses
        if msg_type != MessageType.RESPONSE:
            return None

        # Parse the data bytes
        if msg.data[2] == 0xfa:
            # Extended format with FA marker
            property_id = (msg.data[3] << 8) | msg.data[4]
            raw_value = (msg.data[5] << 8) | msg.data[6]
        else:
            # Short format
            property_id = msg.data[2]
            raw_value = (msg.data[3] << 8) | msg.data[4]

        return can_id, property_id, raw_value

    def _handle_can_message(self, msg: can.Message) -> None:
        """Handle incoming CAN messages."""
        parsed = self._parse_can_message(msg)
        if not parsed:
            return

        can_id, property_id, raw_value = parsed

        _LOGGER.debug(
            f"Received CAN message: ID=0x{can_id:03x}, "
            f"Property=0x{property_id:04x}, Value={raw_value:04x}"
        )

        # Store the raw value
        self._data[property_id] = raw_value

        # Call registered callbacks
        if property_id in self._callbacks:
            for callback in self._callbacks[property_id]:
                try:
                    callback(property_id, raw_value)
                except Exception as e:
                    _LOGGER.error(f"Error in callback for property 0x{property_id:04x}: {e}")

    async def _read_loop(self) -> None:
        """Async loop to read CAN messages."""
        if not self.bus:
            return

        reader = can.AsyncBufferedReader()
        notifier = can.Notifier(self.bus, [reader], loop=asyncio.get_running_loop())

        try:
            while self._running:
                msg = await reader.get_message()
                if msg:
                    self._handle_can_message(msg)
        finally:
            notifier.stop()

    async def start_listening(self) -> None:
        """Start listening for CAN messages asynchronously."""
        if not self.bus:
            raise RuntimeError("Not connected to CAN bus")

        if self._running:
            return

        self._running = True
        self._reader_task = asyncio.create_task(self._read_loop())
        _LOGGER.info("Started listening for CAN messages")

    async def stop_listening(self) -> None:
        """Stop listening for CAN messages asynchronously."""
        if not self._running:
            return

        self._running = False
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
            self._reader_task = None
        _LOGGER.info("Stopped listening for CAN messages")

    async def request_property(self, property: Property[Any], member: Optional[CANMember] = None) -> None:
        """Request a property value from the heat pump.

        Args:
            property: The property to request
            member: Target CAN member (defaults to self.target_id)
        """
        if not self.bus:
            raise RuntimeError("Not connected to CAN bus")

        if member is None:
            member = self.target_id

        # Build the request message
        read_id = self._encode_message_id(member, MessageType.READ)

        # Message format: [ID_byte1, ID_byte2, 0xFA, Prop_byte1, Prop_byte2, 0x00, 0x00]
        id_bytes = struct.pack(">H", read_id)
        prop_bytes = struct.pack(">H", property.id)
        data = bytearray([id_bytes[0], id_bytes[1], 0xfa, prop_bytes[0], prop_bytes[1], 0x00, 0x00])

        msg = can.Message(
            arbitration_id=self.client_id,
            data=data,
            is_extended_id=False
        )

        try:
            self.bus.send(msg)
            _LOGGER.debug(f"Requested property {property.name} (0x{property.id:04x}) from 0x{member:03x}")
        except Exception as e:
            _LOGGER.error(f"Failed to send request: {e}")
            raise

    async def write_property(self, property: Property[Any], value: Any, member: Optional[CANMember] = None) -> None:
        """Write a property value to the heat pump.

        Args:
            property: The property to write
            value: The value to write (will be converted based on property type)
            member: Target CAN member (defaults to self.target_id)
        """
        if not self.bus:
            raise RuntimeError("Not connected to CAN bus")

        if member is None:
            member = self.target_id

        # Convert value to raw format using the property's type converter
        raw_value = property.type_converter.serialize(value)

        # Build the write message
        write_id = self._encode_message_id(member, MessageType.WRITE)

        # Message format: [ID_byte1, ID_byte2, 0xFA, Prop_byte1, Prop_byte2, Val_byte1, Val_byte2]
        id_bytes = struct.pack(">H", write_id)
        prop_bytes = struct.pack(">H", property.id)
        val_bytes = struct.pack(">H", raw_value)
        data = bytearray([id_bytes[0], id_bytes[1], 0xfa, prop_bytes[0], prop_bytes[1], val_bytes[0], val_bytes[1]])

        msg = can.Message(
            arbitration_id=self.client_id,
            data=data,
            is_extended_id=False
        )

        try:
            self.bus.send(msg)
            _LOGGER.info(
                f"Wrote property {property.name} (0x{property.id:04x}) = {value} "
                f"(raw: 0x{raw_value:04x}) to 0x{member:03x}"
            )
        except Exception as e:
            _LOGGER.error(f"Failed to send write: {e}")
            raise

    def get_property_value(self, property: Property[Any]) -> Optional[Any]:
        """Get the last received value for a property.

        Args:
            property: The property to get

        Returns:
            The converted value or None if not available
        """
        raw_value = self._data.get(property.id)
        if raw_value is None:
            return None
        return property.type_converter.deserialize(raw_value)

    def get_raw_value(self, property_id: int) -> Optional[int]:
        """Get the raw value for a property ID.

        Args:
            property_id: The property ID

        Returns:
            The raw uint16 value or None if not available
        """
        return self._data.get(property_id)

    def register_callback(self, property_id: int, callback: Callable[[int, int], None]) -> None:
        """Register a callback for property updates.

        Args:
            property_id: The property ID to monitor
            callback: Function to call with (property_id, raw_value) when updated
        """
        if property_id not in self._callbacks:
            self._callbacks[property_id] = []
        self._callbacks[property_id].append(callback)

    def unregister_callback(self, property_id: int, callback: Callable[[int, int], None]) -> None:
        """Unregister a callback for property updates.

        Args:
            property_id: The property ID
            callback: The callback to remove
        """
        if property_id in self._callbacks:
            try:
                self._callbacks[property_id].remove(callback)
            except ValueError:
                pass

    async def update(self, properties: Optional[list[Property[Any]]] = None) -> None:
        """Request updates for multiple properties.

        Args:
            properties: List of properties to request (None = use default set)
        """
        if properties is None:
            # Default set of common properties
            properties = [
                WPMProperties.AUSSENTEMP,
                WPMProperties.VORLAUFISTTEMP,
                WPMProperties.RUECKLAUFISTTEMP,
                WPMProperties.SPEICHERISTTEMP,
                WPMProperties.SPEICHERSOLLTEMP,
                WPMProperties.RAUMISTTEMP,
                WPMProperties.BETRIEBS_STATUS,
                WPMProperties.HEIZUNGSDRUCK,
                WPMProperties.VOLUMENSTROM,
            ]

        for prop in properties:
            await self.request_property(prop)
            # Small delay between requests to avoid flooding the bus
            await asyncio.sleep(0.05)

    async def __aenter__(self) -> "WPMCanAPI":
        """Async context manager entry."""
        await self.connect()
        await self.start_listening()
        return self

    async def __aexit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[Any]) -> None:
        """Async context manager exit."""
        await self.close()
