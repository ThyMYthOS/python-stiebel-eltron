"""Modbus api for stiebel eltron heat pumps. This file is generated. Do not modify it manually."""

from __future__ import annotations

from modbus_connection import ModbusUnit
from modbus_connection.model import Component, boolean, gauge, integer, repeating_group

from . import UNAVAILABLE, in_range, scaled_sum
from ._components import ControllerComponents

WPM3_HOLDING_RANGES = ((1500, 1520), (4000, 4002))
WPM3_INPUT_RANGES = ((500, 507), (509, 537), (541, 582), (2500, 2506), (3500, 3515), (3522, 3642), (5000, 5001))


class Wpm3HeatPumpModule(Component):
    """One repeated sub-unit; instance i is read at ``base_offset = i * stride``."""

    register_space = "input"

    return_temperature = gauge(541, 0.1, nan=UNAVAILABLE, unit="°C")
    flow_temperature = gauge(542, 0.1, nan=UNAVAILABLE, unit="°C")
    hot_gas_temperature = gauge(543, 0.1, nan=UNAVAILABLE, unit="°C")
    low_pressure = gauge(544, 0.01, nan=UNAVAILABLE, unit="bar")
    mean_pressure = gauge(545, 0.01, nan=UNAVAILABLE, unit="bar")
    high_pressure = gauge(546, 0.01, nan=UNAVAILABLE, unit="bar")
    wp_water_flow_rate = gauge(547, 0.1, nan=UNAVAILABLE, unit="l/min")


class Wpm3SystemValues(Component):
    register_space = "input"
    register_ranges = WPM3_INPUT_RANGES

    actual_temperature_fe7 = gauge(500, 0.1, nan=UNAVAILABLE, unit="°C")
    set_temperature_fe7 = gauge(501, 0.1, nan=UNAVAILABLE, unit="°C")
    actual_temperature_fek = gauge(502, 0.1, nan=UNAVAILABLE, unit="°C")
    set_temperature_fek = gauge(503, 0.1, nan=UNAVAILABLE, unit="°C")
    relative_humidity = gauge(504, 0.1, nan=UNAVAILABLE, unit="%")
    dew_point_temperature = gauge(505, 0.1, nan=UNAVAILABLE, unit="°C")
    outside_temperature = gauge(506, 0.1, nan=UNAVAILABLE, unit="°C")
    actual_temperature_hk_1 = gauge(507, 0.1, nan=UNAVAILABLE, unit="°C")
    set_temperature_hk_1 = gauge(509, 0.1, nan=UNAVAILABLE, unit="°C")
    actual_temperature_hk_2 = gauge(510, 0.1, nan=UNAVAILABLE, unit="°C")
    set_temperature_hk_2 = gauge(511, 0.1, nan=UNAVAILABLE, unit="°C")
    actual_flow_temperature_wp = gauge(512, 0.1, nan=UNAVAILABLE, unit="°C")
    actual_flow_temperature_nhz = gauge(513, 0.1, nan=UNAVAILABLE, unit="°C")
    actual_flow_temperature = gauge(514, 0.1, nan=UNAVAILABLE, unit="°C")
    actual_return_temperature = gauge(515, 0.1, nan=UNAVAILABLE, unit="°C")
    set_fixed_temperature = gauge(516, 0.1, nan=UNAVAILABLE, unit="°C")
    actual_buffer_temperature = gauge(517, 0.1, nan=UNAVAILABLE, unit="°C")
    set_buffer_temperature = gauge(518, 0.1, nan=UNAVAILABLE, unit="°C")
    heating_pressure = gauge(519, 0.01, nan=UNAVAILABLE, unit="bar")
    flow_rate = gauge(520, 0.01, nan=UNAVAILABLE, unit="l/min")
    actual_temperature_dhw = gauge(521, 0.1, nan=UNAVAILABLE, unit="°C")
    set_temperature_dhw = gauge(522, 0.1, nan=UNAVAILABLE, unit="°C")
    actual_temperature_fan = gauge(523, 0.1, nan=UNAVAILABLE, unit="K")
    set_temperature_fan = gauge(524, 0.1, nan=UNAVAILABLE, unit="K")
    actual_temperature_area = gauge(525, 0.1, nan=UNAVAILABLE, unit="K")
    set_temperature_area = gauge(526, 0.1, nan=UNAVAILABLE, unit="K")
    collector_temperature = gauge(527, 0.1, nan=UNAVAILABLE, unit="°C")
    cylinder_temperature = gauge(528, 0.1, nan=UNAVAILABLE, unit="°C")
    runtime = integer(529, signed=False, nan=UNAVAILABLE, unit="h")
    actual_temperature_external = gauge(530, 0.1, nan=UNAVAILABLE, unit="°C")
    set_temperature_external = gauge(531, 0.1, nan=UNAVAILABLE, unit="K")
    application_limit_hzg = gauge(532, 0.1, nan=UNAVAILABLE, unit="°C")
    application_limit_ww = gauge(533, 0.1, nan=UNAVAILABLE, unit="°C")
    runtime_ehs = integer(534, signed=False, nan=UNAVAILABLE, unit="h")
    source_temperature = gauge(535, 0.1, nan=UNAVAILABLE, unit="°C")
    min_source_temperature = gauge(536, 0.1, nan=UNAVAILABLE, unit="°C")
    source_pressure = gauge(537, 0.01, nan=UNAVAILABLE, unit="bar")
    heat_pumps = repeating_group(6, Wpm3HeatPumpModule, stride=7)


class Wpm3SystemParameters(Component):
    register_space = "holding"
    register_ranges = WPM3_HOLDING_RANGES

    operating_mode = integer(1500, signed=False, nan=UNAVAILABLE, writable=in_range(0, 5))
    comfort_temperature_hk_1 = gauge(1501, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(5, 30))
    eco_temperature_hk_1 = gauge(1502, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(5, 30))
    heating_curve_rise_hk_1 = gauge(1503, 0.01, nan=UNAVAILABLE, writable=in_range(0, 3))
    comfort_temperature_hk_2 = gauge(1504, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(5, 30))
    eco_temperature_hk_2 = gauge(1505, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(5, 30))
    heating_curve_rise_hk_2 = gauge(1506, 0.01, nan=UNAVAILABLE, writable=in_range(0, 3))
    fixed_value_operation = gauge(1507, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(20, 70))
    dual_mode_temp_hzg = gauge(1508, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(-40, 40))
    comfort_temperature_dhw = gauge(1509, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(10, 60))
    eco_temperature_dhw = gauge(1510, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(10, 60))
    dhw_stages = integer(1511, signed=False, nan=UNAVAILABLE, writable=in_range(0, 6))
    dual_mode_temp_ww = gauge(1512, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(-40, 40))
    set_flow_temperature_area = gauge(1513, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(7, 25))
    flow_temp_hysteresis_area = gauge(1514, 0.1, nan=UNAVAILABLE, unit="K", writable=in_range(1, 5))
    set_room_temperature_area = gauge(1515, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(20, 30))
    set_flow_temperature_fan = gauge(1516, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(7, 25))
    flow_temp_hysteresis_fan = gauge(1517, 0.1, nan=UNAVAILABLE, unit="K", writable=in_range(1, 5))
    set_room_temperature_fan = gauge(1518, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(20, 30))
    reset = integer(1519, signed=False, nan=UNAVAILABLE, writable=in_range(1, 3))
    restart_isg = integer(1520, signed=False, nan=UNAVAILABLE, writable=in_range(0, 2))


class Wpm3SystemState(Component):
    register_space = "input"
    register_ranges = WPM3_INPUT_RANGES

    operating_status = integer(2500, signed=False, nan=UNAVAILABLE)
    power_off = integer(2501, signed=False, nan=UNAVAILABLE)
    operating_status_wpm_3 = integer(2502, signed=False, nan=UNAVAILABLE)
    fault_status = boolean(2503, nan=UNAVAILABLE)
    bus_status = integer(2504, signed=False, nan=UNAVAILABLE)
    defrost_initiated = boolean(2505, nan=UNAVAILABLE)
    active_error = integer(2506, signed=False, nan=UNAVAILABLE)


class Wpm3EnergyData(Component):
    register_space = "input"
    register_ranges = WPM3_INPUT_RANGES

    vd_heating_day = integer(3500, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_heating_total = scaled_sum(3501, (1, 1000), unit="kWh")
    vd_dhw_day = integer(3503, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_dhw_total = scaled_sum(3504, (1, 1000), unit="kWh")
    nhz_heating_total = scaled_sum(3506, (1, 1000), unit="kWh")
    nhz_dhw_total = scaled_sum(3508, (1, 1000), unit="kWh")
    vd_heating_day_consumed = integer(3510, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_heating_total_consumed = scaled_sum(3511, (1, 1000), unit="kWh")
    vd_dhw_day_consumed = integer(3513, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_dhw_total_consumed = scaled_sum(3514, (1, 1000), unit="kWh")
    vd_heating_day_hp_1 = integer(3522, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_heating_total_hp_1 = scaled_sum(3523, (1, 1000), unit="kWh")
    vd_dhw_day_hp_1 = integer(3525, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_dhw_total_hp_1 = scaled_sum(3526, (1, 1000), unit="kWh")
    nhz_heating_total_hp_1 = scaled_sum(3528, (1, 1000), unit="kWh")
    nhz_dhw_total_hp_1 = scaled_sum(3530, (1, 1000), unit="kWh")
    vd_heating_day_consumed_hp_1 = integer(3532, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_heating_total_consumed_hp_1 = scaled_sum(3533, (1, 1000), unit="kWh")
    vd_dhw_day_consumedhp_1 = integer(3535, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_dhw_total_consumed_hp_1 = scaled_sum(3536, (1, 1000), unit="kWh")
    vd_1_heating_hp_1 = integer(3538, signed=False, nan=UNAVAILABLE, unit="h")
    vd_2_heating_hp_1 = integer(3539, signed=False, nan=UNAVAILABLE, unit="h")
    vd_1_2_heating_hp_1 = integer(3540, signed=False, nan=UNAVAILABLE, unit="h")
    vd_1_dhw_hp_1 = integer(3541, signed=False, nan=UNAVAILABLE, unit="h")
    vd_2_dhw_hp_1 = integer(3542, signed=False, nan=UNAVAILABLE, unit="h")
    vd_1_2_dhw_hp_1 = integer(3543, signed=False, nan=UNAVAILABLE, unit="h")
    vd_cooling_x_hp_1 = integer(3544, signed=False, nan=UNAVAILABLE, unit="h")
    nhz_1_reheating = integer(3545, signed=False, nan=UNAVAILABLE, unit="h")
    nhz_2_reheating = integer(3546, signed=False, nan=UNAVAILABLE, unit="h")
    nhz_1_2_reheating = integer(3547, signed=False, nan=UNAVAILABLE, unit="h")
    vd_heating_day_hp_2 = integer(3548, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_heating_total_hp_2 = scaled_sum(3549, (1, 1000), unit="kWh")
    vd_dhw_day_hp_2 = integer(3551, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_dhw_total_hp_2 = scaled_sum(3552, (1, 1000), unit="kWh")
    vd_heating_day_consumed_hp_2 = integer(3554, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_heating_total_consumed_hp_2 = scaled_sum(3555, (1, 1000), unit="kWh")
    vd_dhw_day_consumed_hp_2 = integer(3557, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_dhw_total_consumed_hp_2 = scaled_sum(3558, (1, 1000), unit="kWh")
    vd_1_heating_hp_2 = integer(3560, signed=False, nan=UNAVAILABLE, unit="h")
    vd_2_heating_hp_2 = integer(3561, signed=False, nan=UNAVAILABLE, unit="h")
    vd_1_2_heating_hp_2 = integer(3562, signed=False, nan=UNAVAILABLE, unit="h")
    vd_1_dhw_hp_2 = integer(3563, signed=False, nan=UNAVAILABLE, unit="h")
    vd_2_dhw_hp_2 = integer(3564, signed=False, nan=UNAVAILABLE, unit="h")
    vd_1_2_dhw_hp_2 = integer(3565, signed=False, nan=UNAVAILABLE, unit="h")
    vd_cooling_hp_2 = integer(3566, signed=False, nan=UNAVAILABLE, unit="h")
    vd_heating_day_hp_3 = integer(3567, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_heating_total_hp_3 = scaled_sum(3568, (1, 1000), unit="kWh")
    vd_dhw_day_hp_3 = integer(3570, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_dhw_total_hp_3 = scaled_sum(3571, (1, 1000), unit="kWh")
    vd_heating_day_consumed_hp_3 = integer(3573, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_heating_total_consumed_hp_3 = scaled_sum(3574, (1, 1000), unit="kWh")
    vd_dhw_day_consumed_hp_3 = integer(3576, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_dhw_total_consumed_hp_3 = scaled_sum(3577, (1, 1000), unit="kWh")
    vd_1_heating_hp_3 = integer(3579, signed=False, nan=UNAVAILABLE, unit="h")
    vd_2_heating_hp_3 = integer(3580, signed=False, nan=UNAVAILABLE, unit="h")
    vd_1_2_heating_hp_3 = integer(3581, signed=False, nan=UNAVAILABLE, unit="h")
    vd_1_dhw_hp_3 = integer(3582, signed=False, nan=UNAVAILABLE, unit="h")
    vd_2_dhw_hp_3 = integer(3583, signed=False, nan=UNAVAILABLE, unit="h")
    vd_1_2_dhw_hp_3 = integer(3584, signed=False, nan=UNAVAILABLE, unit="h")
    vd_cooling_hp_3 = integer(3585, signed=False, nan=UNAVAILABLE, unit="h")
    vd_heating_day_hp_4 = integer(3586, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_heating_total_hp_4 = scaled_sum(3587, (1, 1000), unit="kWh")
    vd_dhw_day_hp_4 = integer(3589, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_dhw_total_hp_4 = scaled_sum(3590, (1, 1000), unit="kWh")
    vd_heating_day_consumed_hp_4 = integer(3592, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_heating_total_consumed_hp_4 = scaled_sum(3593, (1, 1000), unit="kWh")
    vd_dhw_day_consumed_hp_4 = integer(3595, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_dhw_total_consumed_hp_4 = scaled_sum(3596, (1, 1000), unit="kWh")
    vd_1_heating_hp_4 = integer(3598, signed=False, nan=UNAVAILABLE, unit="h")
    vd_2_heating_hp_4 = integer(3599, signed=False, nan=UNAVAILABLE, unit="h")
    vd_1_2_heating_hp_4 = integer(3600, signed=False, nan=UNAVAILABLE, unit="h")
    vd_1_dhw_hp_4 = integer(3601, signed=False, nan=UNAVAILABLE, unit="h")
    vd_2_dhw_hp_4 = integer(3602, signed=False, nan=UNAVAILABLE, unit="h")
    vd_1_2_dhw_hp_4 = integer(3603, signed=False, nan=UNAVAILABLE, unit="h")
    vd_cooling_hp_4 = integer(3604, signed=False, nan=UNAVAILABLE, unit="h")
    vd_heating_day_hp_5 = integer(3605, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_heating_total_hp_5 = scaled_sum(3606, (1, 1000), unit="kWh")
    vd_dhw_day_hp_5 = integer(3608, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_dhw_total_hp_5 = scaled_sum(3609, (1, 1000), unit="kWh")
    vd_heating_day_consumed_hp_5 = integer(3611, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_heating_total_consumed_hp_5 = scaled_sum(3612, (1, 1000), unit="kWh")
    vd_dhw_day_consumed_hp_5 = integer(3614, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_dhw_total_consumed_hp_5 = scaled_sum(3615, (1, 1000), unit="kWh")
    vd_1_heating_hp_5 = integer(3617, signed=False, nan=UNAVAILABLE, unit="h")
    vd_2_heating_hp_5 = integer(3618, signed=False, nan=UNAVAILABLE, unit="h")
    vd_1_2_heating_hp_5 = integer(3619, signed=False, nan=UNAVAILABLE, unit="h")
    vd_1_dhw_hp_5 = integer(3620, signed=False, nan=UNAVAILABLE, unit="h")
    vd_2_dhw_hp_5 = integer(3621, signed=False, nan=UNAVAILABLE, unit="h")
    vd_1_2_dhw_hp_5 = integer(3622, signed=False, nan=UNAVAILABLE, unit="h")
    vd_cooling_hp_5 = integer(3623, signed=False, nan=UNAVAILABLE, unit="h")
    vd_heating_day_hp_6 = integer(3624, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_heating_total_hp_6 = scaled_sum(3625, (1, 1000), unit="kWh")
    vd_dhw_day_hp_6 = integer(3627, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_dhw_total_hp_6 = scaled_sum(3628, (1, 1000), unit="kWh")
    vd_heating_day_consumed_hp_6 = integer(3630, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_heating_total_consumed_hp_6 = scaled_sum(3631, (1, 1000), unit="kWh")
    vd_dhw_day_consumed_hp_6 = integer(3633, signed=False, nan=UNAVAILABLE, unit="kWh")
    vd_dhw_total_consumed_hp_6 = scaled_sum(3634, (1, 1000), unit="kWh")
    vd_1_heating_hp_6 = integer(3636, signed=False, nan=UNAVAILABLE, unit="h")
    vd_2_heating_hp_6 = integer(3637, signed=False, nan=UNAVAILABLE, unit="h")
    vd_1_2_heating_hp_6 = integer(3638, signed=False, nan=UNAVAILABLE, unit="h")
    vd_1_dhw_hp_6 = integer(3639, signed=False, nan=UNAVAILABLE, unit="h")
    vd_2_dhw_hp_6 = integer(3640, signed=False, nan=UNAVAILABLE, unit="h")
    vd_1_2_dhw_hp_6 = integer(3641, signed=False, nan=UNAVAILABLE, unit="h")
    vd_cooling_hp_6 = integer(3642, signed=False, nan=UNAVAILABLE, unit="h")

    _DAY_AND_TOTAL = (
        ("vd_heating_day", "vd_heating_total", "vd_heating_day_and_total"),
        ("vd_dhw_day", "vd_dhw_total", "vd_dhw_day_and_total"),
        ("vd_heating_day_consumed", "vd_heating_total_consumed", "vd_heating_day_and_total_consumed"),
        ("vd_dhw_day_consumed", "vd_dhw_total_consumed", "vd_dhw_day_and_total_consumed"),
        ("vd_heating_day_hp_1", "vd_heating_total_hp_1", "vd_heating_day_and_total_hp_1"),
        ("vd_dhw_day_hp_1", "vd_dhw_total_hp_1", "vd_dhw_day_and_total_hp_1"),
        ("vd_heating_day_consumed_hp_1", "vd_heating_total_consumed_hp_1", "vd_heating_day_and_total_consumed_hp_1"),
        ("vd_dhw_day_consumedhp_1", "vd_dhw_total_consumed_hp_1", "vd_dhw_day_and_total_consumedhp_1"),
        ("vd_heating_day_hp_2", "vd_heating_total_hp_2", "vd_heating_day_and_total_hp_2"),
        ("vd_dhw_day_hp_2", "vd_dhw_total_hp_2", "vd_dhw_day_and_total_hp_2"),
        ("vd_heating_day_consumed_hp_2", "vd_heating_total_consumed_hp_2", "vd_heating_day_and_total_consumed_hp_2"),
        ("vd_dhw_day_consumed_hp_2", "vd_dhw_total_consumed_hp_2", "vd_dhw_day_and_total_consumed_hp_2"),
        ("vd_heating_day_hp_3", "vd_heating_total_hp_3", "vd_heating_day_and_total_hp_3"),
        ("vd_dhw_day_hp_3", "vd_dhw_total_hp_3", "vd_dhw_day_and_total_hp_3"),
        ("vd_heating_day_consumed_hp_3", "vd_heating_total_consumed_hp_3", "vd_heating_day_and_total_consumed_hp_3"),
        ("vd_dhw_day_consumed_hp_3", "vd_dhw_total_consumed_hp_3", "vd_dhw_day_and_total_consumed_hp_3"),
        ("vd_heating_day_hp_4", "vd_heating_total_hp_4", "vd_heating_day_and_total_hp_4"),
        ("vd_dhw_day_hp_4", "vd_dhw_total_hp_4", "vd_dhw_day_and_total_hp_4"),
        ("vd_heating_day_consumed_hp_4", "vd_heating_total_consumed_hp_4", "vd_heating_day_and_total_consumed_hp_4"),
        ("vd_dhw_day_consumed_hp_4", "vd_dhw_total_consumed_hp_4", "vd_dhw_day_and_total_consumed_hp_4"),
        ("vd_heating_day_hp_5", "vd_heating_total_hp_5", "vd_heating_day_and_total_hp_5"),
        ("vd_dhw_day_hp_5", "vd_dhw_total_hp_5", "vd_dhw_day_and_total_hp_5"),
        ("vd_heating_day_consumed_hp_5", "vd_heating_total_consumed_hp_5", "vd_heating_day_and_total_consumed_hp_5"),
        ("vd_dhw_day_consumed_hp_5", "vd_dhw_total_consumed_hp_5", "vd_dhw_day_and_total_consumed_hp_5"),
        ("vd_heating_day_hp_6", "vd_heating_total_hp_6", "vd_heating_day_and_total_hp_6"),
        ("vd_dhw_day_hp_6", "vd_dhw_total_hp_6", "vd_dhw_day_and_total_hp_6"),
        ("vd_heating_day_consumed_hp_6", "vd_heating_total_consumed_hp_6", "vd_heating_day_and_total_consumed_hp_6"),
        ("vd_dhw_day_consumed_hp_6", "vd_dhw_total_consumed_hp_6", "vd_dhw_day_and_total_consumed_hp_6"),
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
    def vd_heating_day_and_total(self) -> int | None:
        return self._running_totals.get("vd_heating_day_and_total")

    @property
    def vd_dhw_day_and_total(self) -> int | None:
        return self._running_totals.get("vd_dhw_day_and_total")

    @property
    def vd_heating_day_and_total_consumed(self) -> int | None:
        return self._running_totals.get("vd_heating_day_and_total_consumed")

    @property
    def vd_dhw_day_and_total_consumed(self) -> int | None:
        return self._running_totals.get("vd_dhw_day_and_total_consumed")

    @property
    def vd_heating_day_and_total_hp_1(self) -> int | None:
        return self._running_totals.get("vd_heating_day_and_total_hp_1")

    @property
    def vd_dhw_day_and_total_hp_1(self) -> int | None:
        return self._running_totals.get("vd_dhw_day_and_total_hp_1")

    @property
    def vd_heating_day_and_total_consumed_hp_1(self) -> int | None:
        return self._running_totals.get("vd_heating_day_and_total_consumed_hp_1")

    @property
    def vd_dhw_day_and_total_consumedhp_1(self) -> int | None:
        return self._running_totals.get("vd_dhw_day_and_total_consumedhp_1")

    @property
    def vd_heating_day_and_total_hp_2(self) -> int | None:
        return self._running_totals.get("vd_heating_day_and_total_hp_2")

    @property
    def vd_dhw_day_and_total_hp_2(self) -> int | None:
        return self._running_totals.get("vd_dhw_day_and_total_hp_2")

    @property
    def vd_heating_day_and_total_consumed_hp_2(self) -> int | None:
        return self._running_totals.get("vd_heating_day_and_total_consumed_hp_2")

    @property
    def vd_dhw_day_and_total_consumed_hp_2(self) -> int | None:
        return self._running_totals.get("vd_dhw_day_and_total_consumed_hp_2")

    @property
    def vd_heating_day_and_total_hp_3(self) -> int | None:
        return self._running_totals.get("vd_heating_day_and_total_hp_3")

    @property
    def vd_dhw_day_and_total_hp_3(self) -> int | None:
        return self._running_totals.get("vd_dhw_day_and_total_hp_3")

    @property
    def vd_heating_day_and_total_consumed_hp_3(self) -> int | None:
        return self._running_totals.get("vd_heating_day_and_total_consumed_hp_3")

    @property
    def vd_dhw_day_and_total_consumed_hp_3(self) -> int | None:
        return self._running_totals.get("vd_dhw_day_and_total_consumed_hp_3")

    @property
    def vd_heating_day_and_total_hp_4(self) -> int | None:
        return self._running_totals.get("vd_heating_day_and_total_hp_4")

    @property
    def vd_dhw_day_and_total_hp_4(self) -> int | None:
        return self._running_totals.get("vd_dhw_day_and_total_hp_4")

    @property
    def vd_heating_day_and_total_consumed_hp_4(self) -> int | None:
        return self._running_totals.get("vd_heating_day_and_total_consumed_hp_4")

    @property
    def vd_dhw_day_and_total_consumed_hp_4(self) -> int | None:
        return self._running_totals.get("vd_dhw_day_and_total_consumed_hp_4")

    @property
    def vd_heating_day_and_total_hp_5(self) -> int | None:
        return self._running_totals.get("vd_heating_day_and_total_hp_5")

    @property
    def vd_dhw_day_and_total_hp_5(self) -> int | None:
        return self._running_totals.get("vd_dhw_day_and_total_hp_5")

    @property
    def vd_heating_day_and_total_consumed_hp_5(self) -> int | None:
        return self._running_totals.get("vd_heating_day_and_total_consumed_hp_5")

    @property
    def vd_dhw_day_and_total_consumed_hp_5(self) -> int | None:
        return self._running_totals.get("vd_dhw_day_and_total_consumed_hp_5")

    @property
    def vd_heating_day_and_total_hp_6(self) -> int | None:
        return self._running_totals.get("vd_heating_day_and_total_hp_6")

    @property
    def vd_dhw_day_and_total_hp_6(self) -> int | None:
        return self._running_totals.get("vd_dhw_day_and_total_hp_6")

    @property
    def vd_heating_day_and_total_consumed_hp_6(self) -> int | None:
        return self._running_totals.get("vd_heating_day_and_total_consumed_hp_6")

    @property
    def vd_dhw_day_and_total_consumed_hp_6(self) -> int | None:
        return self._running_totals.get("vd_dhw_day_and_total_consumed_hp_6")


class Wpm3EnergyManagementSettings(Component):
    register_space = "holding"
    register_ranges = WPM3_HOLDING_RANGES

    switch_sg_ready_on_and_off = boolean(4000, nan=UNAVAILABLE, writable=True)
    sg_ready_input_1 = boolean(4001, nan=UNAVAILABLE, writable=True)
    sg_ready_input_2 = boolean(4002, nan=UNAVAILABLE, writable=True)


class Wpm3EnergySystemInformation(Component):
    register_space = "input"
    register_ranges = WPM3_INPUT_RANGES

    sg_ready_operating_state = integer(5000, signed=False, nan=UNAVAILABLE)
    controller_identification = integer(5001, signed=False, nan=UNAVAILABLE)


class Wpm3StiebelEltronAPI:
    """Stiebel Eltron heat pump API over a modbus_connection ModbusUnit."""

    def __init__(self, unit: ModbusUnit) -> None:
        self.system_values = Wpm3SystemValues(unit)
        self.system_parameters = Wpm3SystemParameters(unit)
        self.system_state = Wpm3SystemState(unit)
        self.energy_data = Wpm3EnergyData(unit)
        self.energy_management_settings = Wpm3EnergyManagementSettings(unit)
        self.energy_system_information = Wpm3EnergySystemInformation(unit)
        self._group = ControllerComponents(
            unit,
            required=[
                self.system_values,
                self.system_parameters,
                self.system_state,
                self.energy_data,
                self.energy_management_settings,
                self.energy_system_information,
            ],
        )

    async def async_update(self) -> None:
        """Read every component the controller serves, in one poll."""
        await self._group.async_update()
