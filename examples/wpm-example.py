#!/usr/bin/env python3
"""Example that uses the optional tmodbus backend.

For the development environment, initialize and sync with uv:
``uv sync --all-extras``.
"""

import argparse
import asyncio

from modbus_connection import ModbusTcpParams
from modbus_connection.tmodbus import ModbusConnection

from pystiebeleltron.wpm import WpmStiebelEltronAPI

host_port = 502
device_id = 1


async def main(host_ip: str) -> None:
    connection = ModbusConnection(ModbusTcpParams(host=host_ip, port=host_port))
    try:
        api = WpmStiebelEltronAPI(connection.for_unit(device_id))

        await api.async_update()

        outside_temp = api.system_values.outside_temperature
        print(f"The current outside temperature is {outside_temp} °C")

        comfort_temp = api.system_parameters.comfort_temperature_dhw
        print(f"The current water comfort temperature is {comfort_temp} °C")

        # Write the water comfort temperature, read it back, then restore it.
        if comfort_temp is None or comfort_temp == 50.0:
            print("Skipping the write demo: no previous value to restore, or it is 50.0 already")
            return
        print("Setting temperature to 50.0")
        try:
            # Inside the try: a write whose answer is lost raises although the
            # ISG may have taken the value, and then the restore must still run.
            await api.system_parameters.write("comfort_temperature_dhw", 50)
            await asyncio.sleep(3)
            await api.async_update()
            if api.system_parameters.comfort_temperature_dhw != 50.0:
                print("setting the water comfort temperature failed!")
        finally:
            # Restore the setpoint even when the read-back failed, so a demo
            # never leaves the heat pump on a value its owner did not choose.
            await api.system_parameters.write("comfort_temperature_dhw", comfort_temp)
        await asyncio.sleep(3)
        await api.async_update()
        print(f"comfort_temperature_dhw: {api.system_parameters.comfort_temperature_dhw}")
    finally:
        await connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read values from a WPM heat pump.")
    parser.add_argument("host_ip", help="IP address of the ISG gateway")
    args = parser.parse_args()
    asyncio.run(main(args.host_ip))
