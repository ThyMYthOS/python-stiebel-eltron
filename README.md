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

`pystiebeleltron.wpmg.WpmGStiebelEltronAPI(unit)` exposes 149 read-only primary
fields under `system_values`, `system_state` and `alarms`: 55 numeric values and
94 boolean status/alarm values. Call `await api.async_update()` to read them.
Select this API explicitly for an ISG-backed WPM G. It does not extend
`get_controller_model()` or support a direct Genesis endpoint.

The mapping follows chapter 9 of the
[ISG Modbus manual](https://www.stiebel-eltron.com.au/download/1685919441_321798-44755-9770_ISG%20Modbus_en.pdf).
The CSV sources retain the printed primary addresses; wire addresses subtract
one. Scales and signed types follow the documented register format. `0x8000`
means unavailable; booleans accept only 0 and 1. Adjacent declared addresses are
read in FC04 blocks, without polling gaps or providing writes.

Code 2 block rejections are split within a bounded exploration budget. Rejected
single words decode as unavailable, while valid neighbours continue updating.
They are re-probed after five minutes; `retry_failed_registers()` makes them
eligible on the next poll. Learned splits support gateways with shorter block
limits. Transport, busy, protocol errors and the 20-second poll timeout still
propagate. The `polling_report` property exposes raw words, current failure
reasons and bounded per-address history without connection identifiers.
At most 149 normal requests and 32 exploratory requests occur in one poll;
a healthy device needs eleven. The state belongs to this API instance only.

Fourteen addresses remain excluded: room temperature (36000), counters
(36035–36036, 36050–36055, 36121), comfort (36122), dew point (36123), and
compressor stages/speed (37701–37702). The capture and manual disagree on scaling,
word ordering or boolean meaning; no substitute interpretation is assumed.

A diagnostic capture returned all 163 documented primary input registers on one
installation. This supports the read path, not every physical value or state
transition. The original six temperature attributes retain their names; the
condenser inlet/outlet correspondence to display labels still needs confirmation.
Secondary units and holding registers are outside this API.
