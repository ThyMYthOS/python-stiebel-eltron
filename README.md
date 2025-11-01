<p align=center>
    <img src="https://www.stiebel-eltron.de/content/dam/ste/logo-stiebel-eltron.svg"/>
</p>
<p align=center>
    <a href="https://pypi.org/project/pystiebeleltron/"><img src="https://img.shields.io/pypi/v/pystiebeleltron.svg"/></a>
    <a href="https://github.com/ThyMYthOS/python-stiebel-eltron/actions/workflows/test-python-package.yml"><img src="https://github.com/ThyMYthOS/python-stiebel-eltron/actions/workflows/test-python-package.yml/badge.svg"/></a>
    <!--a href='https://coveralls.io/github/fucm/python-stiebel-eltron?branch=master'><img src='https://coveralls.io/repos/github/fucm/python-stiebel-eltron/badge.svg?branch=master' alt='Coverage Status' /></a>
  <img src="https://img.shields.io/github/license/ThyMYthOS/python-stiebel-eltron.svg"/></a Maybe use https://github.com/marketplace/actions/coverage-badge-->
</p>

# python-stiebel-eltron
Python API for interacting with STIEBEL ELTRON heat pumps and ventilation units via Modbus TCP or CAN bus.

This module is based on the STIEBEL ELTRON [modbus user manual](https://www.stiebel-eltron.ch/content/dam/ste/ch/de/downloads/kundenservice/smart-home/Modbus/Modbus%20Bedienungsanleitung.pdf), but is not official, developed, supported or endorsed by Stiebel Eltron GmbH & Co. KG. For questions and other inquiries, use the issue tracker in this repo please.

## Communication Protocols

This library supports two communication methods:

1. **Modbus TCP** - Via ISG web gateway (requires ISG hardware)
2. **CAN Bus** - Direct CAN bus communication (requires CAN interface) - **NEW!**

## Requirements
You need to have [Python](https://www.python.org) installed.

### For Modbus TCP (via ISG):
* STIEBEL ELTRON Internet-Service Gateway [ISG WEB](https://www.stiebel-eltron.com/en/home/products-solutions/renewables/controller_energymanagement/internet_servicegateway/isg_web.html) with enabled [modbus module](https://www.stiebel-eltron.ch/de/home/service/smart-home/modbus.html)
  * You can call the STIEBEL ELTRON support, if your ISG does not have the modbus module enabled. They upgraded mine for free.
* STIEBEL ELTRON heat pump (compatible). Successfully used devices:
  * LWZ504e
  * LWZ304
* Network connection to the ISG WEB

### For CAN Bus:
* CAN bus interface (USB-CAN adapter, SPI module like MCP2515, etc.)
* Physical connection to heat pump's CAN bus
* `python-can` library
* See [CAN_API_README.md](CAN_API_README.md) for detailed setup instructions

## Installation
The package is available in the [Python Package Index](https://pypi.python.org/).

Base install:

```bash
# For Modbus TCP support only
$ pip install pystiebeleltron

# For CAN bus support (includes python-can)
$ pip install pystiebeleltron python-can
```

Install with the optional `tmodbus` backend used in the example below:

```bash
    $ pip install "pystiebeleltron[tmodbus]"
```

## Example usage of the module
The [`examples/`](examples/) directory contains runnable examples for WPM and LWZ heat pumps. They use the optional `tmodbus` backend, so install `pystiebeleltron[tmodbus]` first.

The API takes a [`ModbusUnit`](https://github.com/home-assistant-libs/modbus-connection). You own the connection: build it, hand a unit to the API, and close it when done. Building it performs no I/O — the first read establishes the link, and a link that drops later is re-established on the next request, over the same unit handle. Each register block is a component exposed on the API, and values are read as typed attributes (`None` when the register is unavailable).

Pass the IP address of the ISG gateway to the selected example:

```bash
./examples/wpm-example.py 192.168.1.10
./examples/lwz-example.py 192.168.1.10
```

The WPM example also demonstrates writing and restoring the DHW comfort temperature. The LWZ example reads room and outside temperatures and the current operating mode.

## Example usage of the module

### Using CAN Bus (NEW!)
The sample below shows how to use the CAN bus API for direct communication with WPM heat pumps.

```python
import asyncio
from pystiebeleltron.wpm_can import WPMCanAPI, WPMProperties

async def main():
    api = WPMCanAPI(
        channel='can0',  # Your CAN interface
        bustype='socketcan',
        bitrate=20000
    )

    try:
        await api.async_connect()
        api.start_listening()

        # Request outside temperature
        await api.async_request_property(WPMProperties.AUSSENTEMP)
        await asyncio.sleep(0.5)

        temp = api.get_property_value(WPMProperties.AUSSENTEMP)
        print(f"Outside temperature: {temp:.1f}°C")

        # Set comfort temperature
        await api.async_write_property(WPMProperties.KOMFORTTEMPERATUR, 21.5)

    finally:
        api.stop_listening()
        await api.async_close()

asyncio.run(main())
```

For more CAN bus examples and documentation, see [CAN_API_README.md](CAN_API_README.md) and [wpm-can-example.py](wpm-can-example.py).

### Using Modbus TCP (via ISG)
The sample below shows how to use the Modbus API for WPM heat pumps.

```python
import asyncio
from pystiebeleltron.wpm import WpmStiebelEltronAPI, WpmSystemParametersRegisters

async def main():
    api = WpmStiebelEltronAPI('IP_ADDRESS_ISG')
    await api.connect()

    await api.async_update()

    print("water comfort target temperature: {}".format(
        api.get_register_value(WpmSystemParametersRegisters.COMFORT_TEMPERATURE)
    ))

    await api.close()

asyncio.run(main())
```

### Using Modbus TCP - LWZ API (legacy)
The sample below shows how to use this Python module (old API for LWZ heat pumps).

```python
from pystiebeleltron import pystiebeleltron as pyse
from pymodbus.client.sync import ModbusTcpClient as ModbusClient

client = ModbusClient(host='IP_ADDRESS_ISG', port=502, timeout=2)
client.connect()

unit = pyse.StiebelEltronAPI(client, 1)
unit.update()

print("get_target_temp: {}".format(unit.get_target_temp))

client.close()
```

## Additional Documentation

- **[CAN_API_README.md](CAN_API_README.md)** - Comprehensive guide for CAN bus API
- **[wpm-can-example.py](wpm-can-example.py)** - Detailed examples for CAN bus usage
- **[wpm-example.py](wpm-example.py)** - Examples for Modbus TCP WPM API

## License

``python-stiebel-eltron`` is licensed under MIT, for more details check LICENSE.
