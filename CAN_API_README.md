# Stiebel Eltron WPM CAN Bus API

This module provides a Python interface to communicate with Stiebel Eltron WPM (Wärmepumpenmanager) heat pumps via CAN bus.

## Overview

The CAN bus API allows direct communication with Stiebel Eltron heat pumps using the CAN protocol, as an alternative to the Modbus TCP interface. This can provide faster response times and access to additional parameters not available via Modbus.

### Key Features

- **Read Properties**: Request and read sensor values and status information
- **Write Properties**: Set configuration parameters and target temperatures
- **Real-time Monitoring**: Subscribe to property changes with callbacks
- **Async Support**: Full async/await support for non-blocking operations
- **Type Conversion**: Automatic conversion between raw CAN values and meaningful units
- **Multiple Devices**: Support for different CAN members (heat pump, heating circuits, room controllers)

## Based On

This implementation is based on the excellent [OneESP32ToRuleThemAll](https://github.com/kr0ner/OneESP32ToRuleThemAll) project, which provides ESP32-based CAN bus control for Stiebel Eltron heat pumps.

## Requirements

### Hardware

1. **CAN Interface**: You need a CAN bus interface to connect to your heat pump:
   - **USB-CAN Adapter**: PEAK PCAN-USB, Kvaser Leaf Light, CANable, etc.
   - **SPI-CAN Module**: MCP2515 module with Raspberry Pi
   - **Built-in CAN**: Some single-board computers have built-in CAN

2. **Physical Connection**: Connect to the heat pump's CAN bus:
   - CAN High (CANH)
   - CAN Low (CANL)
   - Ground (GND)
   - **Important**: Use proper termination resistors (120Ω) if required

### Software

```bash
pip install python-can
```

### CAN Bus Setup

#### Linux (SocketCAN)

```bash
# Load kernel module
sudo modprobe can
sudo modprobe can_raw

# Configure CAN interface (adjust for your hardware)
# For USB-CAN adapters:
sudo ip link set can0 type can bitrate 20000
sudo ip link set can0 up

# For SPI-CAN (e.g., MCP2515 on Raspberry Pi):
# Add to /boot/config.txt:
# dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25
# Then:
sudo ip link set can0 type can bitrate 20000
sudo ip link set can0 up
```

#### Virtual CAN for Testing

```bash
# Create virtual CAN interface for testing
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```

## Usage

### Basic Example

```python
import asyncio
from pystiebeleltron.wpm_can import WPMCanAPI, WPMProperties

async def main():
    # Create API instance
    api = WPMCanAPI(
        channel='can0',  # Your CAN interface
        bustype='socketcan',
        bitrate=20000,  # Stiebel Eltron uses 20 kbit/s
    )

    try:
        # Connect
        await api.async_connect()
        api.start_listening()

        # Request outside temperature
        await api.async_request_property(WPMProperties.AUSSENTEMP)
        await asyncio.sleep(0.5)  # Wait for response

        # Get the value
        temp = api.get_property_value(WPMProperties.AUSSENTEMP)
        print(f"Outside temperature: {temp:.1f}°C")

    finally:
        api.stop_listening()
        await api.async_close()

asyncio.run(main())
```

### Reading Multiple Properties

```python
async def read_temperatures():
    api = WPMCanAPI(channel='can0', bustype='socketcan')

    try:
        await api.async_connect()
        api.start_listening()

        # Request multiple properties at once
        await api.async_update([
            WPMProperties.AUSSENTEMP,
            WPMProperties.VORLAUFISTTEMP,
            WPMProperties.RUECKLAUFISTTEMP,
            WPMProperties.SPEICHERISTTEMP,
        ])

        # Wait for responses
        await asyncio.sleep(2)

        # Display values
        print(f"Outside:  {api.get_property_value(WPMProperties.AUSSENTEMP):.1f}°C")
        print(f"Flow:     {api.get_property_value(WPMProperties.VORLAUFISTTEMP):.1f}°C")
        print(f"Return:   {api.get_property_value(WPMProperties.RUECKLAUFISTTEMP):.1f}°C")
        print(f"Storage:  {api.get_property_value(WPMProperties.SPEICHERISTTEMP):.1f}°C")

    finally:
        api.stop_listening()
        await api.async_close()
```

### Writing Properties

```python
async def set_comfort_temperature():
    api = WPMCanAPI(channel='can0', bustype='socketcan')

    try:
        await api.async_connect()
        api.start_listening()

        # Read current value
        await api.async_request_property(WPMProperties.KOMFORTTEMPERATUR)
        await asyncio.sleep(0.5)
        current = api.get_property_value(WPMProperties.KOMFORTTEMPERATUR)
        print(f"Current comfort temp: {current:.1f}°C")

        # Write new value
        new_temp = 21.5
        await api.async_write_property(WPMProperties.KOMFORTTEMPERATUR, new_temp)
        print(f"Set to: {new_temp:.1f}°C")

        # Verify
        await asyncio.sleep(1)
        await api.async_request_property(WPMProperties.KOMFORTTEMPERATUR)
        await asyncio.sleep(0.5)
        verified = api.get_property_value(WPMProperties.KOMFORTTEMPERATUR)
        print(f"Verified: {verified:.1f}°C")

    finally:
        api.stop_listening()
        await api.async_close()
```

### Real-time Monitoring with Callbacks

```python
async def monitor_temperatures():
    api = WPMCanAPI(channel='can0', bustype='socketcan')

    def on_temp_change(prop_id, raw_value):
        # This is called whenever a monitored property changes
        value = api._convert_value_from_raw(raw_value, PropertyType.DEC_VAL)
        print(f"Temperature changed: 0x{prop_id:04x} = {value:.1f}°C")

    try:
        await api.async_connect()

        # Register callbacks
        api.register_callback(WPMProperties.AUSSENTEMP.id, on_temp_change)
        api.register_callback(WPMProperties.VORLAUFISTTEMP.id, on_temp_change)

        api.start_listening()

        # Keep monitoring
        while True:
            await api.async_update([
                WPMProperties.AUSSENTEMP,
                WPMProperties.VORLAUFISTTEMP,
            ])
            await asyncio.sleep(5)

    finally:
        api.stop_listening()
        await api.async_close()
```

### Using Context Manager

```python
async def simple_read():
    with WPMCanAPI(channel='can0', bustype='socketcan') as api:
        api.start_listening()
        await api.async_request_property(WPMProperties.AUSSENTEMP)
        await asyncio.sleep(0.5)
        temp = api.get_property_value(WPMProperties.AUSSENTEMP)
        print(f"Temperature: {temp:.1f}°C")
```

## Available Properties

The `WPMProperties` class provides access to common heat pump properties:

### Temperature Sensors
- `AUSSENTEMP` - Outside temperature
- `VORLAUFISTTEMP` - Flow temperature (actual)
- `VORLAUFSOLLTEMP` - Flow temperature (target)
- `RUECKLAUFISTTEMP` - Return temperature
- `SPEICHERISTTEMP` - Storage temperature (actual)
- `SPEICHERSOLLTEMP` - Storage temperature (target)
- `RAUMISTTEMP` - Room temperature
- `VERDAMPFERTEMP` - Evaporator temperature
- `HEISSGASTEMP` - Hot gas temperature

### Comfort Settings
- `KOMFORTTEMPERATUR` - Comfort temperature
- `ECOTEMPERATUR` - Eco temperature
- `RAUMSOLLTEMP` - Room target temperature

### System Status
- `BETRIEBS_STATUS` - Operating status
- `PROGRAMMSCHALTER` - Operating mode
- `FEHLERMELDUNG` - Error message
- `KUEHLMODE` - Cooling mode

### Pressures and Flow
- `HEIZUNGSDRUCK` - Heating pressure
- `VOLUMENSTROM` - Flow rate
- `DRUCK_HOCHDRUCK` - High pressure
- `DRUCK_NIEDERDRUCK` - Low pressure
- `QUELLENDRUCK` - Source pressure

### Compressor
- `VERDICHTERDREHZAHL` - Compressor speed
- `VERDICHTER_STARTS` - Compressor starts counter

### Energy (Daily)
- `EL_ENERGIEAUFNAHME_WW_TAG_WH` - DHW electrical consumption (Wh)
- `EL_ENERGIEAUFNAHME_HEIZ_TAG_WH` - Heating electrical consumption (Wh)
- `WAERMEERTRAG_WW_TAG_WH` - DHW heat production (Wh)
- `WAERMEERTRAG_HEIZ_TAG_WH` - Heating heat production (Wh)

### Heating Circuit
- `STEIGUNG_HEIZKURVE` - Heating curve slope
- `STEIGUNG_HK1` - Heating circuit 1 slope
- `FUSSPUNKT_HK1` - Heating circuit 1 base point

## CAN Bus Protocol

### Message Format

The Stiebel Eltron CAN protocol uses standard 11-bit CAN identifiers with 7-byte data frames:

```
[ID_Hi] [ID_Lo] [0xFA] [Prop_Hi] [Prop_Lo] [Val_Hi] [Val_Lo]
```

- **ID bytes**: Encoded CAN member ID + message type
- **0xFA**: Protocol marker
- **Prop bytes**: Property ID (16-bit)
- **Val bytes**: Property value (16-bit)

### Message Types

- **Write (0x00)**: Set a property value
- **Read (0x100)**: Request a property value
- **Response (0x200)**: Response with property value

### CAN Members

- `ESPCLIENT (0x680)`: Your client/controller
- `KESSEL (0x180)`: Heat pump controller (main target)
- `HK1 (0x301)`: Heating circuit 1
- `HK2 (0x302)`: Heating circuit 2
- `FET (0x402)`: Room controller
- `MANAGER (0x600)`: System manager

### Data Types

Values are encoded as 16-bit integers with various conversion factors:

- **DEFAULT**: Raw uint16 value
- **DEC_VAL**: Value × 0.1 (e.g., 235 → 23.5°C)
- **CENT_VAL**: Value × 0.01 (e.g., 150 → 1.50 bar)
- **BOOL**: Boolean (0/1)
- **LITTLE_ENDIAN**: Byte-swapped uint16

## Troubleshooting

### No CAN Interface Found

```
Error: Network is down
```

**Solution**: Check if your CAN interface is up:
```bash
sudo ip link set can0 up
```

### No Response from Heat Pump

1. **Check Connection**: Verify CAN_H, CAN_L, and GND are correctly connected
2. **Check Termination**: Ensure 120Ω termination resistors are in place
3. **Check Bitrate**: Stiebel Eltron uses 20 kbit/s
4. **Check Traffic**: Use `candump can0` to see if there's any CAN traffic

### Wrong Values

1. **Check Property ID**: Verify you're using the correct property ID for your heat pump model
2. **Check Data Type**: Ensure the PropertyType matches (DEC_VAL, CENT_VAL, etc.)
3. **Monitor Raw Values**: Use `candump can0` to see raw CAN messages

### Permission Denied

```bash
# Add your user to the dialout/can group
sudo usermod -a -G dialout $USER
# Log out and back in for changes to take effect
```

## Advanced Usage

### Custom Properties

You can define custom properties for your specific heat pump model:

```python
from pystiebeleltron.wpm_can import Property, PropertyType

# Define custom property
MY_PROPERTY = Property("MY_PROPERTY", 0x1234, PropertyType.DEC_VAL)

# Use it
await api.async_request_property(MY_PROPERTY)
value = api.get_property_value(MY_PROPERTY)
```

### Different CAN Members

Target different CAN members:

```python
from pystiebeleltron.wpm_can import CANMember

# Request from heating circuit 1
await api.async_request_property(
    WPMProperties.RAUMISTTEMP,
    member=CANMember.HK1
)

# Write to FET room controller
await api.async_write_property(
    WPMProperties.RAUMSOLLTEMP,
    22.0,
    member=CANMember.FET
)
```

## Safety Notes

⚠️ **Important Safety Information**:

1. **Do not** disconnect the heat pump's original controller
2. **Test carefully** before deploying to production
3. **Monitor** the system after making changes
4. **Keep logs** of all write operations
5. **Have a backup** plan to restore original settings
6. **Consult** the heat pump manual and local regulations

## References

- [OneESP32ToRuleThemAll](https://github.com/kr0ner/OneESP32ToRuleThemAll) - Original ESP32 implementation
- [python-can Documentation](https://python-can.readthedocs.io/)
- [SocketCAN Documentation](https://www.kernel.org/doc/html/latest/networking/can.html)
- [Home Assistant Community Forum](https://community.home-assistant.io/t/configured-my-esphome-with-mcp2515-can-bus-for-stiebel-eltron-heating-pump/366053)

## License

This implementation is provided as-is for educational and personal use. Please respect the licenses of the referenced projects and follow all applicable regulations for interfacing with heating equipment.
