"""Modbus api for stiebel eltron heat pumps. This file is generated. Do not modify it manually."""

from __future__ import annotations

from modbus_connection import ModbusUnit
from modbus_connection.model import Component, gauge, integer, repeating_group

from . import UNAVAILABLE, in_range, scaled_sum
from ._components import ControllerComponents

WPM_HOLDING_RANGES = ((1500, 1607), (1703, 1751), (4000, 4002), (4249, 4277))
WPM_INPUT_RANGES = ((500, 610), (2500, 2572), (3500, 3642), (3643, 3733), (5000, 5001), (5219, 5230))


class WpmHeatPumpModule(Component):
    """One repeated sub-unit; instance i is read at ``base_offset = i * stride``."""

    register_space = "input"

    return_temperature = gauge(541, 0.1, nan=UNAVAILABLE, unit="°C")
    flow_temperature = gauge(542, 0.1, nan=UNAVAILABLE, unit="°C")
    hot_gas_temperature = gauge(543, 0.1, nan=UNAVAILABLE, unit="°C")
    low_pressure = gauge(544, 0.01, nan=UNAVAILABLE, unit="bar")
    mean_pressure = gauge(545, 0.01, nan=UNAVAILABLE, unit="bar")
    high_pressure = gauge(546, 0.01, nan=UNAVAILABLE, unit="bar")
    wp_water_flow_rate = gauge(547, 0.1, nan=UNAVAILABLE, unit="l/min")


class WpmRoomTemperature(Component):
    """One repeated sub-unit; instance i is read at ``base_offset = i * stride``."""

    register_space = "input"

    actual_temperature = gauge(583, 0.1, nan=UNAVAILABLE, unit="°C")
    set_temperature = gauge(584, 0.1, nan=UNAVAILABLE, unit="°C")
    relative_humidity = gauge(585, 0.1, nan=UNAVAILABLE, unit="%")
    dew_point_temperature = gauge(586, 0.1, nan=UNAVAILABLE, unit="°C")


class WpmRoomTemperatureCooling(Component):
    """One repeated sub-unit; instance i is read at ``base_offset = i * stride``."""

    register_space = "input"

    set_temperature = gauge(603, 0.1, nan=UNAVAILABLE, unit="°C")


class WpmSystemValues(Component):
    register_space = "input"
    register_ranges = WPM_INPUT_RANGES

    actual_temperature_fe7 = gauge(500, 0.1, nan=UNAVAILABLE, unit="°C")
    set_temperature_fe7 = gauge(501, 0.1, nan=UNAVAILABLE, unit="°C")
    actual_temperature_fek = gauge(502, 0.1, nan=UNAVAILABLE, unit="°C")
    set_temperature_fek = gauge(503, 0.1, nan=UNAVAILABLE, unit="°C")
    relative_humidity = gauge(504, 0.1, nan=UNAVAILABLE, unit="%")
    dew_point_temperature = gauge(505, 0.1, nan=UNAVAILABLE, unit="°C")
    outside_temperature = gauge(506, 0.1, nan=UNAVAILABLE, unit="°C")
    actual_temperature_hk_1 = gauge(507, 0.1, nan=UNAVAILABLE, unit="°C")
    set_temperature_hk_1_wpm3i = gauge(508, 0.1, nan=UNAVAILABLE, unit="°C")
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
    hot_gas_temperature = gauge(538, 0.1, nan=UNAVAILABLE, unit="°C")
    high_pressure = gauge(539, 0.1, nan=UNAVAILABLE, unit="bar")
    low_pressure = gauge(540, 0.1, nan=UNAVAILABLE, unit="bar")
    actual_temperature_hk_3 = gauge(609, 0.1, nan=UNAVAILABLE, unit="°C")
    set_temperature_hk_3 = gauge(610, 0.1, nan=UNAVAILABLE, unit="°C")
    heat_pumps = repeating_group(6, WpmHeatPumpModule, stride=7)
    room_temperatures = repeating_group(5, WpmRoomTemperature, stride=4)
    room_temperatures_cooling = repeating_group(5, WpmRoomTemperatureCooling, stride=1)


class WpmSystemParameters(Component):
    register_space = "holding"
    register_ranges = WPM_HOLDING_RANGES

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
    comfort_temperature_hk_3 = gauge(1550, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(5, 30))
    eco_temperature_hk_3 = gauge(1551, 0.1, nan=UNAVAILABLE, unit="°C", writable=in_range(5, 30))
    heating_curve_rise_hk_3 = gauge(1552, 0.01, nan=UNAVAILABLE, writable=True)
    comfort_temperature_hk_4 = gauge(1553, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    eco_temperature_hk_4 = gauge(1554, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    heating_curve_rise_hk_4 = gauge(1555, 0.01, nan=UNAVAILABLE, writable=True)
    comfort_temperature_hk_5 = gauge(1556, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    eco_temperature_hk_5 = gauge(1557, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    heating_curve_rise_hk_5 = gauge(1558, 0.01, nan=UNAVAILABLE, writable=True)
    set_temperature_cc_1_hk_1 = gauge(1603, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    set_temperature_cc_2_hk_2 = gauge(1604, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    set_temperature_cc_3_hk_3 = gauge(1605, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    set_temperature_cc_4_hk_4 = gauge(1606, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    set_temperature_cc_5_hk_5 = gauge(1607, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)


class WpmSystemState(Component):
    register_space = "input"
    register_ranges = WPM_INPUT_RANGES

    operating_status = integer(2500, signed=False, nan=UNAVAILABLE)
    power_off = integer(2501, signed=False, nan=UNAVAILABLE)
    operating_status_wpm_3 = integer(2502, signed=False, nan=UNAVAILABLE)
    fault_status = integer(2503, signed=False, nan=UNAVAILABLE)
    bus_status = integer(2504, signed=False, nan=UNAVAILABLE)
    defrost_initiated = integer(2505, signed=False, nan=UNAVAILABLE)
    active_error = integer(2506, signed=False, nan=UNAVAILABLE)
    message_number = integer(2507, signed=False, nan=UNAVAILABLE)
    heating_circuit_pump_1 = integer(2508, signed=False, nan=UNAVAILABLE)
    heating_circuit_pump_2 = integer(2509, signed=False, nan=UNAVAILABLE)
    heating_circuit_pump_3 = integer(2510, signed=False, nan=UNAVAILABLE)
    buffer_charging_pump_1 = integer(2511, signed=False, nan=UNAVAILABLE)
    buffer_charging_pump_2 = integer(2512, signed=False, nan=UNAVAILABLE)
    dhw_charging_pump = integer(2513, signed=False, nan=UNAVAILABLE)
    source_pump = integer(2514, signed=False, nan=UNAVAILABLE)
    fault_output = integer(2515, signed=False, nan=UNAVAILABLE)
    dhw_circulation_pump = integer(2516, signed=False, nan=UNAVAILABLE)
    we_2_dhw = integer(2517, signed=False, nan=UNAVAILABLE)
    we_2_heating = integer(2518, signed=False, nan=UNAVAILABLE)
    cooling_mode = integer(2519, signed=False, nan=UNAVAILABLE)
    mixer_open_hc2 = integer(2520, signed=False, nan=UNAVAILABLE)
    mixer_close_hc2 = integer(2521, signed=False, nan=UNAVAILABLE)
    mixer_open_hc3 = integer(2522, signed=False, nan=UNAVAILABLE)
    mixer_close_hc3 = integer(2523, signed=False, nan=UNAVAILABLE)
    nhz_1 = integer(2524, signed=False, nan=UNAVAILABLE)
    nhz_2 = integer(2525, signed=False, nan=UNAVAILABLE)
    nhz_1_2 = integer(2526, signed=False, nan=UNAVAILABLE)
    heating_circuit_pump_4 = integer(2527, signed=False, nan=UNAVAILABLE)
    heating_circuit_pump_5 = integer(2528, signed=False, nan=UNAVAILABLE)
    buffer_charging_pump_3 = integer(2529, signed=False, nan=UNAVAILABLE)
    buffer_charging_pump_4 = integer(2530, signed=False, nan=UNAVAILABLE)
    buffer_charging_pump_5 = integer(2531, signed=False, nan=UNAVAILABLE)
    buffer_charging_pump_6 = integer(2532, signed=False, nan=UNAVAILABLE)
    diff_controller_pump_1 = integer(2533, signed=False, nan=UNAVAILABLE)
    diff_controller_pump_2 = integer(2534, signed=False, nan=UNAVAILABLE)
    pool_pump_primary = integer(2535, signed=False, nan=UNAVAILABLE)
    pool_pump_secondary = integer(2536, signed=False, nan=UNAVAILABLE)
    mixer_open_hc4 = integer(2537, signed=False, nan=UNAVAILABLE)
    mixer_close_hc4 = integer(2538, signed=False, nan=UNAVAILABLE)
    mixer_open_hc5 = integer(2539, signed=False, nan=UNAVAILABLE)
    mixer_close_hc5 = integer(2540, signed=False, nan=UNAVAILABLE)
    compressor_1 = integer(2541, signed=False, nan=UNAVAILABLE)
    compressor_2 = integer(2542, signed=False, nan=UNAVAILABLE)
    compressor_3 = integer(2543, signed=False, nan=UNAVAILABLE)
    compressor_4 = integer(2544, signed=False, nan=UNAVAILABLE)
    compressor_5 = integer(2545, signed=False, nan=UNAVAILABLE)
    compressor_6 = integer(2546, signed=False, nan=UNAVAILABLE)
    source_pump_1 = integer(2560, signed=False, nan=UNAVAILABLE)
    source_pump_2 = integer(2561, signed=False, nan=UNAVAILABLE)
    source_pump_3 = integer(2562, signed=False, nan=UNAVAILABLE)
    source_pump_4 = integer(2563, signed=False, nan=UNAVAILABLE)
    source_pump_5 = integer(2564, signed=False, nan=UNAVAILABLE)
    source_pump_6 = integer(2565, signed=False, nan=UNAVAILABLE)
    extension_version = integer(2569, signed=False, nan=UNAVAILABLE)
    major_version = integer(2570, signed=False, nan=UNAVAILABLE)
    minor_version = integer(2571, signed=False, nan=UNAVAILABLE)
    revision = integer(2572, signed=False, nan=UNAVAILABLE)


class WpmEnergyData(Component):
    register_space = "input"
    register_ranges = WPM_INPUT_RANGES

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
    vd_heating = integer(3516, signed=False, nan=UNAVAILABLE, unit="h")
    vd_dhw = integer(3517, signed=False, nan=UNAVAILABLE, unit="h")
    vd_cooling = integer(3518, signed=False, nan=UNAVAILABLE, unit="h")
    nhz_1 = integer(3519, signed=False, nan=UNAVAILABLE, unit="h")
    nhz_2 = integer(3520, signed=False, nan=UNAVAILABLE, unit="h")
    nhz_1_2 = integer(3521, signed=False, nan=UNAVAILABLE, unit="h")
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


class WpmEnergyManagementSettings(Component):
    register_space = "holding"
    register_ranges = WPM_HOLDING_RANGES

    switch_sg_ready_on_and_off = integer(4000, signed=False, nan=UNAVAILABLE, writable=in_range(0, 1))
    sg_ready_input_1 = integer(4001, signed=False, nan=UNAVAILABLE, writable=in_range(0, 1))
    sg_ready_input_2 = integer(4002, signed=False, nan=UNAVAILABLE, writable=in_range(0, 1))


class WpmEnergySystemInformation(Component):
    register_space = "input"
    register_ranges = WPM_INPUT_RANGES

    sg_ready_operating_state = integer(5000, signed=False, nan=UNAVAILABLE)
    controller_identification = integer(5001, signed=False, nan=UNAVAILABLE)


class WpmExtendedSystemParameters(Component):
    """Registers not every machine serves, read on their own.

    A controller without them answers the block with illegal data address, which
    would fail a pooled read for everything else too, so
    :class:`~pystiebeleltron._components.ControllerComponents` reads this block
    separately and drops it once the controller has refused it.
    """

    register_space = "holding"
    register_ranges = WPM_HOLDING_RANGES

    set_flow_temperature_cc_1_hk_1 = gauge(1703, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    set_flow_temperature_cc_2_hk_2 = gauge(1704, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    set_flow_temperature_cc_3_hk_3 = gauge(1705, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    set_flow_temperature_cc_4_hk_4 = gauge(1706, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    set_flow_temperature_cc_5_hk_5 = gauge(1707, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    set_flow_temperature_fan_cooling = gauge(1708, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    summer_mode_auto_ = integer(1749, signed=False, nan=UNAVAILABLE)
    outside_temperature_summer_mode = gauge(1750, 0.1, nan=UNAVAILABLE, unit="°C")
    summer_mode_building_heat_buffer = gauge(1751, 0.1, nan=UNAVAILABLE, unit="°C")


class WpmExtendedEnergyData(Component):
    """Registers not every machine serves, read on their own.

    A controller without them answers the block with illegal data address, which
    would fail a pooled read for everything else too, so
    :class:`~pystiebeleltron._components.ControllerComponents` reads this block
    separately and drops it once the controller has refused it.
    """

    register_space = "input"
    register_ranges = WPM_INPUT_RANGES

    vd_heating_hp_1 = integer(3643, signed=False, nan=UNAVAILABLE, unit="h")
    vd_dhw_hp_1 = integer(3644, signed=False, nan=UNAVAILABLE, unit="h")
    vd_heating_hp_2 = integer(3645, signed=False, nan=UNAVAILABLE, unit="h")
    vd_dhw_hp_2 = integer(3646, signed=False, nan=UNAVAILABLE, unit="h")
    vd_heating_hp_3 = integer(3647, signed=False, nan=UNAVAILABLE, unit="h")
    vd_dhw_hp_3 = integer(3648, signed=False, nan=UNAVAILABLE, unit="h")
    vd_heating_hp_4 = integer(3649, signed=False, nan=UNAVAILABLE, unit="h")
    vd_dhw_hp_4 = integer(3650, signed=False, nan=UNAVAILABLE, unit="h")
    vd_heating_hp_5 = integer(3651, signed=False, nan=UNAVAILABLE, unit="h")
    vd_dhw_hp_5 = integer(3652, signed=False, nan=UNAVAILABLE, unit="h")
    vd_heating_hp_6 = integer(3653, signed=False, nan=UNAVAILABLE, unit="h")
    vd_dhw_hp_6 = integer(3654, signed=False, nan=UNAVAILABLE, unit="h")
    inverter_power_iws_1 = gauge(3679, 0.1, nan=UNAVAILABLE, unit="kW")
    inverter_power_iws_2 = gauge(3680, 0.1, nan=UNAVAILABLE, unit="kW")
    inverter_power_iws_3 = gauge(3681, 0.1, nan=UNAVAILABLE, unit="kW")
    inverter_power_iws_4 = gauge(3682, 0.1, nan=UNAVAILABLE, unit="kW")
    inverter_power_iws_5 = gauge(3683, 0.1, nan=UNAVAILABLE, unit="kW")
    inverter_power_iws_6 = gauge(3684, 0.1, nan=UNAVAILABLE, unit="kW")
    amount_of_heat_heating_1_24_h = scaled_sum(3689, (1, 1000), unit="Wh")
    amount_of_heat_heating_1_12 = scaled_sum(3691, (1, 1000), unit="kWh")
    amount_of_heat_heating_13_24 = scaled_sum(3693, (1, 1000), unit="kWh")
    amount_of_heat_cooling_1_24_h = scaled_sum(3695, (1, 1000), unit="Wh")
    amount_of_heat_cooling_1_12_m = scaled_sum(3697, (1, 1000), unit="kWh")
    amount_of_heat_cooling_13_24 = scaled_sum(3699, (1, 1000), unit="kWh")
    amount_of_heat_dhw_1_24_h__wh_wh = scaled_sum(3701, (1, 1000), unit="Wh")
    amount_of_heat_dhw_1_12_m = scaled_sum(3703, (1, 1000), unit="kWh")
    amount_of_heat_dhw_13_24_m = scaled_sum(3705, (1, 1000), unit="kWh")
    heating_24h = scaled_sum(3707, (1, 1000), unit="kWh")
    heating_12m = scaled_sum(3709, (1, 1000), unit="kWh")
    heating_13_24 = scaled_sum(3711, (1, 1000), unit="kWh")
    cooling_24h = scaled_sum(3713, (1, 1000), unit="kWh")
    cooling_12m = scaled_sum(3715, (1, 1000), unit="kWh")
    cooling_13_24 = scaled_sum(3717, (1, 1000), unit="kWh")
    dhw_24h = scaled_sum(3719, (1, 1000), unit="kWh")
    dhw_12m = scaled_sum(3721, (1, 1000), unit="kWh")
    dhw_13_24 = scaled_sum(3723, (1, 1000), unit="kWh")
    efficiency_heating_1_24_h = integer(3725, signed=False, nan=UNAVAILABLE)
    efficiency_heating_1_12_m = integer(3726, signed=False, nan=UNAVAILABLE)
    efficiency_heating_13_24_m = integer(3727, signed=False, nan=UNAVAILABLE)
    efficiency_cooling_1_24_h = integer(3728, signed=False, nan=UNAVAILABLE)
    efficiency_cooling_1_12_m = integer(3729, signed=False, nan=UNAVAILABLE)
    efficiency_cooling_13_24_m = integer(3730, signed=False, nan=UNAVAILABLE)
    efficiency_dhw_1_24_h = integer(3731, signed=False, nan=UNAVAILABLE)
    efficiency_dhw_1_12_m = integer(3732, signed=False, nan=UNAVAILABLE)
    efficiency_dhw_13_24_m = integer(3733, signed=False, nan=UNAVAILABLE)


class WpmExtendedEnergyManagementSettings(Component):
    """Registers not every machine serves, read on their own.

    A controller without them answers the block with illegal data address, which
    would fail a pooled read for everything else too, so
    :class:`~pystiebeleltron._components.ControllerComponents` reads this block
    separately and drops it once the controller has refused it.
    """

    register_space = "holding"
    register_ranges = WPM_HOLDING_RANGES

    sg_ready_enabled = integer(4249, signed=False, nan=UNAVAILABLE, writable=True)
    sg_ready_input = integer(4250, signed=False, nan=UNAVAILABLE, writable=True)
    heating_buffer = integer(4251, signed=False, nan=UNAVAILABLE, writable=True)
    load_temperature_hc1 = gauge(4253, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    load_temperature_hc2 = gauge(4254, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    load_temperature_dhw = gauge(4255, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    input_mode = integer(4257, signed=False, nan=UNAVAILABLE, writable=True)
    power_limit = integer(4258, signed=False, nan=UNAVAILABLE, writable=True)
    load_temperature_hc1_2 = gauge(4271, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    load_temperature_hc2_2 = gauge(4272, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    load_temperature_hc3 = gauge(4273, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    load_temperature_hc4 = gauge(4274, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    load_temperature_hc5 = gauge(4275, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    load_temperature_buffer = gauge(4276, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)
    load_temperature_dhw_2 = gauge(4277, 0.1, nan=UNAVAILABLE, unit="°C", writable=True)


class WpmExtendedEnergySystemInformation(Component):
    """Registers not every machine serves, read on their own.

    A controller without them answers the block with illegal data address, which
    would fail a pooled read for everything else too, so
    :class:`~pystiebeleltron._components.ControllerComponents` reads this block
    separately and drops it once the controller has refused it.
    """

    register_space = "input"
    register_ranges = WPM_INPUT_RANGES

    sg_ready_inputs_active = integer(5219, signed=False, nan=UNAVAILABLE)
    sg_ready_bit_1 = integer(5220, signed=False, nan=UNAVAILABLE)
    sg_ready_bit_2 = integer(5221, signed=False, nan=UNAVAILABLE)
    user_power_limit = integer(5229, signed=False, nan=UNAVAILABLE, unit="W")
    electrical_power_limit_requested = integer(5230, signed=False, nan=UNAVAILABLE, unit="W")


class WpmStiebelEltronAPI:
    """Stiebel Eltron heat pump API over a modbus_connection ModbusUnit."""

    def __init__(self, unit: ModbusUnit) -> None:
        self.system_values = WpmSystemValues(unit)
        self.system_parameters = WpmSystemParameters(unit)
        self.system_state = WpmSystemState(unit)
        self.energy_data = WpmEnergyData(unit)
        self.energy_management_settings = WpmEnergyManagementSettings(unit)
        self.energy_system_information = WpmEnergySystemInformation(unit)
        self.extended_system_parameters = WpmExtendedSystemParameters(unit)
        self.extended_energy_data = WpmExtendedEnergyData(unit)
        self.extended_energy_management_settings = WpmExtendedEnergyManagementSettings(unit)
        self.extended_energy_system_information = WpmExtendedEnergySystemInformation(unit)
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
            optional=[
                self.extended_system_parameters,
                self.extended_energy_data,
                self.extended_energy_management_settings,
                self.extended_energy_system_information,
            ],
        )

    async def async_update(self) -> None:
        """Read every component the controller serves, in one poll."""
        await self._group.async_update()
