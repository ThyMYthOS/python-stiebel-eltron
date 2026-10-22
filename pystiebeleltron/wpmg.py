"""Modbus api for stiebel eltron heat pumps. This file is generated. Do not modify it manually."""

from __future__ import annotations

from asyncio import timeout
from typing import Any, cast

from modbus_connection import ModbusUnit
from modbus_connection.model import Component, boolean, gauge, integer

from . import UNAVAILABLE
from ._components import ControllerComponents
from ._wpmg_reader import WpmGReader

WPMG_INPUT_RANGES = ((6000, 6033), (6099, 6119), (6123, 6127), (7499, 7507), (7599, 7603), (7649, 7652), (7654, 7656), (7659, 7660), (7662, 7662), (7699, 7699), (8999, 9062))


class WpmGSystemValues(Component):
    register_space = "input"
    register_ranges = WPMG_INPUT_RANGES

    buffer_cylinder_temperature = gauge(6000, 0.01, nan=UNAVAILABLE, unit="°C")
    heating_circuit_1_flow_temperature = gauge(6001, 0.01, nan=UNAVAILABLE, unit="°C")
    heating_circuit_2_flow_temperature = gauge(6002, 0.01, nan=UNAVAILABLE, unit="°C")
    heating_circuit_3_flow_temperature = gauge(6003, 0.01, nan=UNAVAILABLE, unit="°C")
    heating_circuit_4_flow_temperature = gauge(6004, 0.01, nan=UNAVAILABLE, unit="°C")
    heating_circuit_5_flow_temperature = gauge(6005, 0.01, nan=UNAVAILABLE, unit="°C")
    heating_circuit_2_return_temperature = gauge(6006, 0.01, nan=UNAVAILABLE, unit="°C")
    heating_circuit_3_return_temperature = gauge(6007, 0.01, nan=UNAVAILABLE, unit="°C")
    heating_circuit_4_return_temperature = gauge(6008, 0.01, nan=UNAVAILABLE, unit="°C")
    heating_circuit_5_return_temperature = gauge(6009, 0.01, nan=UNAVAILABLE, unit="°C")
    cooling_circuit_return_temperature = gauge(6010, 0.01, nan=UNAVAILABLE, unit="°C")
    cooling_cylinder_temperature = gauge(6011, 0.01, nan=UNAVAILABLE, unit="°C")
    cooling_cylinder_return_temperature = gauge(6012, 0.01, nan=UNAVAILABLE, unit="°C")
    cooling_cylinder_flow_temperature = gauge(6013, 0.01, nan=UNAVAILABLE, unit="°C")
    dhw_draw_off_control_flow_temperature = gauge(6014, 0.01, nan=UNAVAILABLE, unit="°C")
    dhw_draw_off_control_return_temperature = gauge(6015, 0.01, nan=UNAVAILABLE, unit="°C")
    dhw_charging_system_return_temperature = gauge(6016, 0.01, nan=UNAVAILABLE, unit="°C")
    dhw_draw_off_control_cylinder_temperature = gauge(6017, 0.01, nan=UNAVAILABLE, unit="°C")
    system_sensor_upper_dhw_temperature = gauge(6018, 0.01, nan=UNAVAILABLE, unit="°C")
    system_sensor_lower_dhw_temperature = gauge(6019, 0.01, nan=UNAVAILABLE, unit="°C")
    brine_inlet_temperature = gauge(6020, 0.01, nan=UNAVAILABLE, unit="°C")
    brine_outlet_temperature = gauge(6021, 0.01, nan=UNAVAILABLE, unit="°C")
    hot_gas_temperature = gauge(6022, 0.01, nan=UNAVAILABLE, unit="°C")
    condenser_inlet_temperature = gauge(6023, 0.01, nan=UNAVAILABLE, unit="°C")
    condenser_outlet_temperature = gauge(6024, 0.01, nan=UNAVAILABLE, unit="°C")
    liquid_line_temperature = gauge(6025, 0.01, nan=UNAVAILABLE, unit="°C")
    suction_gas_temperature = gauge(6026, 0.01, nan=UNAVAILABLE, unit="°C")
    pool_flow_temperature = gauge(6027, 0.01, nan=UNAVAILABLE, unit="°C")
    pool_return_temperature = gauge(6028, 0.01, nan=UNAVAILABLE, unit="°C")
    hot_gas_mode_dhw_flow_temperature = gauge(6029, 0.01, nan=UNAVAILABLE, unit="°C")
    sg_ready_input_1 = boolean(6030, nan=UNAVAILABLE)
    sg_ready_input_2 = boolean(6031, nan=UNAVAILABLE)
    external_stop_pool_heating = boolean(6032, nan=UNAVAILABLE)
    external_start_brine_pump = boolean(6033, nan=UNAVAILABLE)
    outside_temperature_averaged = gauge(6099, 0.01, nan=UNAVAILABLE, unit="°C")
    dhw_temperature_weighted = gauge(6100, 0.01, nan=UNAVAILABLE, unit="°C")
    evaporation_temperature_in_high_pressure_range = gauge(6101, 0.01, nan=UNAVAILABLE, unit="°C")
    condensation_temperature_in_high_pressure_range = gauge(6102, 0.01, nan=UNAVAILABLE, unit="°C")
    condensation_temperature_in_low_pressure_range = gauge(6103, 0.01, nan=UNAVAILABLE, unit="°C")
    superheating = gauge(6104, 0.01, nan=UNAVAILABLE, unit="K")
    supercooling = gauge(6105, 0.01, nan=UNAVAILABLE, unit="K")
    pressure_low_pressure_side = gauge(6106, 0.01, nan=UNAVAILABLE, unit="bar")
    pressure_high_pressure_side = gauge(6107, 0.01, nan=UNAVAILABLE, unit="bar")
    l1_current = gauge(6108, 0.01, nan=UNAVAILABLE, unit="A")
    l2_current = gauge(6109, 0.01, nan=UNAVAILABLE, unit="A")
    l3_current = gauge(6110, 0.01, nan=UNAVAILABLE, unit="A")
    l1_n_voltage = gauge(6111, 0.01, nan=UNAVAILABLE, unit="V")
    l2_n_voltage = gauge(6112, 0.01, nan=UNAVAILABLE, unit="V")
    l3_n_voltage = gauge(6113, 0.01, nan=UNAVAILABLE, unit="V")
    l1_l2_voltage = gauge(6114, 0.1, nan=UNAVAILABLE, unit="V")
    l2_l3_voltage = gauge(6115, 0.1, nan=UNAVAILABLE, unit="V")
    l3_l1_voltage = gauge(6116, 0.1, nan=UNAVAILABLE, unit="V")
    l1_power_consumption = integer(6117, signed=False, nan=UNAVAILABLE, unit="W")
    l2_power_consumption = integer(6118, signed=False, nan=UNAVAILABLE, unit="W")
    l3_power_consumption = integer(6119, signed=False, nan=UNAVAILABLE, unit="W")
    set_buffer_cylinder_temperature = gauge(6123, 0.01, nan=UNAVAILABLE, unit="°C")
    start_delay_active = boolean(6124, nan=UNAVAILABLE)
    current_output_stage_compressor = integer(6125, signed=False, nan=UNAVAILABLE)
    current_output_stage_internal_booster_heater = integer(6126, signed=False, nan=UNAVAILABLE)
    percentage_compressor_speed = integer(6127, signed=False, nan=UNAVAILABLE, unit="%")


class WpmGSystemState(Component):
    register_space = "input"
    register_ranges = WPMG_INPUT_RANGES

    control_signal_external_booster_heater = boolean(7499, nan=UNAVAILABLE)
    control_signal_internal_booster_heater_stage_2 = boolean(7500, nan=UNAVAILABLE)
    control_signal_heating_circuit_1_circulation_pump = boolean(7501, nan=UNAVAILABLE)
    control_signal_condenser = boolean(7502, nan=UNAVAILABLE)
    control_signal_internal_booster_heater_stage_1 = boolean(7503, nan=UNAVAILABLE)
    control_signal_hot_gas_circulation_pump = boolean(7504, nan=UNAVAILABLE)
    control_signal_brine_pump = boolean(7505, nan=UNAVAILABLE)
    control_signal_external_booster_heater_dhw_circulation_pump = boolean(7506, nan=UNAVAILABLE)
    control_signal_external_relay_for_brine_pump = boolean(7507, nan=UNAVAILABLE)
    feedback_external_booster_heater = boolean(7599, nan=UNAVAILABLE)
    feedback_internal_booster_heater = boolean(7600, nan=UNAVAILABLE)
    control_signal_hot_gas_control = boolean(7601, nan=UNAVAILABLE)
    heat_pump_off = boolean(7602, nan=UNAVAILABLE)
    heat_pump_ready_to_start = boolean(7603, nan=UNAVAILABLE)
    control_signal_dhw_draw_off_control_flow_dhw_circulation_pump = boolean(7649, nan=UNAVAILABLE)
    control_signal_dhw_charging_system_control = boolean(7650, nan=UNAVAILABLE)
    control_signal_dhw_charging_system_dhw_circulation_pump = boolean(7651, nan=UNAVAILABLE)
    control_signal_dhw_draw_off_control_cylinder_heating = boolean(7652, nan=UNAVAILABLE)
    control_signal_cooling_circuit_dhw_circulation_pump = boolean(7654, nan=UNAVAILABLE)
    control_signal_pool_dhw_circulation_pump = boolean(7655, nan=UNAVAILABLE)
    control_signal_cooling_circuit_control = boolean(7656, nan=UNAVAILABLE)
    control_signal_pool_control = boolean(7659, nan=UNAVAILABLE)
    note_if_mixing_valve_used_for_passive_cooling = boolean(7660, nan=UNAVAILABLE)
    control_signal_compressor = boolean(7662, nan=UNAVAILABLE)
    compressor_cannot_start = boolean(7699, nan=UNAVAILABLE)


class WpmGAlarms(Component):
    register_space = "input"
    register_ranges = WPMG_INPUT_RANGES

    level_1_notification = boolean(8999, nan=UNAVAILABLE)
    level_2_notification = boolean(9000, nan=UNAVAILABLE)
    level_3_notification = boolean(9001, nan=UNAVAILABLE)
    level_1_notification_high_pressure = boolean(9002, nan=UNAVAILABLE)
    level_1_notification_low_pressure = boolean(9003, nan=UNAVAILABLE)
    level_1_notification_hot_gas_temperature = boolean(9004, nan=UNAVAILABLE)
    level_1_notification_operating_pressure = boolean(9005, nan=UNAVAILABLE)
    level_1_notification_hot_gas_line_sensor = boolean(9006, nan=UNAVAILABLE)
    level_1_notification_liquid_line_sensor = boolean(9007, nan=UNAVAILABLE)
    level_1_notification_suction_gas_sensor = boolean(9008, nan=UNAVAILABLE)
    level_1_notification_flow_rate_pressure_brine_or_condenser = boolean(9009, nan=UNAVAILABLE)
    level_1_notification_bm_card_phase_sequence = boolean(9010, nan=UNAVAILABLE)
    level_1_notification_inverter_fault = boolean(9011, nan=UNAVAILABLE)
    level_3_notification_low_source_temperature = boolean(9012, nan=UNAVAILABLE)
    level_1_notification_low_compressor_speed = boolean(9013, nan=UNAVAILABLE)
    level_1_notification_low_superheating = boolean(9014, nan=UNAVAILABLE)
    level_1_notification_outside_pressure_ratio = boolean(9015, nan=UNAVAILABLE)
    level_1_notification_outside_operating_range = boolean(9016, nan=UNAVAILABLE)
    level_1_notification_brine_temperature_outside_range = boolean(9017, nan=UNAVAILABLE)
    level_2_notification_brine_inlet_sensor = boolean(9018, nan=UNAVAILABLE)
    level_2_notification_brine_outlet_sensor = boolean(9019, nan=UNAVAILABLE)
    level_2_notification_condenser_inlet_sensor = boolean(9020, nan=UNAVAILABLE)
    level_2_notification_condenser_outlet_sensor = boolean(9021, nan=UNAVAILABLE)
    level_2_notification_outside_temperature_sensor = boolean(9022, nan=UNAVAILABLE)
    level_2_notification_system_flow_sensor = boolean(9023, nan=UNAVAILABLE)
    level_2_notification_heating_circuit_1_sensor = boolean(9024, nan=UNAVAILABLE)
    level_2_notification_heating_circuit_2_sensor = boolean(9025, nan=UNAVAILABLE)
    level_2_notification_heating_circuit_3_sensor = boolean(9026, nan=UNAVAILABLE)
    level_2_notification_heating_circuit_4_sensor = boolean(9027, nan=UNAVAILABLE)
    level_2_notification_heating_circuit_5_sensor = boolean(9028, nan=UNAVAILABLE)
    level_2_notification_dhw_charging_circuit_sensor = boolean(9029, nan=UNAVAILABLE)
    level_2_notification_dhw_sensor = boolean(9030, nan=UNAVAILABLE)
    level_2_notification_cooling_buffer_sensor = boolean(9031, nan=UNAVAILABLE)
    level_2_notification_cooling_cylinder_flow_sensor = boolean(9032, nan=UNAVAILABLE)
    level_2_notification_cooling_circuit_return_sensor = boolean(9033, nan=UNAVAILABLE)
    level_2_notification_source_circuit_spread_max = boolean(9034, nan=UNAVAILABLE)
    level_2_notification_dhw_centre_sensor = boolean(9035, nan=UNAVAILABLE)
    level_2_notification_dhw_return_sensor = boolean(9036, nan=UNAVAILABLE)
    level_2_notification_dhw_hot_gas_sensor = boolean(9037, nan=UNAVAILABLE)
    level_2_notification_internal_booster_heater = boolean(9038, nan=UNAVAILABLE)
    level_3_notification_condenser_maximum_temperature = boolean(9039, nan=UNAVAILABLE)
    level_2_notification_max_brine_inlet = boolean(9040, nan=UNAVAILABLE)
    level_2_notification_min_brine_inlet = boolean(9041, nan=UNAVAILABLE)
    level_2_notification_min_brine_outlet = boolean(9042, nan=UNAVAILABLE)
    level_3_notification_min_dhw_circulation_return = boolean(9043, nan=UNAVAILABLE)
    level_3_notification_min_dhw_circulation_temperature = boolean(9044, nan=UNAVAILABLE)
    level_3_notification_heating_circuit_1_temperature = boolean(9045, nan=UNAVAILABLE)
    level_3_notification_heating_circuit_2_temperature = boolean(9046, nan=UNAVAILABLE)
    level_3_notification_heating_circuit_3_temperature = boolean(9047, nan=UNAVAILABLE)
    level_3_notification_heating_circuit_4_temperature = boolean(9048, nan=UNAVAILABLE)
    level_3_notification_heating_circuit_5_temperature = boolean(9049, nan=UNAVAILABLE)
    level_3_notification_dhw_circulation_return_temperature = boolean(9050, nan=UNAVAILABLE)
    notification_central_message = boolean(9051, nan=UNAVAILABLE)
    level_3_notification_cooling_circuit_temperature = boolean(9052, nan=UNAVAILABLE)
    level_3_notification_cooling_buffer_temperature = boolean(9053, nan=UNAVAILABLE)
    level_2_notification_humidity_sensor = boolean(9054, nan=UNAVAILABLE)
    level_2_notification_cooling_buffer_return_sensor = boolean(9055, nan=UNAVAILABLE)
    level_3_notification_room_temperature_sensor = boolean(9056, nan=UNAVAILABLE)
    level_1_notification_inverter_communication = boolean(9057, nan=UNAVAILABLE)
    level_2_notification_pool_return_sensor = boolean(9058, nan=UNAVAILABLE)
    level_2_notification_cooling_heating_circuit_1_sensor = boolean(9059, nan=UNAVAILABLE)
    level_2_notification_dhw_cylinder_sensor = boolean(9060, nan=UNAVAILABLE)
    level_2_notification_maximum_pasteurisation_time = boolean(9061, nan=UNAVAILABLE)
    level_3_notification_external_alarm = boolean(9062, nan=UNAVAILABLE)


class WpmGStiebelEltronAPI:
    """Stiebel Eltron heat pump API over a modbus_connection ModbusUnit."""

    def __init__(self, unit: ModbusUnit) -> None:
        self._reader = WpmGReader(unit, WPMG_INPUT_RANGES)
        # Components below use FC04 only; the adapter intentionally offers no writes.
        unit = cast(ModbusUnit, self._reader)
        self.system_values = WpmGSystemValues(unit)
        self.system_state = WpmGSystemState(unit)
        self.alarms = WpmGAlarms(unit)
        self._group = ControllerComponents(
            unit,
            required=[
                self.system_values,
                self.system_state,
                self.alarms,
            ],
        )

    async def async_update(self) -> None:
        """Read every component the controller serves, in one poll."""
        self._reader.start_poll()
        try:
            async with timeout(20):
                await self._group.async_update()
        except BaseException as error:
            self._reader.finish_poll(error)
            raise
        self._reader.finish_poll()

    @property
    def polling_report(self) -> dict[str, Any]:
        """Latest register reads and bounded error history, without connection data."""
        report = self._reader.report
        rows = {row["wire_address"]: row for row in report["registers"]}
        for name, field in self.system_values.resolved_fields.items():
            if (row := rows.get(field.address)) is not None:
                row["field"] = "system_values." + name
                if report["status"] in {"completed", "partial"} and row["status"] == "ok" and getattr(self.system_values, name) is None:
                    row["status"] = "invalid_value"
        for name, field in self.system_state.resolved_fields.items():
            if (row := rows.get(field.address)) is not None:
                row["field"] = "system_state." + name
                if report["status"] in {"completed", "partial"} and row["status"] == "ok" and getattr(self.system_state, name) is None:
                    row["status"] = "invalid_value"
        for name, field in self.alarms.resolved_fields.items():
            if (row := rows.get(field.address)) is not None:
                row["field"] = "alarms." + name
                if report["status"] in {"completed", "partial"} and row["status"] == "ok" and getattr(self.alarms, name) is None:
                    row["status"] = "invalid_value"
        if report["status"] == "completed" and any(row["status"] == "invalid_value" for row in rows.values()):
            report["status"] = "partial"
        report["usable_registers"] = sum(row["status"] == "ok" for row in rows.values())
        return report

    def retry_failed_registers(self) -> None:
        """Re-probe rejected registers on the next regular poll."""
        self._reader.retry_failed_registers()
