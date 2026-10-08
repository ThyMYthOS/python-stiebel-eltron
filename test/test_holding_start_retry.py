"""Holding regressions for the public report in integration issue #722."""

from __future__ import annotations

import asyncio

import pytest
from modbus_connection import IllegalDataAddressError, ModbusError, ServerDeviceBusyError
from modbus_connection.mock import MockModbusConnection, MockModbusUnit
from modbus_connection.model import Component, integer

from pystiebeleltron import UNAVAILABLE
from pystiebeleltron._components import ControllerComponents
from pystiebeleltron._read_retry import ReadStartRetry
from pystiebeleltron.lwz import LwzStiebelEltronAPI
from pystiebeleltron.wpm import WpmStiebelEltronAPI


class HoldingStartUnit(MockModbusUnit):
    """Synthetic start-only refusals; shorter retry success is not hardware proof."""

    def __init__(self) -> None:
        super().__init__(MockModbusConnection(), 1)
        self.reject_input: set[int] = {2560}
        self.reject_holding: set[int] = {1550, 1603}
        self.input[2500] = [UNAVAILABLE] * 73
        self.holding[1500] = [UNAVAILABLE] * 108
        self.holding[1500] = 3
        self.holding[1501] = 215
        self.holding[1550] = 227
        self.holding[1603] = 185

    async def read_input_registers(self, address: int, count: int) -> list[int]:
        values = await super().read_input_registers(address, count)
        if address in self.reject_input:
            raise IllegalDataAddressError()
        return values

    async def read_holding_registers(self, address: int, count: int) -> list[int]:
        values = await super().read_holding_registers(address, count)
        if address in self.reject_holding:
            raise IllegalDataAddressError()
        return values


def reads(unit: MockModbusUnit, space: str) -> list[tuple[int, int]]:
    return [(event.address, event.count) for event in unit.read_events if event.register_type == space]


@pytest.mark.asyncio
@pytest.mark.parametrize("raw", [False, True])
async def test_wpm_required_holding_recovers_without_moving_fields(raw: bool) -> None:
    unit = HoldingStartUnit()
    api = WpmStiebelEltronAPI(unit)
    for _ in range(2):
        unit.read_events.clear()
        if raw:
            data = await api.async_read_raw()
            assert data["holding"][1550] == 227 and data["holding"][1603] == 185
            assert 1521 not in data["holding"]
        else:
            await api.async_update()
        assert api.system_parameters.comfort_temperature_hk_3 == 22.7
        assert api.system_parameters.set_temperature_cc_1_hk_1 == 18.5
        requests = reads(unit, "holding")
        assert requests.index((1500, 21)) < requests.index((1550, 9)) < requests.index((1500, 59))
        assert (1603, 5) in requests and (1500, 108) in requests
        # Recovered 1550 must not become an anchor for the second refusal.
        assert (1550, 58) not in requests
        assert all(count <= 125 for _, count in requests)


@pytest.mark.asyncio
async def test_holding_unavailable_values_remain_at_existing_field_locations() -> None:
    unit = HoldingStartUnit()
    unit.holding[1550] = UNAVAILABLE
    unit.holding[1603] = UNAVAILABLE
    api = WpmStiebelEltronAPI(unit)
    await api.async_update()
    assert api.system_parameters.comfort_temperature_hk_3 is None
    assert api.system_parameters.set_temperature_cc_1_hk_1 is None


@pytest.mark.asyncio
@pytest.mark.parametrize("space", ["input", "holding"])
async def test_read_spaces_never_share_anchors(space: str) -> None:
    unit = HoldingStartUnit()
    retry = ReadStartRetry(unit)
    other = "holding" if space == "input" else "input"
    getattr(unit, f"reject_{space}").add(220)
    await getattr(retry, f"read_{other}_registers")(100, 1)
    with pytest.raises(IllegalDataAddressError):
        await getattr(retry, f"read_{space}_registers")(220, 1)
    assert reads(unit, space) == [(220, 1)]


@pytest.mark.asyncio
@pytest.mark.parametrize(("address", "count"), [(225, 1), (220, 6), (100, 1)])
async def test_holding_needs_lower_same_poll_anchor_within_limit(address: int, count: int) -> None:
    unit = HoldingStartUnit()
    retry = ReadStartRetry(unit)
    await retry.read_holding_registers(100, 1)
    unit.reject_holding.add(address)
    with pytest.raises(IllegalDataAddressError):
        await retry.read_holding_registers(address, count)
    assert reads(unit, "holding") == [(100, 1), (address, count)]


@pytest.mark.asyncio
async def test_holding_limit_nearest_anchor_prefix_and_poll_reset() -> None:
    unit = HoldingStartUnit()
    unit.reject_holding.add(220)
    unit.holding[100] = list(range(125))
    retry = ReadStartRetry(unit)
    await retry.read_holding_registers(90, 1)
    await retry.read_holding_registers(100, 1)
    assert await retry.read_holding_registers(220, 5) == [120, 121, 122, 123, 124]
    assert reads(unit, "holding")[-1] == (100, 125)
    retry.begin_poll()
    unit.read_events.clear()
    with pytest.raises(IllegalDataAddressError):
        await retry.read_holding_registers(220, 5)
    assert reads(unit, "holding") == [(220, 5)]


@pytest.mark.asyncio
@pytest.mark.parametrize("error_class", [IllegalDataAddressError, ServerDeviceBusyError, ModbusError])
@pytest.mark.parametrize("raw", [False, True])
async def test_required_holding_retry_failure_propagates_without_notification(error_class, raw: bool) -> None:
    class FailedRetryUnit(HoldingStartUnit):
        async def read_holding_registers(self, address: int, count: int) -> list[int]:
            if (address, count) == (1500, 59):
                raise error_class()
            return await super().read_holding_registers(address, count)

    unit = FailedRetryUnit()
    api = WpmStiebelEltronAPI(unit)
    notifications = []
    api.system_parameters.add_update_listener(lambda: notifications.append(True))
    with pytest.raises(error_class):
        await (api.async_read_raw() if raw else api.async_update())
    assert not notifications
    assert reads(unit, "holding").count((1550, 9)) == 1
    assert (1603, 5) not in reads(unit, "holding")


@pytest.mark.asyncio
@pytest.mark.parametrize("error_class", [ServerDeviceBusyError, ModbusError])
async def test_original_holding_transient_failure_never_retries(error_class) -> None:
    unit = HoldingStartUnit()
    unit.fail_read(1550, error_class(), register_type="holding")
    api = WpmStiebelEltronAPI(unit)
    with pytest.raises(error_class):
        await api.async_update()
    assert (1500, 59) not in reads(unit, "holding")


@pytest.mark.asyncio
async def test_healthy_holding_and_writes_are_unchanged() -> None:
    unit = HoldingStartUnit()
    unit.reject_holding.clear()
    api = WpmStiebelEltronAPI(unit)
    await api.async_update()
    assert (1500, 59) not in reads(unit, "holding")
    assert (1500, 108) not in reads(unit, "holding")
    await api.system_parameters.write("comfort_temperature_hk_3", 23)
    assert unit.holding[1550] == 230
    # A write at a refused read start never performs a read retry.
    unit.reject_holding.add(1550)
    retry = ReadStartRetry(unit)
    unit.read_events.clear()
    await retry.write_register(1550, 231)
    await retry.write_registers(1551, [1, 2])
    assert not unit.read_events
    assert unit.holding[1550] == 231


@pytest.mark.asyncio
async def test_lwz_holding_read_still_has_no_retry() -> None:
    unit = HoldingStartUnit()
    unit.reject_holding = {4000}
    api = LwzStiebelEltronAPI(unit)
    with pytest.raises(IllegalDataAddressError):
        await api.async_update()
    assert api._group._read_retry is None
    assert reads(unit, "holding").count((4000, 3)) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("raw", [False, True])
@pytest.mark.parametrize("error_class", [IllegalDataAddressError, ServerDeviceBusyError, ModbusError])
async def test_optional_holding_retry_error_semantics(error_class, raw: bool) -> None:
    class Required(Component):
        register_space = "holding"
        register_ranges = ((1500, 1500),)
        value = integer(1500)

    class Optional(Component):
        register_space = "holding"
        register_ranges = ((1550, 1550),)
        value = integer(1550, nan=UNAVAILABLE)

    class RetryFailure(HoldingStartUnit):
        fail_retry = True

        async def read_holding_registers(self, address: int, count: int) -> list[int]:
            if self.fail_retry and (address, count) == (1500, 51):
                raise error_class()
            return await super().read_holding_registers(address, count)

    unit = RetryFailure()
    required, optional = Required(unit), Optional(unit)
    group = ControllerComponents(unit, [required], [optional], retry_register_start=True)
    notified = []
    required.add_update_listener(lambda: notified.append(True))
    if error_class is IllegalDataAddressError:
        await (group.async_read_raw() if raw else group.async_update())
        assert optional not in group._optional
        assert notified == [True]
    else:
        with pytest.raises(error_class):
            await (group.async_read_raw() if raw else group.async_update())
        assert optional in group._optional
        assert not notified
        unit.fail_retry = False
        await group.async_update()
        assert optional.value == 227
        assert notified == [True]


@pytest.mark.asyncio
async def test_holding_pause_serializes_update_and_raw() -> None:
    class Paused(HoldingStartUnit):
        def __init__(self) -> None:
            super().__init__()
            self.paused, self.release = asyncio.Event(), asyncio.Event()

        async def read_holding_registers(self, address: int, count: int) -> list[int]:
            if address == 1550 and not self.paused.is_set():
                self.paused.set()
                await self.release.wait()
            return await super().read_holding_registers(address, count)

    unit = Paused()
    api = WpmStiebelEltronAPI(unit)
    update = asyncio.create_task(api.async_update())
    await asyncio.wait_for(unit.paused.wait(), 1)
    before = len(unit.read_events)
    started = asyncio.Event()

    async def raw():
        started.set()
        return await api.async_read_raw()

    raw_task = asyncio.create_task(raw())
    try:
        await asyncio.wait_for(started.wait(), 1)
        assert len(unit.read_events) == before
        unit.release.set()
        await asyncio.wait_for(asyncio.gather(update, raw_task), 1)
        assert reads(unit, "holding").count((1500, 59)) == 2
        assert reads(unit, "holding").count((1500, 108)) == 2
    finally:
        unit.release.set()
        for task in (update, raw_task):
            if not task.done():
                task.cancel()
        await asyncio.gather(update, raw_task, return_exceptions=True)


@pytest.mark.asyncio
async def test_write_failure_is_forwarded_exactly_once() -> None:
    class WriteFailure(HoldingStartUnit):
        writes = 0

        async def write_register(self, address: int, value: int) -> None:
            self.writes += 1
            raise IllegalDataAddressError()

    unit = WriteFailure()
    retry = ReadStartRetry(unit)
    await retry.read_holding_registers(1500, 1)
    with pytest.raises(IllegalDataAddressError):
        await retry.write_register(1550, 230)
    assert unit.writes == 1
    assert reads(unit, "holding") == [(1500, 1)]


@pytest.mark.asyncio
async def test_holding_chooses_nearest_of_two_eligible_anchors() -> None:
    unit = HoldingStartUnit()
    unit.reject_holding.add(220)
    retry = ReadStartRetry(unit)
    await retry.read_holding_registers(100, 1)
    await retry.read_holding_registers(110, 1)
    await retry.read_holding_registers(220, 5)
    assert reads(unit, "holding") == [(100, 1), (110, 1), (220, 5), (110, 115)]


class ReportedHoldingTraceUnit(HoldingStartUnit):
    """Reproduce only public reads from tnomas' hardware report6053518891."""

    def __init__(self) -> None:
        super().__init__()
        self.reject_input.update({609, 5219})
        self.reject_holding.update({1548, 1558, 1600, 1602, 1700, 1703, 1740, 1749})
        for address in (*range(500, 611), *range(2500, 2573)):
            self.input[address] = UNAVAILABLE
        self.input[506] = 215
        for address in (*range(1550, 1559), *range(1603, 1608), *range(1703, 1752)):
            self.holding[address] = UNAVAILABLE


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("start", "end", "accepted"),
    [
        (1500, 1520, True),
        (1500, 1558, True),
        (1520, 1558, True),
        (1548, 1558, False),
        (1500, 1607, True),
        (1520, 1607, True),
        (1558, 1607, False),
        (1600, 1607, False),
        (1602, 1607, False),
        (1700, 1708, False),
        (1703, 1708, False),
        (1740, 1751, False),
        (1749, 1751, False),
    ],
)
async def test_public_holding_trace_read_outcomes(start: int, end: int, accepted: bool) -> None:
    unit = ReportedHoldingTraceUnit()
    if accepted:
        words = await unit.read_holding_registers(start, end - start + 1)
        for address in range(start, end + 1):
            if 1550 <= address <= 1558 or 1603 <= address <= 1607:
                assert words[address - start] == UNAVAILABLE
    else:
        with pytest.raises(IllegalDataAddressError):
            await unit.read_holding_registers(start, end - start + 1)


@pytest.mark.asyncio
@pytest.mark.parametrize("raw", [False, True])
async def test_public_trace_three_polls_recover_required_and_drop_optional(raw: bool) -> None:
    unit = ReportedHoldingTraceUnit()
    api = WpmStiebelEltronAPI(unit)
    writes = []
    unit.on_write(writes.append)
    for poll in range(3):
        unit.read_events.clear()
        if raw:
            data = await api._group.async_read_raw()
            assert all(data["holding"][address] == UNAVAILABLE for address in (*range(1550, 1559), *range(1603, 1608)))
        else:
            await api.async_update()
        assert api.system_values.outside_temperature == 21.5
        assert api.system_parameters.comfort_temperature_hk_3 is None
        assert api.system_parameters.set_temperature_cc_1_hk_1 is None
        requests = reads(unit, "holding")
        assert requests.index((1500, 21)) < requests.index((1550, 9)) < requests.index((1500, 59))
        assert requests.index((1603, 5)) < requests.index((1500, 108))
        assert requests.count((1703, 6)) == (1 if poll == 0 else 0)
        assert (1500, 209) not in requests
        # 1703 and1749 belong to the same optional component, dropped at1703.
        assert all(address != 1749 for address, _ in requests)
        assert api.extended_system_parameters not in api._group._optional
        assert api.extended_energy_system_information not in api._group._optional
        assert ("input", 5219, 3) in {(e.register_type, e.address, e.count) for e in unit.read_events} if poll == 0 else all(e.address != 5219 for e in unit.read_events)
        assert all(count <= 125 for _, count in requests)
    assert not writes
