#!/usr/bin/env python3
import asyncio
from pystiebeleltron.wpm import WpmStiebelEltronAPI, WpmSystemParametersRegisters, WpmSystemValuesRegisters

host_ip = "192.168.1.20"


async def main():
    api = WpmStiebelEltronAPI(host_ip, 502)
    await api.connect()

    await api.async_update()

    for k, v in api._data.items():
        if v is not None:
            print(f"{k.name} ({k.value}): {v}")

    outside_temp = api.get_register_value(WpmSystemValuesRegisters.OUTSIDE_TEMPERATURE)
    print(f"The current outside temperature is {outside_temp} °C")

    comfort_temp = api.get_register_value(WpmSystemParametersRegisters.COMFORT_TEMPERATURE)
    print(f"The current water comfort temperature is {comfort_temp} °C")

    # Test set_target_temp
    print("Setting temperature to 50.0")
    await api.write_register_value(WpmSystemParametersRegisters.COMFORT_TEMPERATURE, 50)
    await asyncio.sleep(3)
    await api.async_update()
    mod_temp = api.get_register_value(WpmSystemParametersRegisters.COMFORT_TEMPERATURE)
    if mod_temp != 50.0:
        print("setting the water comfort temperature failed!")
    if mod_temp != comfort_temp:
        await api.write_register_value(WpmSystemParametersRegisters.COMFORT_TEMPERATURE, comfort_temp)
        await asyncio.sleep(3)
        await api.async_update()
    print(f"get_target_temp: {api.get_register_value(WpmSystemParametersRegisters.COMFORT_TEMPERATURE)}")
    await api.close()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(main())
