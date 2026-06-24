#!/usr/bin/env python3
import asyncio

from modbus_connection.pymodbus import connect_tcp

from pystiebeleltron.wpm import WpmStiebelEltronAPI

host_ip = "192.168.1.20"
host_port = 502
device_id = 1


async def main():
    connection = await connect_tcp(host_ip, port=host_port)
    api = WpmStiebelEltronAPI(connection.for_unit(device_id))

    await api.async_update()

    outside_temp = api.system_values.outside_temperature
    print(f"The current outside temperature is {outside_temp} °C")

    comfort_temp = api.system_parameters.comfort_temperature
    print(f"The current water comfort temperature is {comfort_temp} °C")

    # Write the water comfort temperature, then read it back.
    print("Setting temperature to 50.0")
    await api.system_parameters.write("comfort_temperature", 50)
    await asyncio.sleep(3)
    await api.async_update()
    mod_temp = api.system_parameters.comfort_temperature
    if mod_temp != 50.0:
        print("setting the water comfort temperature failed!")
    if mod_temp != comfort_temp:
        await api.system_parameters.write("comfort_temperature", comfort_temp)
        await asyncio.sleep(3)
        await api.async_update()
    print(f"comfort_temperature: {api.system_parameters.comfort_temperature}")
    await connection.close()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(main())
