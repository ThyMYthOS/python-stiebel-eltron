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
Python API for interacting with the STIEBEL ELTRON ISG web gateway via modbus for controlling integral ventilation units and heat pumps.

This module is based on the STIEBEL ELTRON [modbus user manual](https://www.stiebel-eltron.ch/content/dam/ste/ch/de/downloads/kundenservice/smart-home/Modbus/Modbus%20Bedienungsanleitung.pdf), but is not official, developed, supported or endorsed by Stiebel Eltron GmbH & Co. KG. For questions and other inquiries, use the issue tracker in this repo please.

## Requirements
You need to have [Python](https://www.python.org) installed.

* STIEBEL ELTRON Internet-Service Gateway [ISG WEB](https://www.stiebel-eltron.com/en/home/products-solutions/renewables/controller_energymanagement/internet_servicegateway/isg_web.html) with enabled [modbus module](https://www.stiebel-eltron.ch/de/home/service/smart-home/modbus.html)
  * You can call the STIEBEL ELTRON support, if your ISG does not have the modbus module enabled. They upgraded mine for free.
* STIEBEL ELTRON heatpumpt (compatible). Successfully used devices:
  * LWZ504e
  * LWZ304
* Network connection to the ISG WEB

## Installation
The package is available in the [Python Package Index](https://pypi.python.org/).

Base install:

```bash
    $ pip install pystiebeleltron
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

## License

``python-stiebel-eltron`` is licensed under MIT, for more details check LICENSE.

### Experimental ISG WPM G

`pystiebeleltron.wpmg.WpmGStiebelEltronAPI(unit)` exposes six read-only
primary-pump temperatures under `api.system_values`. Call `await api.async_update()`
to read them. This API requires an explicitly selected ISG-backed WPM G; it does
not extend `get_controller_model()` and does not support a direct Genesis endpoint.

The FC04 wire addresses are 6020, 6021, 6023, 6024, 6099 and 6100 (ISG chapter 9
references 36021, 36022, 36024, 36025, 36100 and 36101). Signed values use a 0.01 °C
scale and `0x8000` means unavailable. Only the three adjacent pairs are polled.
No holding registers, secondary units or write operations are provided.

The initial capture and display comparisons are documented in
[the WPM G alpha notes](https://github.com/Optic00/stiebel_eltron_isg_component/blob/2026.9-wpmg-alpha2/docs/wpmg-alpha-test.md).
The condenser inlet/outlet labels still require confirmation against the device's
flow/return labels. Successful reads alone do not establish automatic detection.
