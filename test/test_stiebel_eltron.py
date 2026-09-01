from __future__ import annotations

import pytest
from modbus_connection import IllegalDataAddressError, ModbusError, ReadBlock, ServerDeviceBusyError
from modbus_connection.mock import MockModbusConnection, MockModbusUnit
from modbus_connection.model import Component

from pystiebeleltron import (
    UNAVAILABLE,
    ControllerModel,
    StiebelEltronModbusError,
    UnknownControllerModelError,
    get_controller_model,
)
from pystiebeleltron.lwz import LWZ_HOLDING_RANGES, LWZ_INPUT_RANGES, LwzStiebelEltronAPI, OperatingMode
from pystiebeleltron.wpm import WPM_HOLDING_RANGES, WPM_INPUT_RANGES, WpmStiebelEltronAPI
from pystiebeleltron.wpm3i import WPM3I_HOLDING_RANGES, WPM3I_INPUT_RANGES, Wpm3iStiebelEltronAPI


def _seed(unit: MockModbusUnit, *components: Component) -> None:
    """Seed each component's store so register ``i`` of a block reads back as ``i``.

    Mirrors the synthetic pattern the assertions are derived from: a block whose
    fields start at address ``base`` gets ``[0, 1, 2, ...]`` from ``base`` on, so a
    field at address ``base + n`` decodes the raw value ``n``.
    """
    for component in components:
        fields = component.declared_fields.values()
        low = min(field.address for field in fields)
        high = max(field.address + field.count - 1 for field in fields)
        store = unit.input if component.register_space == "input" else unit.holding
        store[low] = list(range(high - low + 1))


@pytest.mark.parametrize(
    "ranges",
    [WPM_HOLDING_RANGES, WPM_INPUT_RANGES, WPM3I_HOLDING_RANGES, WPM3I_INPUT_RANGES, LWZ_HOLDING_RANGES, LWZ_INPUT_RANGES],
)
def test_declared_ranges_are_separated_by_a_real_gap(ranges: tuple[tuple[int, int], ...]) -> None:
    """Consecutive entries must leave at least one address unclaimed between them.

    A gap in the map is what stops a read from crossing it. The manual splits
    the registers into documentation blocks that sometimes abut - the WPM energy
    block ends at 3642 and the extended one starts at 3643 - and emitting those
    as two entries would forbid a single read the controller answers happily.
    The generator joins them, so every remaining boundary is one the device
    really has.
    """
    for (_, high), (low, _) in zip(ranges, ranges[1:], strict=False):
        assert low > high + 1, f"({low}, ...) touches (..., {high}); they are one readable run"


@pytest.mark.parametrize("api_class", [WpmStiebelEltronAPI, Wpm3iStiebelEltronAPI, LwzStiebelEltronAPI])
@pytest.mark.asyncio()
async def test_every_field_sits_inside_a_declared_readable_range(
    mock_modbus_unit: MockModbusUnit,
    api_class: type[WpmStiebelEltronAPI | Wpm3iStiebelEltronAPI | LwzStiebelEltronAPI],
) -> None:
    """Every controller's layout must plan against the ranges it declares.

    ``register_ranges`` says which addresses the controller answers, and a field
    the map does not contain cannot be read at all, so the planner refuses to
    build the plan rather than emitting a block the device would refuse. That
    fails the first poll of a whole controller family, which is why each of them
    is polled here and not only the two with value assertions below.
    """
    api = api_class(mock_modbus_unit)

    await api.async_update()

    for component in vars(api).values():
        if not isinstance(component, Component):
            continue
        ranges = component.register_ranges or ()
        for name, resolved in component.resolved_fields.items():
            last = resolved.address + resolved.count - 1
            assert any(low <= resolved.address and last <= high for low, high in ranges), f"{type(component).__name__}.{name} reads {resolved.address}-{last}, outside {ranges}"


@pytest.mark.asyncio()
async def test_wpm(mock_modbus_unit: MockModbusUnit) -> None:
    api = WpmStiebelEltronAPI(mock_modbus_unit)
    _seed(mock_modbus_unit, api.system_values, api.energy_data)

    await api.async_update()

    assert api.system_values.actual_temperature_fek == 0.2
    # vd_heating_day (10) + scaled_sum total (11 + 12 * 1000) = 12021
    assert api.energy_data.vd_heating_day_and_total_consumed == 12021


@pytest.mark.asyncio()
async def test_wpm_repeating_groups(mock_modbus_unit: MockModbusUnit) -> None:
    """Repeated sub-units read as typed lists, each instance at its strided address."""
    api = WpmStiebelEltronAPI(mock_modbus_unit)
    _seed(mock_modbus_unit, api.system_values)

    await api.async_update()

    heat_pumps = api.system_values.heat_pumps
    assert len(heat_pumps) == 6
    # return_temperature is at wire address 541 (raw 41) for HP1, +7 per instance.
    assert heat_pumps[0].return_temperature == 4.1
    assert heat_pumps[5].return_temperature == 7.6
    assert heat_pumps[0].low_pressure == 0.44  # 0.01-scaled

    room_temperatures = api.system_values.room_temperatures
    assert len(room_temperatures) == 5
    # actual_temperature is at wire address 583 (raw 83) for HC1, +4 per instance.
    assert room_temperatures[0].actual_temperature == 8.3
    assert room_temperatures[1].actual_temperature == 8.7

    cooling = api.system_values.room_temperatures_cooling
    assert len(cooling) == 5
    # set_temperature is at wire address 603 (raw 103) for COOLING1, +1 per instance.
    assert cooling[0].set_temperature == 10.3
    assert cooling[4].set_temperature == 10.7


@pytest.mark.asyncio()
async def test_write_out_of_range_rejected(mock_modbus_unit: MockModbusUnit) -> None:
    """A write validator rejects values outside the register's documented range."""
    api = WpmStiebelEltronAPI(mock_modbus_unit)

    # comfort_temperature_hk_1 is a 0.1-scaled holding register with range [5, 30].
    await api.system_parameters.write("comfort_temperature_hk_1", 22)
    assert mock_modbus_unit.holding[1501] == 220

    with pytest.raises(ValueError, match="outside the allowed range"):
        await api.system_parameters.write("comfort_temperature_hk_1", 40)
    # The rejected write must not have reached the device.
    assert mock_modbus_unit.holding[1501] == 220


@pytest.mark.asyncio()
async def test_a_documented_flag_reads_as_a_bool(mock_modbus_unit: MockModbusUnit) -> None:
    """A register the manual bounds to 0..1 decodes to True/False, not 0/1.

    ``is`` rather than ``==`` because ``False == 0`` - only identity tells the
    flag apart from the integer it used to be. A code the manual does not
    define reads as None: a pump reported with an undefined value is unknown,
    and taking anything non-zero as running would invent a state the
    controller never reported.
    """
    api = WpmStiebelEltronAPI(mock_modbus_unit)

    for raw, expected in ((1, True), (0, False), (UNAVAILABLE, None), (2, None)):
        mock_modbus_unit.input[2508] = raw
        await api.async_update()
        assert api.system_state.heating_circuit_pump_1 is expected


@pytest.mark.asyncio()
async def test_a_writable_flag_takes_a_bool_or_the_raw_code(mock_modbus_unit: MockModbusUnit) -> None:
    """Writing a flag accepts True/False and the 1/0 callers passed before."""
    api = WpmStiebelEltronAPI(mock_modbus_unit)

    for value in (True, 1):
        await api.energy_management_settings.write("sg_ready_input_1", value)
        assert mock_modbus_unit.holding[4001] == 1

    for value in (False, 0):
        await api.energy_management_settings.write("sg_ready_input_1", value)
        assert mock_modbus_unit.holding[4001] == 0


@pytest.mark.asyncio()
async def test_lwz_dhw_setpoint_accepts_the_documented_model_maximum(
    mock_modbus_unit: MockModbusUnit,
) -> None:
    """The LWZ hot water setpoints accept what the larger models document.

    The manual states 55 °C for DHW SET DAY and DHW SET NIGHT without naming a
    model. The ISG object database gives 65 °C for LWZ 5S Plus, 5S Smart and
    LWZ INV on the same two registers, so a validator that stops at 55 refuses
    a value those controllers accept.
    """
    api = LwzStiebelEltronAPI(mock_modbus_unit)

    # dhw_set_day is a 0.1-scaled holding register at wire address 1011.
    await api.system_parameters.write("dhw_set_day", 57)
    assert mock_modbus_unit.holding[1011] == 570

    await api.system_parameters.write("dhw_set_night", 65)
    assert mock_modbus_unit.holding[1012] == 650

    # Above the largest documented value the validator still rejects.
    with pytest.raises(ValueError, match="outside the allowed range"):
        await api.system_parameters.write("dhw_set_day", 66)
    assert mock_modbus_unit.holding[1011] == 570


@pytest.mark.asyncio()
async def test_wpm_power_consumption_registers(mock_modbus_unit: MockModbusUnit) -> None:
    api = WpmStiebelEltronAPI(mock_modbus_unit)
    _seed(mock_modbus_unit, api.extended_energy_data)

    await api.async_update()

    # The block starts at 3643, so heating_24h at 3707 decodes 64 + 65 * 1000.
    extended = api.extended_energy_data
    assert extended.heating_24h == 65064
    assert extended.heating_12m == 67066
    assert extended.cooling_24h == 71070
    assert extended.cooling_12m == 73072
    assert extended.dhw_24h == 77076
    assert extended.dhw_12m == 79078


@pytest.mark.asyncio()
async def test_lwz(mock_modbus_unit: MockModbusUnit) -> None:
    api = LwzStiebelEltronAPI(mock_modbus_unit)
    _seed(mock_modbus_unit, api.system_values, api.system_parameters, api.system_state, api.energy_data)

    await api.async_update()

    assert api.system_values.relative_humidity_hc1 == 0.2
    # heat_meter_htg_day (0) + scaled_sum total (1 + 2 * 1000) = 2001
    assert api.energy_data.heat_meter_htg_day_and_total == 2001

    assert api.get_current_humidity() == 0.2
    assert api.get_current_temp() == 0.0
    assert api.get_target_temp() == 0.1

    assert api.get_operation() == OperatingMode.EMERGENCY_OPERATION

    # compressor_starts_hi (30) * 1000 + compressor_starts_low (33) = 30033
    assert api.system_values.compressor_starts == 30033


@pytest.mark.asyncio()
async def test_write_register(mock_modbus_unit: MockModbusUnit) -> None:
    api = LwzStiebelEltronAPI(mock_modbus_unit)

    await api.set_target_temp(21.5)

    # room_temperature_day_hk1 is a 0.1-scaled holding register at wire address 1001.
    assert mock_modbus_unit.holding[1001] == 215


@pytest.mark.parametrize(
    ("model_id", "expected"),
    [
        (103, ControllerModel.LWZ),
        (104, ControllerModel.LWZ_x04_SOL),
        (390, ControllerModel.WPM_3),
        (391, ControllerModel.WPM_3i),
        (449, ControllerModel.WPMsystem),
        (551, ControllerModel.LWZ_R290),
    ],
)
@pytest.mark.asyncio()
async def test_get_controller_model(mock_modbus_unit: MockModbusUnit, model_id: int, expected: ControllerModel) -> None:
    """Test get_controller_model maps a model id register to its ControllerModel."""
    mock_modbus_unit.input[5001] = model_id
    model = await get_controller_model(mock_modbus_unit)
    assert model == expected


@pytest.mark.asyncio()
async def test_get_controller_model_error_response(mock_modbus_connection: MockModbusConnection) -> None:
    """Test get_controller_model raises error when the modbus read fails."""
    await mock_modbus_connection.close()
    with pytest.raises(StiebelEltronModbusError):
        await get_controller_model(mock_modbus_connection.for_unit(1))


@pytest.mark.asyncio()
async def test_get_controller_model_unknown_id(mock_modbus_unit: MockModbusUnit) -> None:
    """An unrecognized model id surfaces as UnknownControllerModelError, not a comms error."""
    mock_modbus_unit.input[5001] = 999
    with pytest.raises(UnknownControllerModelError) as exc_info:
        await get_controller_model(mock_modbus_unit)
    assert exc_info.value.model_id == 999
    assert not isinstance(exc_info.value, StiebelEltronModbusError)


@pytest.mark.asyncio()
async def test_energy_counter_unavailable(mock_modbus_unit: MockModbusUnit) -> None:
    """A magnitude counter with an unavailable (0x8000) word decodes to None."""
    api = LwzStiebelEltronAPI(mock_modbus_unit)
    _seed(mock_modbus_unit, api.energy_data)
    mock_modbus_unit.input[3002] = 0x8000  # the MWh word of heat_meter_htg_ttl

    await api.async_update()

    assert api.energy_data.heat_meter_htg_ttl is None
    assert api.energy_data.heat_meter_htg_day_and_total is None


@pytest.mark.asyncio()
async def test_async_update_surfaces_refused_block(mock_modbus_unit: MockModbusUnit) -> None:
    """A device that refuses a register block (e.g. an uninstalled module) errors out.

    ``async_update`` pools reads into per-space blocks; if the controller answers
    one with a Modbus exception, that surfaces as a ``ModbusError`` rather than
    quietly leaving those fields at their previous values.
    """
    api = WpmStiebelEltronAPI(mock_modbus_unit)
    _seed(mock_modbus_unit, api.system_values)
    # 502 falls inside the first input block; illegal-data-address (2) mimics a
    # controller that doesn't serve that block.
    mock_modbus_unit.fail_read(502, IllegalDataAddressError(), register_type="input")

    with pytest.raises(ModbusError):
        await api.async_update()

    # Clearing the failure lets the same update succeed.
    mock_modbus_unit.fail_read(502, None, register_type="input")
    await api.async_update()
    assert api.system_values.actual_temperature_fek == 0.2


@pytest.mark.asyncio()
async def test_wpm_without_the_extended_energy_registers(mock_modbus_unit: MockModbusUnit) -> None:
    """A controller without the energy-management registers still updates.

    Registers 5219-5230 belong to an extension not every controller and firmware
    serves; one that doesn't answers the block with illegal data address. That
    must cost those values and nothing else, rather than failing the poll -
    the setup failure reported as pail23/stiebel_eltron_isg_component#599.
    """
    api = WpmStiebelEltronAPI(mock_modbus_unit)
    _seed(mock_modbus_unit, api.system_values, api.energy_system_information)
    mock_modbus_unit.fail_read(5219, IllegalDataAddressError(), register_type="input")

    await api.async_update()

    assert api.system_values.actual_temperature_fek == 0.2
    assert api.energy_system_information.sg_ready_operating_state == 0
    assert api.extended_energy_system_information.sg_ready_inputs_active is None


@pytest.mark.asyncio()
async def test_lwz_without_the_extended_energy_registers(mock_modbus_unit: MockModbusUnit) -> None:
    """An LWZ without the inverter and efficiency registers still updates.

    The block at 3679-3697 is the one an LWZ 304 Trend refuses in #599.
    """
    api = LwzStiebelEltronAPI(mock_modbus_unit)
    _seed(mock_modbus_unit, api.system_values, api.energy_data)
    mock_modbus_unit.fail_read(3679, IllegalDataAddressError(), register_type="input")

    await api.async_update()

    assert api.energy_data.heat_meter_htg_day_and_total == 2001
    assert api.extended_energy_data.inverter_power is None


@pytest.mark.asyncio()
async def test_a_busy_controller_does_not_lose_an_optional_block(mock_modbus_unit: MockModbusUnit) -> None:
    """Only illegal data address means "not built in"; other codes are failures.

    A controller that answers a block with device busy or device failure still
    has those registers, so dropping the component would lose its values for
    good over a passing complaint. Such an answer fails the poll instead, and
    the block is read again once the controller answers properly.
    """
    api = WpmStiebelEltronAPI(mock_modbus_unit)
    _seed(mock_modbus_unit, api.system_values, api.extended_energy_system_information)
    mock_modbus_unit.fail_read(5219, ServerDeviceBusyError(), register_type="input")

    # The busy answer reaches the caller as itself, naming the block it aborted,
    # rather than as something the tolerance rewrapped on the way out.
    with pytest.raises(ServerDeviceBusyError) as exc_info:
        await api.async_update()
    assert exc_info.value.block == ReadBlock("input", 5219, 3)

    mock_modbus_unit.fail_read(5219, None, register_type="input")
    await api.async_update()

    assert api.extended_energy_system_information.sg_ready_inputs_active == 0


@pytest.mark.asyncio()
async def test_a_refused_optional_block_is_not_read_again(mock_modbus_unit: MockModbusUnit) -> None:
    """Once a controller has refused an optional block, later polls skip it.

    Otherwise every poll would spend a doomed round trip on a block the
    controller has already said it does not serve.
    """
    api = WpmStiebelEltronAPI(mock_modbus_unit)
    _seed(mock_modbus_unit, api.system_values)
    mock_modbus_unit.fail_read(5219, IllegalDataAddressError(), register_type="input")

    await api.async_update()
    await api.async_update()

    attempts = [event for event in mock_modbus_unit.read_events if event.register_type == "input" and event.address <= 5219 <= event.address + event.count - 1]
    assert len(attempts) == 1


@pytest.mark.asyncio()
async def test_a_failed_poll_notifies_nobody(mock_modbus_unit: MockModbusUnit) -> None:
    """A poll that raises must not have told listeners the values are fresh.

    The required components are read before the optional ones, so a later
    optional block answering with anything but illegal data address would
    otherwise fire their listeners and then raise, leaving whoever listens
    acting on half a poll. A single pooled read never did that.
    """
    api = WpmStiebelEltronAPI(mock_modbus_unit)
    _seed(mock_modbus_unit, api.system_values, api.extended_energy_system_information)
    notified = 0

    def count() -> None:
        nonlocal notified
        notified += 1

    api.system_values.add_update_listener(count)
    mock_modbus_unit.fail_read(5219, ServerDeviceBusyError(), register_type="input")

    with pytest.raises(ModbusError):
        await api.async_update()

    assert notified == 0

    mock_modbus_unit.fail_read(5219, None, register_type="input")
    await api.async_update()

    assert notified == 1


@pytest.mark.asyncio()
async def test_a_refused_block_still_notifies_the_rest(mock_modbus_unit: MockModbusUnit) -> None:
    """A block the controller does not serve is not a failed poll.

    Deferring the notification must not swallow it on the one path that is
    expected to happen on every machine without the optional registers.
    """
    api = WpmStiebelEltronAPI(mock_modbus_unit)
    _seed(mock_modbus_unit, api.system_values)
    notified = 0

    def count() -> None:
        nonlocal notified
        notified += 1

    api.system_values.add_update_listener(count)
    mock_modbus_unit.fail_read(5219, IllegalDataAddressError(), register_type="input")

    await api.async_update()

    assert notified == 1


@pytest.mark.asyncio()
async def test_a_controller_refusing_everything_still_errors(mock_modbus_unit: MockModbusUnit) -> None:
    """Tolerating optional blocks must not make a mute controller look healthy."""
    api = WpmStiebelEltronAPI(mock_modbus_unit)
    mock_modbus_unit.fail_requests(IllegalDataAddressError())

    with pytest.raises(ModbusError):
        await api.async_update()
