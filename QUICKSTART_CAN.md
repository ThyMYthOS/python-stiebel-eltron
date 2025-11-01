# Quick Start Guide: CAN Bus API for Stiebel Eltron WPM

This guide will get you up and running with the CAN bus API in 10 minutes.

## Prerequisites

- Linux system with CAN interface (or Raspberry Pi with MCP2515 module)
- Stiebel Eltron WPM heat pump
- Physical access to the heat pump's CAN bus

## Step 1: Install Dependencies

```bash
# Install python-can with your CAN adapter support
# For socketcan (Linux native, most USB-CAN adapters):
pip install "python-can[socketcan]"

# For PCAN adapters:
pip install "python-can[pcan]"

# For Kvaser adapters:
pip install "python-can[kvaser]"

# For other adapters, see: https://python-can.readthedocs.io/

# Install the library (when published)
pip install pystiebeleltron
```

## Step 2: Setup CAN Interface

### For USB-CAN Adapter (e.g., PEAK PCAN-USB, Kvaser)

```bash
# Load CAN modules
sudo modprobe can
sudo modprobe can_raw

# Configure interface (replace can0 with your interface)
sudo ip link set can0 type can bitrate 20000
sudo ip link set can0 up

# Verify
ip link show can0
```

### For MCP2515 on Raspberry Pi

```bash
# Add to /boot/config.txt (or /boot/firmware/config.txt on newer systems)
dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25
dtparam=spi=on

# Reboot
sudo reboot

# After reboot, configure
sudo ip link set can0 type can bitrate 20000
sudo ip link set can0 up
```

## Step 3: Verify CAN Connection

```bash
# Install can-utils if needed
sudo apt-get install can-utils

# Monitor CAN traffic
candump can0

# You should see messages from your heat pump
# If not, check your connections
```

## Step 4: Test the API

Create a test script `test_can.py`:

```python
#!/usr/bin/env python3
import asyncio
from pystiebeleltron.wpm_can import WPMCanAPI, WPMProperties

async def main():
    # Create API instance
    api = WPMCanAPI(
        channel='can0',  # Your CAN interface
        bustype='socketcan',
        bitrate=20000
    )

    try:
        print("Connecting to CAN bus...")
        await api.async_connect()
        print("Connected!")

        # Start listening for messages
        api.start_listening()
        print("Listening for responses...\n")

        # Request outside temperature
        print("Requesting outside temperature...")
        await api.async_request_property(WPMProperties.AUSSENTEMP)

        # Wait for response
        await asyncio.sleep(1)

        # Get and display the value
        temp = api.get_property_value(WPMProperties.AUSSENTEMP)
        if temp is not None:
            print(f"✓ Outside temperature: {temp:.1f}°C")
        else:
            print("✗ No response received")
            print("  Check your CAN connection and verify traffic with 'candump can0'")

        # Request a few more values
        print("\nRequesting more properties...")
        await api.async_update([
            WPMProperties.VORLAUFISTTEMP,
            WPMProperties.RUECKLAUFISTTEMP,
            WPMProperties.SPEICHERISTTEMP,
        ])

        await asyncio.sleep(2)

        print("\n=== Current Values ===")
        flow = api.get_property_value(WPMProperties.VORLAUFISTTEMP)
        ret = api.get_property_value(WPMProperties.RUECKLAUFISTTEMP)
        stor = api.get_property_value(WPMProperties.SPEICHERISTTEMP)

        if flow: print(f"Flow temperature:    {flow:.1f}°C")
        if ret:  print(f"Return temperature:  {ret:.1f}°C")
        if stor: print(f"Storage temperature: {stor:.1f}°C")

        print("\n✓ CAN bus API is working!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Verify CAN interface is up: ip link show can0")
        print("2. Check CAN traffic: candump can0")
        print("3. Verify connections: CAN_H, CAN_L, GND")
        print("4. Check bitrate is 20000 (20 kbit/s)")

    finally:
        api.stop_listening()
        await api.async_close()
        print("\nDisconnected from CAN bus")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
chmod +x test_can.py
python3 test_can.py
```

## Step 5: Common Use Cases

### Read Current Temperatures

```python
async def read_temps():
    async with WPMCanAPI('can0', 'socketcan') as api:
        api.start_listening()

        await api.async_update([
            WPMProperties.AUSSENTEMP,
            WPMProperties.VORLAUFISTTEMP,
            WPMProperties.RAUMISTTEMP,
        ])

        await asyncio.sleep(1)

        print(f"Outside: {api.get_property_value(WPMProperties.AUSSENTEMP):.1f}°C")
        print(f"Flow:    {api.get_property_value(WPMProperties.VORLAUFISTTEMP):.1f}°C")
        print(f"Room:    {api.get_property_value(WPMProperties.RAUMISTTEMP):.1f}°C")
```

### Set Comfort Temperature

```python
async def set_comfort_temp(temp):
    async with WPMCanAPI('can0', 'socketcan') as api:
        api.start_listening()

        # Write new temperature
        await api.async_write_property(WPMProperties.KOMFORTTEMPERATUR, temp)
        print(f"Set comfort temperature to {temp}°C")

        # Verify
        await asyncio.sleep(1)
        await api.async_request_property(WPMProperties.KOMFORTTEMPERATUR)
        await asyncio.sleep(0.5)

        verified = api.get_property_value(WPMProperties.KOMFORTTEMPERATUR)
        print(f"Verified: {verified:.1f}°C")
```

### Monitor in Real-time

```python
async def monitor():
    async with WPMCanAPI('can0', 'socketcan') as api:
        def on_change(prop_id, raw_value):
            if prop_id == WPMProperties.AUSSENTEMP.id:
                value = api._convert_value_from_raw(raw_value, PropertyType.DEC_VAL)
                print(f"Outside temp changed: {value:.1f}°C")

        api.register_callback(WPMProperties.AUSSENTEMP.id, on_change)
        api.start_listening()

        # Keep requesting updates
        while True:
            await api.async_request_property(WPMProperties.AUSSENTEMP)
            await asyncio.sleep(10)
```

## Troubleshooting

### "Network is down"
```bash
sudo ip link set can0 up
```

### "Permission denied"
```bash
sudo usermod -a -G dialout $USER
# Log out and back in
```

### No messages received
1. Check candump: `candump can0`
2. Verify connections (CAN_H, CAN_L, GND)
3. Check termination resistors (120Ω)
4. Verify bitrate: 20 kbit/s

### Wrong values
- Different heat pump models use different property IDs
- Check the OneESP32ToRuleThemAll project for your model
- Use candump to see raw messages and verify IDs

## Next Steps

1. Explore more properties in `WPMProperties`
2. Read the full documentation: [CAN_API_README.md](CAN_API_README.md)
3. Check out examples: [wpm-can-example.py](wpm-can-example.py)
4. Integrate with your home automation system

## Safety Reminder

⚠️ **Important:**
- Test carefully before production use
- Monitor your heat pump after changes
- Keep the original controller connected
- Have a way to restore original settings
- Follow local regulations

## Getting Help

- Check the documentation: [CAN_API_README.md](CAN_API_README.md)
- Review examples: [wpm-can-example.py](wpm-can-example.py)
- Create an issue on GitHub
- Check the OneESP32ToRuleThemAll project for model-specific info

---

**Congratulations!** 🎉 You're now up and running with the CAN bus API!
