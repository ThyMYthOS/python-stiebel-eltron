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

For a read-only WPM library check outside Home Assistant, use `examples/wpm-readonly-check.py` in a separate virtual environment. Select `--family wpm`, `wpm3` or `wpm3i`, and pass `--confirm-read-only`. It performs one poll by default (`--polls` accepts at most three); `--raw` exercises raw reads without printing register values. The output contains package versions, a retry-module fingerprint and request outcomes, excluding host addresses and register values. The wrapper permits only input and holding reads and rejects all write operations. This checks the library, not Home Assistant compatibility.

WPM API polls retry an illegal-address input or holding read at most once from a lower start answered directly in the same register space and poll, when the expanded read fits within 125 registers. Healthy reads and writes are unchanged; LWZ does not opt in. A rejected block costs one failed original request and at most one additional read on every poll. A successful retry does not establish that the target registers exist; unavailable words still decode as `None`.

## License

``python-stiebel-eltron`` is licensed under MIT, for more details check LICENSE.
