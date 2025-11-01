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

import asyncio
import logging

from pystiebeleltron.wpm_can import (
    WPMCanAPI,
    WPMProperties,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

_LOGGER = logging.getLogger(__name__)


async def example_basic_usage() -> None:
    """Example of basic usage - request and read values."""
    _LOGGER.info("=== Example 1: Basic Usage ===")

    # Create API instance
    # For real hardware, use 'can0' or your actual CAN interface
    # For testing with virtual CAN, use 'vcan0'
    api = WPMCanAPI(
        interface='vcan0',  # Change to 'can0' for real hardware
        bustype='socketcan',
        bitrate=20000,  # Stiebel Eltron uses 20 kbit/s
    )

    try:
        # Connect to CAN bus
        await api.async_connect()

        # Start listening for responses
        api.start_listening()

        # Request some properties
        _LOGGER.info("Requesting outside temperature...")
        await api.async_request_property(WPMProperties.AUSSENTEMP)

        # Wait for response
        await asyncio.sleep(0.5)

        # Get the value
        outside_temp = api.get_property_value(WPMProperties.AUSSENTEMP)
        if outside_temp is not None:
            _LOGGER.info(f"Outside temperature: {outside_temp:.1f}°C")
        else:
            _LOGGER.info("Outside temperature: No data received")

        # Request multiple properties
        _LOGGER.info("\nRequesting multiple properties...")
        await api.async_update()

        # Wait for responses
        await asyncio.sleep(2)

        # Display results
        _LOGGER.info("\n--- Current Values ---")

        properties_to_display = [
            (WPMProperties.AUSSENTEMP, "Outside Temperature", "°C"),
            (WPMProperties.VORLAUFISTTEMP, "Flow Temperature", "°C"),
            (WPMProperties.RUECKLAUFISTTEMP, "Return Temperature", "°C"),
            (WPMProperties.SPEICHERISTTEMP, "Storage Temperature", "°C"),
            (WPMProperties.RAUMISTTEMP, "Room Temperature", "°C"),
            (WPMProperties.HEIZUNGSDRUCK, "Heating Pressure", "bar"),
            (WPMProperties.VOLUMENSTROM, "Flow Rate", "l/min"),
        ]

        for prop, name, unit in properties_to_display:
            value = api.get_property_value(prop)
            if value is not None:
                _LOGGER.info(f"{name:25s}: {value:7.2f} {unit}")
            else:
                _LOGGER.info(f"{name:25s}: No data")

    finally:
        # Cleanup
        api.stop_listening()
        await api.async_close()


async def example_write_values() -> None:
    """Example of writing values to the heat pump."""
    _LOGGER.info("\n=== Example 2: Writing Values ===")

    api = WPMCanAPI(interface='vcan0', bustype='socketcan')

    try:
        await api.async_connect()
        api.start_listening()

        # Read current comfort temperature
        _LOGGER.info("Reading current comfort temperature...")
        await api.async_request_property(WPMProperties.KOMFORTTEMPERATUR)
        await asyncio.sleep(0.5)

        current_temp = api.get_property_value(WPMProperties.KOMFORTTEMPERATUR)
        if current_temp is not None:
            _LOGGER.info(f"Current comfort temperature: {current_temp:.1f}°C")

            # Write new value
            new_temp = 21.5
            _LOGGER.info(f"Setting comfort temperature to {new_temp:.1f}°C...")
            await api.async_write_property(WPMProperties.KOMFORTTEMPERATUR, new_temp)

            # Wait and verify
            await asyncio.sleep(2)
            await api.async_request_property(WPMProperties.KOMFORTTEMPERATUR)
            await asyncio.sleep(0.5)

            verified_temp = api.get_property_value(WPMProperties.KOMFORTTEMPERATUR)
            if verified_temp is not None:
                _LOGGER.info(f"Verified temperature: {verified_temp:.1f}°C")

                # Restore original value
                _LOGGER.info(f"Restoring original temperature: {current_temp:.1f}°C...")
                await api.async_write_property(WPMProperties.KOMFORTTEMPERATUR, current_temp)
        else:
            _LOGGER.info("Could not read current temperature")

    finally:
        api.stop_listening()
        await api.async_close()


async def example_monitoring() -> None:
    """Example of monitoring property changes in real-time."""
    _LOGGER.info("\n=== Example 3: Real-time Monitoring ===")

    api = WPMCanAPI(interface='vcan0', bustype='socketcan')

    # Define callback for property updates
    def on_temperature_update(prop_id: int, raw_value: int) -> None:
        # Find the property
        for name, prop in WPMProperties.__dict__.items():
            if hasattr(prop, 'id') and prop.id == prop_id:
                value = api._convert_value_from_raw(raw_value, prop.type)
                _LOGGER.info(f"Property updated: {name} = {value}")
                break

    try:
        await api.async_connect()

        # Register callbacks for temperature properties
        api.register_callback(WPMProperties.AUSSENTEMP.id, on_temperature_update)
        api.register_callback(WPMProperties.VORLAUFISTTEMP.id, on_temperature_update)
        api.register_callback(WPMProperties.RAUMISTTEMP.id, on_temperature_update)

        api.start_listening()

        _LOGGER.info("Monitoring temperature changes for 30 seconds...")
        _LOGGER.info("Press Ctrl+C to stop\n")

        # Periodically request updates
        for _i in range(10):
            await api.async_update([
                WPMProperties.AUSSENTEMP,
                WPMProperties.VORLAUFISTTEMP,
                WPMProperties.RAUMISTTEMP,
            ])
            await asyncio.sleep(3)

    except KeyboardInterrupt:
        _LOGGER.info("\nStopped by user")
    finally:
        api.stop_listening()
        await api.async_close()


async def example_energy_monitoring() -> None:
    """Example of monitoring energy consumption."""
    _LOGGER.info("\n=== Example 4: Energy Monitoring ===")

    api = WPMCanAPI(interface='vcan0', bustype='socketcan')

    try:
        await api.async_connect()
        api.start_listening()

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
            await api.async_request_property(prop)
            await asyncio.sleep(0.1)

        # Wait for responses
        await asyncio.sleep(2)

        # Display results
        _LOGGER.info("\n--- Energy Consumption (Today) ---")

        dhw_consumed_wh = api.get_property_value(WPMProperties.EL_ENERGIEAUFNAHME_WW_TAG_WH)
        dhw_consumed_kwh = api.get_property_value(WPMProperties.EL_ENERGIEAUFNAHME_WW_TAG_KWH)
        heating_consumed_wh = api.get_property_value(WPMProperties.EL_ENERGIEAUFNAHME_HEIZ_TAG_WH)
        heating_consumed_kwh = api.get_property_value(WPMProperties.EL_ENERGIEAUFNAHME_HEIZ_TAG_KWH)

        dhw_produced_wh = api.get_property_value(WPMProperties.WAERMEERTRAG_WW_TAG_WH)
        dhw_produced_kwh = api.get_property_value(WPMProperties.WAERMEERTRAG_WW_TAG_KWH)
        heating_produced_wh = api.get_property_value(WPMProperties.WAERMEERTRAG_HEIZ_TAG_WH)
        heating_produced_kwh = api.get_property_value(WPMProperties.WAERMEERTRAG_HEIZ_TAG_KWH)

        _LOGGER.info("\nDomestic Hot Water (DHW):")
        if dhw_consumed_wh is not None:
            _LOGGER.info(f"  Energy consumed: {dhw_consumed_wh} Wh ({dhw_consumed_kwh:.2f} kWh)")
        if dhw_produced_wh is not None:
            _LOGGER.info(f"  Heat produced:   {dhw_produced_wh} Wh ({dhw_produced_kwh:.2f} kWh)")
        if dhw_consumed_wh and dhw_produced_wh:
            cop = dhw_produced_wh / dhw_consumed_wh if dhw_consumed_wh > 0 else 0
            _LOGGER.info(f"  COP:             {cop:.2f}")

        _LOGGER.info("\nHeating:")
        if heating_consumed_wh is not None:
            _LOGGER.info(f"  Energy consumed: {heating_consumed_wh} Wh ({heating_consumed_kwh:.2f} kWh)")
        if heating_produced_wh is not None:
            _LOGGER.info(f"  Heat produced:   {heating_produced_wh} Wh ({heating_produced_kwh:.2f} kWh)")
        if heating_consumed_wh and heating_produced_wh:
            cop = heating_produced_wh / heating_consumed_wh if heating_consumed_wh > 0 else 0
            _LOGGER.info(f"  COP:             {cop:.2f}")

    finally:
        api.stop_listening()
        await api.async_close()


async def example_context_manager() -> None:
    """Example using context manager."""
    _LOGGER.info("\n=== Example 5: Using Context Manager ===")

    # Using context manager for automatic cleanup
    with WPMCanAPI(interface='vcan0', bustype='socketcan') as api:
        api.start_listening()

        # Request and display outside temperature
        await api.async_request_property(WPMProperties.AUSSENTEMP)
        await asyncio.sleep(0.5)

        temp = api.get_property_value(WPMProperties.AUSSENTEMP)
        if temp is not None:
            _LOGGER.info(f"Outside temperature: {temp:.1f}°C")


async def main() -> None:
    """Run all examples."""
    print("=" * 60)
    print("Stiebel Eltron WPM CAN Bus API Examples")
    print("=" * 60)
    print()
    print("Note: These examples use 'vcan0' virtual CAN interface.")
    print("For real hardware, change 'vcan0' to your actual interface (e.g., 'can0')")
    print()

    try:
        # Run examples one by one
        await example_basic_usage()
        await example_write_values()
        await example_monitoring()
        await example_energy_monitoring()
        await example_context_manager()

    except Exception as e:
        _LOGGER.error(f"Error running examples: {e}", exc_info=True)

    print()
    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
