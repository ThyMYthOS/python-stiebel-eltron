#!/usr/bin/env python3
"""Example script demonstrating the CAN bus API for Stiebel Eltron WPM.

This example shows how to:
1. Connect to a CAN bus interface
2. Request property values from the heat pump
3. Write property values to the heat pump
4. Monitor property changes in real-time

Requirements:
- python-can library: pip install python-can
- CAN interface (e.g., SocketCAN on Linux, PCAN on Windows)

For testing on Linux without hardware:
    sudo modprobe vcan
    sudo ip link add dev vcan0 type vcan
    sudo ip link set up vcan0
"""

import argparse
import asyncio
import logging

from pystiebeleltron.wpm_can import (
    CANMember,
    WPMCanAPI,
    WPMProperties,
)

_LOGGER = logging.getLogger(__name__)


async def example_basic_usage(interface: str, channel: str) -> None:
    """Example of basic usage - request and read values."""
    _LOGGER.info("=== Example 1: Basic Usage ===")

    # Create API instance
    api = WPMCanAPI(
        channel=channel,
        interface=interface,
    )

    try:
        # Connect to CAN bus
        await api.connect()

        # Start listening for responses
        await api.start_listening()

        # Request some properties
        _LOGGER.info("Requesting outside temperature...")
        await api.request_property(WPMProperties.AUSSENTEMP)

        # Wait for response
        await asyncio.sleep(0.5)

        # Get the value
        outside_temp = api.get_property_value(WPMProperties.AUSSENTEMP)
        if outside_temp is not None:
            _LOGGER.info(f"Outside temperature: {outside_temp:.1f}°C")
        else:
            _LOGGER.info("Outside temperature: No data received")

        # Request multiple properties
        _LOGGER.info("Requesting multiple properties...")
        await api.update([
            WPMProperties.SPEICHERISTTEMP,
            WPMProperties.SPEICHERSOLLTEMP,
            WPMProperties.HEIZUNGSDRUCK,
            WPMProperties.VOLUMENSTROM,
            WPMProperties.RAUMTEMP_ERFASSUNG
        ], member=CANMember.KESSEL)

        # Wait for responses
        await asyncio.sleep(2)

        # Display results
        _LOGGER.info("--- Current Values ---")

        properties_to_display = [
            (WPMProperties.AUSSENTEMP, "Outside Temperature", "°C"),
            #(WPMProperties.VORLAUFISTTEMP, "Flow Temperature", "°C"),
            #(WPMProperties.RUECKLAUFISTTEMP, "Return Temperature", "°C"),
            (WPMProperties.SPEICHERISTTEMP, "Storage Temperature", "°C"),
            (WPMProperties.SPEICHERSOLLTEMP, "Storage Setpoint", "°C"),
            #(WPMProperties.RAUMISTTEMP, "Room Temperature", "°C"),
            (WPMProperties.HEIZUNGSDRUCK, "Heating Pressure", "bar"),
            (WPMProperties.VOLUMENSTROM, "Flow Rate", "l/min"),
            (WPMProperties.RAUMTEMP_ERFASSUNG, "Room Temp. Sensor", "?"),
        ]

        for prop, name, unit in properties_to_display:
            value = api.get_property_value(prop)
            if value is not None:
                _LOGGER.info(f"{name:25s}: {value:7.2f} {unit}")
            else:
                _LOGGER.info(f"{name:25s}: No data")

    finally:
        # Cleanup
        await api.stop_listening()
        await api.close()


async def example_write_values(interface: str, channel: str) -> None:
    """Example of writing values to the heat pump."""
    _LOGGER.info("=== Example 2: Writing Values ===")

    api = WPMCanAPI(channel=channel, interface=interface)

    try:
        await api.connect()
        await api.start_listening()

        # Read current room temperature
        _LOGGER.info("Reading current room temperature...")
        await api.request_property(WPMProperties.RAUMISTTEMP, CANMember.HK1)
        await asyncio.sleep(0.5)

        current_temp = api.get_property_value(WPMProperties.RAUMISTTEMP)
        if current_temp is not None:
            _LOGGER.info(f"Current room temperature: {current_temp:.1f}°C")

            # Write new value
            new_temp = 21.5
            _LOGGER.info(f"Setting actual room temperature to {new_temp:.1f}°C...")
            await api.write_property(WPMProperties.RAUMISTTEMP, new_temp, CANMember.HK1)

            # Wait and verify
            await asyncio.sleep(2)
            await api.request_property(WPMProperties.RAUMISTTEMP, CANMember.HK1)
            await asyncio.sleep(0.5)

            verified_temp = api.get_property_value(WPMProperties.RAUMISTTEMP)
            if verified_temp is not None:
                _LOGGER.info(f"Verified temperature: {verified_temp:.1f}°C")
        else:
            _LOGGER.info("Could not read current temperature")

    finally:
        await api.stop_listening()
        await api.close()


async def example_monitoring(interface: str, channel: str) -> None:
    """Example of monitoring property changes in real-time."""
    _LOGGER.info("=== Example 3: Real-time Monitoring ===")

    api = WPMCanAPI(channel=channel, interface=interface)

    # Define callback for property updates
    def on_temperature_update(prop_id: int, raw_value: int) -> None:
        # Find the property
        for name, prop in WPMProperties.__dict__.items():
            if hasattr(prop, 'id') and prop.id == prop_id:
                value = prop.deserialize(raw_value)
                _LOGGER.info(f"Property updated: {name} = {value}")
                break

    try:
        await api.connect()

        # Register callbacks for temperature properties
        api.register_callback(WPMProperties.AUSSENTEMP.id, on_temperature_update)
        api.register_callback(WPMProperties.VORLAUFISTTEMP.id, on_temperature_update)
        api.register_callback(WPMProperties.RAUMISTTEMP.id, on_temperature_update)

        await api.start_listening()

        _LOGGER.info("Monitoring temperature changes for 30 seconds...")
        _LOGGER.info("Press Ctrl+C to stop\n")

        # Periodically request updates
        for _i in range(10):
            await api.update([
                WPMProperties.RUECKLAUFISTTEMP,
                WPMProperties.VORLAUFISTTEMP,
                WPMProperties.RAUMISTTEMP,
            ], member=CANMember.HK1)
            await asyncio.sleep(3)

    except KeyboardInterrupt:
        _LOGGER.info("Stopped by user")
    finally:
        await api.stop_listening()
        await api.close()


async def example_energy_monitoring(interface: str, channel: str) -> None:
    """Example of monitoring energy consumption."""
    _LOGGER.info("=== Example 4: Energy Monitoring ===")

    api = WPMCanAPI(channel=channel, interface=interface)

    try:
        await api.connect()
        await api.start_listening()

        # Request energy consumption data
        energy_properties = [
            WPMProperties.EL_ENERGIEAUFNAHME_WW_TAG_WH,
            WPMProperties.EL_ENERGIEAUFNAHME_WW_TAG_KWH,
            WPMProperties.EL_ENERGIEAUFNAHME_HEIZ_TAG_WH,
            WPMProperties.EL_ENERGIEAUFNAHME_HEIZ_TAG_KWH,
            WPMProperties.WAERMEERTRAG_WW_TAG_WH,
            WPMProperties.WAERMEERTRAG_WW_TAG_KWH,
            WPMProperties.WAERMEERTRAG_HEIZ_TAG_WH,
            WPMProperties.WAERMEERTRAG_HEIZ_TAG_KWH,
        ]

        _LOGGER.info("Requesting energy consumption data...")
        for prop in energy_properties:
            await api.request_property(prop)
            await asyncio.sleep(0.1)

        # Wait for responses
        await asyncio.sleep(2)

        # Display results
        _LOGGER.info("--- Energy Consumption (Today) ---")

        dhw_consumed_wh = api.get_property_value(WPMProperties.EL_ENERGIEAUFNAHME_WW_TAG_WH)
        dhw_consumed_kwh = api.get_property_value(WPMProperties.EL_ENERGIEAUFNAHME_WW_TAG_KWH)
        heating_consumed_wh = api.get_property_value(WPMProperties.EL_ENERGIEAUFNAHME_HEIZ_TAG_WH)
        heating_consumed_kwh = api.get_property_value(WPMProperties.EL_ENERGIEAUFNAHME_HEIZ_TAG_KWH)

        dhw_produced_wh = api.get_property_value(WPMProperties.WAERMEERTRAG_WW_TAG_WH)
        dhw_produced_kwh = api.get_property_value(WPMProperties.WAERMEERTRAG_WW_TAG_KWH)
        heating_produced_wh = api.get_property_value(WPMProperties.WAERMEERTRAG_HEIZ_TAG_WH)
        heating_produced_kwh = api.get_property_value(WPMProperties.WAERMEERTRAG_HEIZ_TAG_KWH)

        _LOGGER.info("Domestic Hot Water (DHW):")
        if dhw_consumed_wh is not None and dhw_consumed_kwh is not None:
            dhw_consumed_wh += dhw_consumed_kwh * 1000
            _LOGGER.info(f"  Energy consumed: {dhw_consumed_wh} Wh")
        if dhw_produced_wh is not None and dhw_produced_kwh is not None:
            dhw_produced_wh += dhw_produced_kwh * 1000
            _LOGGER.info(f"  Heat produced:   {dhw_produced_wh} Wh")
        if dhw_consumed_wh and dhw_produced_wh:
            cop = dhw_produced_wh / dhw_consumed_wh if dhw_consumed_wh > 0 else 0
            _LOGGER.info(f"  COP:             {cop:.2f}")

        _LOGGER.info("Heating:")
        if heating_consumed_wh is not None and heating_consumed_kwh is not None:
            heating_consumed_wh += heating_consumed_kwh * 1000
            _LOGGER.info(f"  Energy consumed: {heating_consumed_wh} Wh")
        if heating_produced_wh is not None and heating_produced_kwh is not None:
            heating_produced_wh += heating_produced_kwh * 1000
            _LOGGER.info(f"  Heat produced:   {heating_produced_wh} Wh")
        if heating_consumed_wh and heating_produced_wh:
            cop = heating_produced_wh / heating_consumed_wh if heating_consumed_wh > 0 else 0
            _LOGGER.info(f"  COP:             {cop:.2f}")

    finally:
        await api.stop_listening()
        await api.close()


async def example_context_manager(interface: str, channel: str) -> None:
    """Example using context manager."""
    _LOGGER.info("=== Example 5: Using Async Context Manager ===")

    # Using async context manager for automatic cleanup
    async with WPMCanAPI(channel=channel, interface=interface) as api:
        # Request and display outside temperature
        await api.request_property(WPMProperties.AUSSENTEMP)
        await asyncio.sleep(0.5)

        temp = api.get_property_value(WPMProperties.AUSSENTEMP)
        if temp is not None:
            _LOGGER.info(f"Outside temperature: {temp:.1f}°C")


async def main(interface: str, channel: str) -> None:
    """Run all examples."""
    print("=" * 60)
    print("Stiebel Eltron WPM CAN Bus API Examples")
    print("=" * 60)
    print()
    print(f"Using CAN interface: {interface} (channel: {channel})")
    print()

    try:
        # Run examples one by one
        await example_basic_usage(interface, channel)
        await example_write_values(interface, channel)
        await example_monitoring(interface, channel)
        await example_energy_monitoring(interface, channel)
        await example_context_manager(interface, channel)

    except Exception as e:
        _LOGGER.error(f"Error running examples: {e}", exc_info=True)

    print()
    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Stiebel Eltron WPM CAN Bus API Examples",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use virtual CAN interface (for testing without hardware)
  %(prog)s --channel vcan0

  # Use real hardware CAN interface
  %(prog)s --channel can0

  # Use PCAN USB adapter
  %(prog)s --channel PCAN_USBBUS1 --interface pcan

  # Enable debug logging
  %(prog)s --channel vcan0 --log-level DEBUG
"""
    )

    parser.add_argument(
        '--channel',
        type=str,
        default='vcan0',
        help='CAN channel name (default: vcan0)'
    )

    parser.add_argument(
        '--interface',
        type=str,
        default='socketcan',
        help='CAN bus type (default: socketcan)'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO)'
    )

    args = parser.parse_args()

    # Configure logging with the specified level
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(main(args.interface, args.channel))
