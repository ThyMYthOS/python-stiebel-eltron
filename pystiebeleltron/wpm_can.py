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
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Any, Callable, Optional

import can

_LOGGER = logging.getLogger(__name__)


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


class PropertyType(Enum):
    """Property data types."""
    DEFAULT = "default"  # No conversion (uint16)
    DEC_VAL = "dec_val"  # Decimal value (*0.1)
    CENT_VAL = "cent_val"  # Centimal value (*0.01)
    DOUBLE_VAL = "double_val"  # Double word value
    LITTLE_ENDIAN = "little_endian"  # Little endian uint16
    LITTLE_BOOL = "little_bool"  # Little endian bool
    BOOL = "bool"  # Boolean
    BYTE = "byte"  # Single byte
    BETRIEBSART = "betriebsart"  # Operating mode


@dataclass
class Property:
    """Represents a CAN bus property."""
    name: str
    id: int
    type: PropertyType = PropertyType.DEFAULT


class WPMProperties:
    """Common properties for WPM heat pumps."""

    # System temperatures
    AUSSENTEMP = Property("AUSSENTEMP", 0x000c, PropertyType.DEC_VAL)
    SPEICHERISTTEMP = Property("SPEICHERISTTEMP", 0x000e, PropertyType.DEC_VAL)
    SPEICHERSOLLTEMP = Property("SPEICHERSOLLTEMP", 0x0003, PropertyType.DEC_VAL)
    VORLAUFSOLLTEMP = Property("VORLAUFSOLLTEMP", 0x0004, PropertyType.DEC_VAL)
    VORLAUFISTTEMP = Property("VORLAUFISTTEMP", 0xfdf3, PropertyType.DEC_VAL)
    RUECKLAUFISTTEMP = Property("RUECKLAUFISTTEMP", 0x0016, PropertyType.DEC_VAL)
    RAUMISTTEMP = Property("RAUMISTTEMP", 0x0011, PropertyType.DEC_VAL)
    RAUMSOLLTEMP = Property("RAUMSOLLTEMP", 0x4ece, PropertyType.DEC_VAL)
    KOMFORTTEMPERATUR = Property("KOMFORTTEMPERATUR", 0x4eb8, PropertyType.DEC_VAL)
    ECOTEMPERATUR = Property("ECOTEMPERATUR", 0x4eb9, PropertyType.DEC_VAL)

    # Heat pump status
    BETRIEBS_STATUS = Property("BETRIEBS_STATUS", 0x0176)
    PROGRAMMSCHALTER = Property("PROGRAMMSCHALTER", 0x0112, PropertyType.BETRIEBSART)
    FEHLERMELDUNG = Property("FEHLERMELDUNG", 0x0001)

    # Heating circuit
    STEIGUNG_HEIZKURVE = Property("STEIGUNG_HEIZKURVE", 0x4f2b, PropertyType.DEC_VAL)
    STEIGUNG_HK1 = Property("STEIGUNG_HK1", 0x010e, PropertyType.CENT_VAL)
    FUSSPUNKT_HK1 = Property("FUSSPUNKT_HK1", 0x059e, PropertyType.DEC_VAL)

    # Pressures and volumes
    HEIZUNGSDRUCK = Property("HEIZUNGSDRUCK", 0x4f46, PropertyType.CENT_VAL)
    VOLUMENSTROM = Property("VOLUMENSTROM", 0x01da, PropertyType.DEC_VAL)
    DRUCK_HOCHDRUCK = Property("DRUCK_HOCHDRUCK", 0x07a6, PropertyType.DEC_VAL)
    DRUCK_NIEDERDRUCK = Property("DRUCK_NIEDERDRUCK", 0x07a7, PropertyType.DEC_VAL)
    QUELLENDRUCK = Property("QUELLENDRUCK", 0x4fa8, PropertyType.DEC_VAL)

    # Compressor
    VERDICHTERDREHZAHL = Property("VERDICHTERDREHZAHL", 0x069e)
    VERDICHTER_STARTS = Property("VERDICHTER_STARTS", 0x4ef1)
    HEISSGASTEMP = Property("HEISSGASTEMP", 0x0265, PropertyType.DEC_VAL)
    VERDAMPFERTEMP = Property("VERDAMPFERTEMP", 0x0014, PropertyType.DEC_VAL)

    # Energy consumption
    EL_ENERGIEAUFNAHME_WW_TAG_WH = Property("EL_ENERGIEAUFNAHME_WW_TAG_WH", 0x091a)
    EL_ENERGIEAUFNAHME_WW_TAG_KWH = Property("EL_ENERGIEAUFNAHME_WW_TAG_KWH", 0x091b, PropertyType.DOUBLE_VAL)
    EL_ENERGIEAUFNAHME_HEIZ_TAG_WH = Property("EL_ENERGIEAUFNAHME_HEIZ_TAG_WH", 0x091e)
    EL_ENERGIEAUFNAHME_HEIZ_TAG_KWH = Property("EL_ENERGIEAUFNAHME_HEIZ_TAG_KWH", 0x091f, PropertyType.DOUBLE_VAL)
    WAERMEERTRAG_WW_TAG_WH = Property("WAERMEERTRAG_WW_TAG_WH", 0x092a)
    WAERMEERTRAG_WW_TAG_KWH = Property("WAERMEERTRAG_WW_TAG_KWH", 0x092b, PropertyType.DOUBLE_VAL)
    WAERMEERTRAG_HEIZ_TAG_WH = Property("WAERMEERTRAG_HEIZ_TAG_WH", 0x092e)
    WAERMEERTRAG_HEIZ_TAG_KWH = Property("WAERMEERTRAG_HEIZ_TAG_KWH", 0x092f, PropertyType.DOUBLE_VAL)

    # Cooling
    KUEHLMODE = Property("KUEHLMODE", 0x0287, PropertyType.BOOL)
    KUEHL_RAUMSOLL_TAG = Property("KUEHL_RAUMSOLL_TAG", 0x0569, PropertyType.DEC_VAL)

    # Time
    JAHR = Property("JAHR", 0x0124, PropertyType.LITTLE_ENDIAN)
    MONAT = Property("MONAT", 0x0123, PropertyType.LITTLE_ENDIAN)
    TAG = Property("TAG", 0x0122, PropertyType.LITTLE_ENDIAN)
    STUNDE = Property("STUNDE", 0x0125, PropertyType.LITTLE_ENDIAN)
    MINUTE = Property("MINUTE", 0x0126, PropertyType.LITTLE_ENDIAN)
    WOCHENTAG = Property("WOCHENTAG", 0x0121, PropertyType.LITTLE_ENDIAN)


class WPMCanAPI:
    """CAN bus API for Stiebel Eltron WPM heat pumps."""

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
        self._notifier: Optional[can.Notifier] = None
        self._running = False

    def connect(self) -> None:
        """Connect to the CAN bus."""
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

    async def async_connect(self) -> None:
        """Asynchronously connect to the CAN bus."""
        self.connect()

    def close(self) -> None:
        """Close the CAN bus connection."""
        if self._notifier:
            self._notifier.stop()
            self._notifier = None
        if self.bus:
            self.bus.shutdown()
            self.bus = None
            _LOGGER.info("Disconnected from CAN bus")

    async def async_close(self) -> None:
        """Asynchronously close the CAN bus connection."""
        self.close()

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

        if external_id & 0x200:
            message_type = MessageType.RESPONSE
        elif external_id & 0x100:
            message_type = MessageType.READ
        else:
            message_type = MessageType.WRITE

        can_id = ((write_id >> 5) & 0x7c0) | (write_id & 0x3f)
        return can_id, message_type

    def _convert_value_from_raw(self, raw_value: int, prop_type: PropertyType) -> Any:
        """Convert raw uint16 value to the appropriate type."""
        # Handle signed values
        signed_value = raw_value - 0x10000 if raw_value > 0x7FFF else raw_value

        if prop_type == PropertyType.DEC_VAL:
            return signed_value * 0.1
        elif prop_type == PropertyType.CENT_VAL:
            return signed_value * 0.01
        elif prop_type == PropertyType.BOOL:
            return bool(raw_value)
        elif prop_type == PropertyType.BYTE:
            return raw_value & 0xFF
        elif prop_type == PropertyType.LITTLE_ENDIAN:
            # Swap bytes for little endian
            return ((raw_value & 0xFF) << 8) | ((raw_value >> 8) & 0xFF)
        elif prop_type == PropertyType.LITTLE_BOOL:
            # Swap bytes then convert to bool
            swapped = ((raw_value & 0xFF) << 8) | ((raw_value >> 8) & 0xFF)
            return bool(swapped)
        else:
            return raw_value

    def _convert_value_to_raw(self, value: Any, prop_type: PropertyType) -> int:
        """Convert typed value to raw uint16."""
        if prop_type == PropertyType.DEC_VAL:
            raw = int(round(value * 10))
        elif prop_type == PropertyType.CENT_VAL:
            raw = int(round(value * 100))
        elif prop_type == PropertyType.BOOL or prop_type == PropertyType.LITTLE_BOOL:
            raw = 1 if value else 0
        elif prop_type == PropertyType.LITTLE_ENDIAN:
            # Swap bytes for little endian
            val_int = int(value)
            raw = ((val_int & 0xFF) << 8) | ((val_int >> 8) & 0xFF)
        else:
            raw = int(value)

        # Handle negative values (two's complement)
        if raw < 0:
            raw = raw + 0x10000

        return raw & 0xFFFF

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

    def start_listening(self) -> None:
        """Start listening for CAN messages."""
        if not self.bus:
            raise RuntimeError("Not connected to CAN bus")

        self._running = True
        self._notifier = can.Notifier(self.bus, [self._handle_can_message])
        _LOGGER.info("Started listening for CAN messages")

    def stop_listening(self) -> None:
        """Stop listening for CAN messages."""
        self._running = False
        if self._notifier:
            self._notifier.stop()
            self._notifier = None
        _LOGGER.info("Stopped listening for CAN messages")

    def request_property(self, property: Property, member: Optional[CANMember] = None) -> None:
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

    async def async_request_property(self, property: Property, member: Optional[CANMember] = None) -> None:
        """Asynchronously request a property value from the heat pump."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.request_property, property, member)

    def write_property(self, property: Property, value: Any, member: Optional[CANMember] = None) -> None:
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

        # Convert value to raw format
        raw_value = self._convert_value_to_raw(value, property.type)

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

    async def async_write_property(self, property: Property, value: Any, member: Optional[CANMember] = None) -> None:
        """Asynchronously write a property value to the heat pump."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.write_property, property, value, member)

    def get_property_value(self, property: Property) -> Optional[Any]:
        """Get the last received value for a property.

        Args:
            property: The property to get

        Returns:
            The converted value or None if not available
        """
        raw_value = self._data.get(property.id)
        if raw_value is None:
            return None
        return self._convert_value_from_raw(raw_value, property.type)

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

    async def async_update(self, properties: Optional[list[Property]] = None) -> None:
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
            await self.async_request_property(prop)
            # Small delay between requests to avoid flooding the bus
            await asyncio.sleep(0.05)

    def __enter__(self) -> "WPMCanAPI":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[Any]) -> None:
        """Context manager exit."""
        self.close()
