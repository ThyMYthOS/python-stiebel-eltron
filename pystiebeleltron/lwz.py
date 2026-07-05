"""Modbus api for stiebel eltron heat pumps. This file is generated. Do not modify it manually."""

from __future__ import annotations

from enum import Enum

from modbus_connection import ModbusUnit
from modbus_connection.model import Component, ComponentGroup, gauge, integer

from . import UNAVAILABLE, EnergyManagementSettings, EnergySystemInformation, in_range, scaled_sum

LWZ_HOLDING_RANGES = ((1000, 1026), (4000, 4002))
LWZ_INPUT_RANGES = ((0, 33), (2000, 2004), (3000, 3031), (5000, 5001))


class OperatingMode(Enum):
    """Enum for the operation mode of the heat pump."""

    AUTOMATIC = 11  # AUTOMATIK
    STANDBY = 1  # BEREITSCHAFT
    DAY_MODE = 3  # TAGBETRIEB
    SETBACK_MODE = 4  # ABSENKBETRIEB
    DHW = 5  # WARMWASSER
    MANUAL_MODE = 14  # HANDBETRIEB
    EMERGENCY_OPERATION = 0  # NOTBETRIEB


class LwzSystemValues(Component):
    register_space = "input"
    register_ranges = LWZ_INPUT_RANGES

    actual_room_t_hc1 = gauge(0, 0.1, nan=UNAVAILABLE, unit="°C")
    set_room_temperature_hc1 = gauge(1, 0.1, nan=UNAVAILABLE, unit="°C")
    relative_humidity_hc1 = gauge(2, 0.1, nan=UNAVAILABLE, unit="%")
    actual_room_t_hc2 = gauge(3, 0.1, nan=UNAVAILABLE, unit="°C")
    set_room_temperature_hc2 = gauge(4, 0.1, nan=UNAVAILABLE, unit="°C")
    relative_humidity_hc2 = gauge(5, 0.1, nan=UNAVAILABLE, unit="%")
    outside_temperature = gauge(6, 0.1, nan=UNAVAILABLE, unit="°C")
    actual_value_hc1 = gauge(7, 0.1, nan=UNAVAILABLE, unit="°C")
    set_value_hc1 = gauge(8, 0.1, nan=UNAVAILABLE, unit="°C")
    actual_value_hc2 = gauge(9, 0.1, nan=UNAVAILABLE, unit="°C")
    set_value_hc2 = gauge(10, 0.1, nan=UNAVAILABLE, unit="°C")
    flow_temperature = gauge(11, 0.1, nan=UNAVAILABLE, unit="°C")
    return_temperature = gauge(12, 0.1, nan=UNAVAILABLE, unit="°C")
    pressure_htg_circ = gauge(13, 0.1, nan=UNAVAILABLE, unit="bar")
    flow_rate = gauge(14, 0.1, nan=UNAVAILABLE, unit="l/min")
    actual_dhw_t = gauge(15, 0.1, nan=UNAVAILABLE, unit="°C")
    dhw_set_temperature = gauge(16, 0.1, nan=UNAVAILABLE, unit="°C")
    ventilation_air_actual_fan_speed = integer(17, signed=False, nan=UNAVAILABLE, unit="Hz")
    ventilation_air_set_flow_rate = integer(18, signed=False, nan=UNAVAILABLE, unit="m³/h")
    extract_air_actual_fan_speed = integer(19, signed=False, nan=UNAVAILABLE, unit="Hz")
    extract_air_set_flow_rate = integer(20, signed=False, nan=UNAVAILABLE, unit="m³/h")
    extract_air_humidity = integer(21, signed=False, nan=UNAVAILABLE, unit="%")
    extract_air_temp = gauge(22, 0.1, nan=UNAVAILABLE, unit="°C")
    extract_air_dew_point = gauge(23, 0.1, nan=UNAVAILABLE, unit="°C")
    dew_point_temp_hc1 = gauge(24, 0.1, nan=UNAVAILABLE, unit="°C")
    dew_point_temp_hc2 = gauge(25, 0.1, nan=UNAVAILABLE, unit="°C")
    collector_temperature = gauge(26, 0.1, nan=UNAVAILABLE, unit="°C")
    hot_gas_temperature = gauge(27, 0.1, nan=UNAVAILABLE, unit="°C")
    high_pressure = gauge(28, 0.01, nan=UNAVAILABLE, unit="bar")
    low_pressure = gauge(29, 0.01, nan=UNAVAILABLE, unit="bar")
    compressor_starts_hi = integer(30, signed=False, nan=UNAVAILABLE)
    compressor_speed = gauge(31, 0.1, nan=UNAVAILABLE, unit="Hz")
    mixed_water_amount = integer(32, signed=False, nan=UNAVAILABLE, unit="l")
    compressor_starts_low = integer(33, signed=False, nan=UNAVAILABLE)

    @property
    def compressor_starts(self) -> int | None:
        """Total compressor starts, combined from the HI/LOW registers."""
        high = self.compressor_starts_hi
        if high is None:
            return None
        low = self.compressor_starts_low
        return high * 1000 + (low or 0)


class LwzSystemParameters(Component):
    register_space = "holding"
    register_ranges = LWZ_HOLDING_RANGES

    operating_mode = integer(1000, signed=False, nan=UNAVAILABLE, writable=in_range(0, 14))
    room_temperature_day_hk1 = gauge(1001, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(10, 30))
    room_temperature_night_hk1 = gauge(1002, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(10, 30))
    manual_hc_set_hk1 = gauge(1003, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(10, 65))
    room_temperature_day_hk2 = gauge(1004, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(10, 30))
    room_temperature_night_hk2 = gauge(1005, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(10, 30))
    manual_hc_set_hk2 = gauge(1006, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(10, 65))
    gradient_hk1 = gauge(1007, 0.01, nan=UNAVAILABLE, writable=in_range(0, 5))
    low_end_hk1 = gauge(1008, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(0, 20))
    gradient_hk2 = gauge(1009, 0.01, nan=UNAVAILABLE, writable=in_range(0, 5))
    low_end_hk2 = gauge(1010, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(0, 20))
    dhw_set_day = gauge(1011, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(10, 55))
    dhw_set_night = gauge(1012, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(10, 55))
    dhw_set_manual = gauge(1013, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(10, 65))
    mwm_set_day = integer(1014, signed=False, nan=UNAVAILABLE, unit="l", writable=in_range(50, 288))
    mwm_set_night = integer(1015, signed=False, nan=UNAVAILABLE, unit="l", writable=in_range(50, 288))
    mwm_set_manual = integer(1016, signed=False, nan=UNAVAILABLE, unit="l", writable=in_range(50, 288))
    day_stage = integer(1017, signed=False, nan=UNAVAILABLE, writable=in_range(0, 3))
    night_stage = integer(1018, signed=False, nan=UNAVAILABLE, writable=in_range(0, 3))
    party_stage = integer(1019, signed=False, nan=UNAVAILABLE, writable=in_range(0, 3))
    manual_stage = integer(1020, signed=False, nan=UNAVAILABLE, writable=in_range(0, 3))
    room_temperature_day_hk1_cooling = gauge(1021, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(10, 30))
    room_temperature_night_hk1_cooling = gauge(1022, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(10, 30))
    room_temperature_day_hk2_cooling = gauge(1023, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(10, 30))
    room_temperature_night_hk2_cooling = gauge(1024, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(10, 30))
    reset = integer(1025, signed=False, nan=UNAVAILABLE, writable=in_range(0, 1))
    restart_isg = integer(1026, signed=False, nan=UNAVAILABLE, writable=in_range(0, 2))


class LwzSystemState(Component):
    register_space = "input"
    register_ranges = LWZ_INPUT_RANGES

    operating_status = integer(2000, signed=False, nan=UNAVAILABLE)
    fault_status = integer(2001, signed=False, nan=UNAVAILABLE)
    bus_status = integer(2002, signed=False, nan=UNAVAILABLE)
    defrost_initiated = integer(2003, signed=False, nan=UNAVAILABLE)
    operating_status_2 = integer(2004, signed=False, nan=UNAVAILABLE)


class LwzEnergyData(Component):
    register_space = "input"
    register_ranges = LWZ_INPUT_RANGES

    heat_meter_htg_day = integer(3000, signed=False, nan=UNAVAILABLE, unit="kWh")
    heat_meter_htg_ttl = scaled_sum(3001, (1, 1000), unit="kWh")
    heat_meter_dhw_day = integer(3003, signed=False, nan=UNAVAILABLE, unit="kWh")
    heat_meter_dhw_ttl = scaled_sum(3004, (1, 1000), unit="kWh")
    heat_m_boost_htg_ttl = scaled_sum(3006, (1, 1000), unit="kWh")
    heat_m_boost_dhw_ttl = scaled_sum(3008, (1, 1000), unit="kWh")
    heat_m_recovery_day = integer(3010, signed=False, nan=UNAVAILABLE, unit="kWh")
    heat_m_recovery_ttl = scaled_sum(3011, (1, 1000), unit="kWh")
    hm_solar_htg_day = integer(3013, signed=False, nan=UNAVAILABLE, unit="kWh")
    hm_solar_htg_total = scaled_sum(3014, (1, 1000), unit="kWh")
    hm_solar_dhw_day = integer(3016, signed=False, nan=UNAVAILABLE, unit="kWh")
    hm_solar_dwh_total = scaled_sum(3017, (1, 1000), unit="kWh")
    hm_cooling_total = scaled_sum(3019, (1, 1000), unit="kWh")
    pwr_con_htg_day = integer(3021, signed=False, nan=UNAVAILABLE, unit="kWh")
    pwr_con_htg_ttl = scaled_sum(3022, (1, 1000), unit="kWh")
    pwr_con_dhw_day = integer(3024, signed=False, nan=UNAVAILABLE, unit="kWh")
    pwr_con_dhw_ttl = scaled_sum(3025, (1, 1000), unit="kWh")
    compressor_heating = integer(3027, signed=False, nan=UNAVAILABLE, unit="h")
    compressor_cooling = integer(3028, signed=False, nan=UNAVAILABLE, unit="h")
    compressor_dhw = integer(3029, signed=False, nan=UNAVAILABLE, unit="h")
    elec_booster_heating = integer(3030, signed=False, nan=UNAVAILABLE, unit="h")
    elec_booster_dhw = integer(3031, signed=False, nan=UNAVAILABLE, unit="h")

    _DAY_AND_TOTAL = (
        ("heat_meter_htg_day", "heat_meter_htg_ttl", "heat_meter_htg_day_and_total"),
        ("heat_meter_dhw_day", "heat_meter_dhw_ttl", "heat_meter_dhw_day_and_total"),
        ("heat_m_recovery_day", "heat_m_recovery_ttl", "heat_m_recovery_day_and_total"),
        ("hm_solar_htg_day", "hm_solar_htg_total", "hm_solar_htg_day_and_total"),
        ("hm_solar_dhw_day", "hm_solar_dwh_total", "hm_solar_dhw_day_and_total"),
        ("pwr_con_htg_day", "pwr_con_htg_ttl", "pwr_con_htg_day_and_total"),
        ("pwr_con_dhw_day", "pwr_con_dhw_ttl", "pwr_con_dhw_day_and_total"),
    )

    def __init__(self, unit: ModbusUnit, index: int = 1) -> None:
        super().__init__(unit, index)
        self._running_totals: dict[str, int] = {}

    def notify(self) -> None:
        """Refresh the monotonic day-and-total counters, then notify listeners."""
        for day_attr, total_attr, key in self._DAY_AND_TOTAL:
            day = getattr(self, day_attr)
            total = getattr(self, total_attr)
            if day is not None and total is not None:
                combined = day + total
                previous = self._running_totals.get(key)
                self._running_totals[key] = combined if previous is None else max(combined, previous)
        super().notify()

    @property
    def heat_meter_htg_day_and_total(self) -> int | None:
        return self._running_totals.get("heat_meter_htg_day_and_total")

    @property
    def heat_meter_dhw_day_and_total(self) -> int | None:
        return self._running_totals.get("heat_meter_dhw_day_and_total")

    @property
    def heat_m_recovery_day_and_total(self) -> int | None:
        return self._running_totals.get("heat_m_recovery_day_and_total")

    @property
    def hm_solar_htg_day_and_total(self) -> int | None:
        return self._running_totals.get("hm_solar_htg_day_and_total")

    @property
    def hm_solar_dhw_day_and_total(self) -> int | None:
        return self._running_totals.get("hm_solar_dhw_day_and_total")

    @property
    def pwr_con_htg_day_and_total(self) -> int | None:
        return self._running_totals.get("pwr_con_htg_day_and_total")

    @property
    def pwr_con_dhw_day_and_total(self) -> int | None:
        return self._running_totals.get("pwr_con_dhw_day_and_total")


class LwzStiebelEltronAPI:
    """Stiebel Eltron heat pump API over a modbus_connection ModbusUnit."""

    def __init__(self, unit: ModbusUnit) -> None:
        self.system_values = LwzSystemValues(unit)
        self.system_parameters = LwzSystemParameters(unit)
        self.system_state = LwzSystemState(unit)
        self.energy_data = LwzEnergyData(unit)
        self.energy_management_settings = EnergyManagementSettings(unit)
        self.energy_management_settings.register_ranges = LWZ_HOLDING_RANGES
        self.energy_system_information = EnergySystemInformation(unit)
        self.energy_system_information.register_ranges = LWZ_INPUT_RANGES
        self._group = ComponentGroup(
            unit,
            [
                self.system_values,
                self.system_parameters,
                self.system_state,
                self.energy_data,
                self.energy_management_settings,
                self.energy_system_information,
            ],
        )

    async def async_update(self) -> None:
        """Read every component in one pooled set of block reads."""
        await self._group.async_update()

    def get_current_temp(self) -> float | None:
        """Get the current room temperature."""
        return self.system_values.actual_room_t_hc1

    def get_target_temp(self) -> float | None:
        """Get the target room temperature."""
        return self.system_parameters.room_temperature_day_hk1

    async def set_target_temp(self, temp: float) -> None:
        """Set the target room temperature (day)(HC1)."""
        await self.system_parameters.write("room_temperature_day_hk1", temp)

    def get_current_humidity(self) -> float | None:
        """Get the current room humidity."""
        return self.system_values.relative_humidity_hc1

    def get_operation(self) -> OperatingMode:
        """Return the current mode of operation."""
        op_mode = self.system_parameters.operating_mode
        if op_mode is None:
            return OperatingMode.EMERGENCY_OPERATION
        return OperatingMode(int(op_mode))

    async def set_operation(self, mode: OperatingMode) -> None:
        """Set the operation mode."""
        await self.system_parameters.write("operating_mode", mode.value)

    def get_heating_status(self) -> bool:
        """Return heater status."""
        value = self.system_state.operating_status
        if value is None:
            return False
        return bool(int(value) & (1 << 2))

    def get_cooling_status(self) -> bool:
        """Cooling status."""
        value = self.system_state.operating_status
        if value is None:
            return False
        return bool(int(value) & (1 << 3))

    def get_filter_alarm_status(self) -> bool:
        """Return filter alarm."""
        value = self.system_state.operating_status
        if value is None:
            return False
        filter_mask = (1 << 8) | (1 << 12) | (1 << 13)
        return bool(int(value) & filter_mask)
