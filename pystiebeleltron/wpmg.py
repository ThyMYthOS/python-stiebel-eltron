"""Modbus api for stiebel eltron heat pumps. This file is generated. Do not modify it manually."""

from __future__ import annotations

from modbus_connection import ModbusUnit
from modbus_connection.model import Component, gauge

from . import UNAVAILABLE
from ._components import ControllerComponents

WPMG_INPUT_RANGES = ((6020, 6021), (6023, 6024), (6099, 6100))


class WpmGSystemValues(Component):
    register_space = "input"
    register_ranges = WPMG_INPUT_RANGES

    brine_inlet_temperature = gauge(6020, 0.01, nan=UNAVAILABLE, unit="°C")
    brine_outlet_temperature = gauge(6021, 0.01, nan=UNAVAILABLE, unit="°C")
    condenser_inlet_temperature = gauge(6023, 0.01, nan=UNAVAILABLE, unit="°C")
    condenser_outlet_temperature = gauge(6024, 0.01, nan=UNAVAILABLE, unit="°C")
    outside_temperature_averaged = gauge(6099, 0.01, nan=UNAVAILABLE, unit="°C")
    dhw_temperature_weighted = gauge(6100, 0.01, nan=UNAVAILABLE, unit="°C")


class WpmGStiebelEltronAPI:
    """Stiebel Eltron heat pump API over a modbus_connection ModbusUnit."""

    def __init__(self, unit: ModbusUnit) -> None:
        self.system_values = WpmGSystemValues(unit)
        self._group = ControllerComponents(
            unit,
            required=[
                self.system_values,
            ],
        )

    async def async_update(self) -> None:
        """Read every component the controller serves, in one poll."""
        await self._group.async_update()
