# Implementation Summary: python-can Based CAN Bus API for Stiebel Eltron WPM

## Overview

This implementation provides a complete python-can based API for communicating with Stiebel Eltron WPM heat pumps via CAN bus, based on the OneESP32ToRuleThemAll project by kr0ner.

## Files Created

### 1. Core API Module: `pystiebeleltron/wpm_can.py`
The main CAN bus API implementation with the following features:

- **WPMCanAPI Class**: Main API for CAN communication
  - Connection management (connect/disconnect)
  - Asynchronous operations support
  - Context manager support
  - Message parsing and encoding

- **CAN Protocol Implementation**:
  - Message ID encoding/decoding
  - Property request/response handling
  - Write operations
  - Value type conversion (DEC_VAL, CENT_VAL, BOOL, etc.)

- **Property Definitions**:
  - WPMProperties class with ~50+ pre-defined properties
  - Temperature sensors
  - Status registers
  - Energy consumption counters
  - Compressor information
  - Heating circuit settings

- **Monitoring Features**:
  - Real-time message listening
  - Callback registration for property updates
  - Background message processing

### 2. Example Script: `wpm-can-example.py`
Comprehensive examples demonstrating:

1. **Basic Usage**: Request and read single/multiple properties
2. **Writing Values**: Set comfort temperature and verify
3. **Real-time Monitoring**: Monitor property changes with callbacks
4. **Energy Monitoring**: Track energy consumption and calculate COP
5. **Context Manager**: Using the API with automatic cleanup

### 3. Documentation: `CAN_API_README.md`
Detailed documentation covering:

- Hardware requirements (CAN interfaces, connections)
- Software setup (python-can, SocketCAN configuration)
- Complete usage examples
- Property reference
- CAN protocol details
- Troubleshooting guide
- Safety notes

### 4. Additional Files
- `requirements-can.txt`: Python dependencies for CAN support
- `README.md`: Updated main README with CAN bus information
- `pystiebeleltron/__init__.py`: Updated to expose CAN API

## Key Features

### Protocol Implementation
Based on OneESP32ToRuleThemAll's communication protocol:

1. **Message Format**:
   - 7-byte CAN data frames
   - Standard 11-bit identifiers
   - Property ID + value encoding

2. **Message Types**:
   - Read (0x100): Request property value
   - Write (0x00): Set property value
   - Response (0x200): Property value response

3. **Data Types**:
   - DEC_VAL: Decimal values (×0.1)
   - CENT_VAL: Centimal values (×0.01)
   - BOOL: Boolean values
   - LITTLE_ENDIAN: Byte-swapped values
   - DEFAULT: Raw uint16 values

### CAN Members Supported
- KESSEL (0x180): Heat pump controller
- HK1 (0x301): Heating circuit 1
- HK2 (0x302): Heating circuit 2
- FET (0x402): Room controller
- MANAGER (0x600): System manager
- ESPCLIENT (0x680): Client/controller ID

### Properties Included
Over 50 properties covering:
- Temperatures (outside, flow, return, storage, room, etc.)
- Pressures (heating, high, low, source)
- Flow rates
- Compressor information
- Energy consumption (daily values)
- System status
- Operating modes
- Comfort settings

## Usage Patterns

### Synchronous
```python
with WPMCanAPI('can0', 'socketcan') as api:
    api.start_listening()
    api.request_property(WPMProperties.AUSSENTEMP)
    time.sleep(0.5)
    temp = api.get_property_value(WPMProperties.AUSSENTEMP)
```

### Asynchronous
```python
async with WPMCanAPI('can0', 'socketcan') as api:
    api.start_listening()
    await api.async_request_property(WPMProperties.AUSSENTEMP)
    await asyncio.sleep(0.5)
    temp = api.get_property_value(WPMProperties.AUSSENTEMP)
```

### With Callbacks
```python
def on_update(prop_id, raw_value):
    print(f"Property {prop_id:04x} updated: {raw_value}")

api.register_callback(WPMProperties.AUSSENTEMP.id, on_update)
```

## Testing

To test without hardware:

```bash
# Create virtual CAN interface
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0

# Run examples with vcan0
python wpm-can-example.py
```

For testing with candump:
```bash
# Monitor CAN traffic
candump vcan0

# Send test messages (in another terminal)
cansend vcan0 680#0101FA000C00EB  # Response with outside temp 23.5°C
```

## Integration with Existing Code

The CAN bus API is designed to work alongside the existing Modbus TCP API:

- Modbus TCP via ISG gateway: Use existing `wpm.py` API
- Direct CAN bus: Use new `wpm_can.py` API
- Both share similar async/await patterns
- Property naming intentionally different to avoid confusion

## References

This implementation is based on:
- [OneESP32ToRuleThemAll](https://github.com/kr0ner/OneESP32ToRuleThemAll) by kr0ner
- [python-can Documentation](https://python-can.readthedocs.io/)
- Community knowledge from Home Assistant forum

## Next Steps

Potential enhancements:
1. Add more property definitions from OneESP32ToRuleThemAll
2. Implement device auto-discovery
3. Add caching/rate limiting for repeated requests
4. Create Home Assistant integration
5. Add support for other Stiebel Eltron models (THZ, LWZ, etc.)
6. Implement error code mapping
7. Add logging improvements
8. Create unit tests with mock CAN interfaces

## Notes

- The API is designed to be non-intrusive and safe
- All write operations should be tested carefully
- Always monitor the heat pump after making changes
- Keep the original controller connected
- Follow local regulations and safety guidelines
