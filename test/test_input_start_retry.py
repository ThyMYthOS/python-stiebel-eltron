"""Start-only refusals, distinct from a mock rejecting every overlapping block."""

from __future__ import annotations

import asyncio

import pytest
from modbus_connection import IllegalDataAddressError, ModbusError, ServerDeviceBusyError
from modbus_connection.mock import MockModbusConnection, MockModbusUnit

from pystiebeleltron import UNAVAILABLE
from pystiebeleltron._read_retry import ReadStartRetry
from pystiebeleltron.lwz import LwzStiebelEltronAPI
from pystiebeleltron.wpm import WpmStiebelEltronAPI
from pystiebeleltron.wpm3 import Wpm3StiebelEltronAPI
from pystiebeleltron.wpm3i import Wpm3iStiebelEltronAPI


class StartRejectingUnit(MockModbusUnit):
    """Model the start-only rejection observed in integration issue #722."""

    def __init__(self) -> None:
        super().__init__(MockModbusConnection(), 1)
        self.rejected_starts = {609, 2560, 2569, 3679, 3689, 5219, 5229}
        self.input[500] = [UNAVAILABLE] * 111
        self.input[506] = 215
        self.input[2500] = [UNAVAILABLE] * 73
        self.input[3500] = [UNAVAILABLE] * 234
        self.input[5000] = [0, 449]

    async def read_input_registers(self, address: int, count: int) -> list[int]:
        values = await super().read_input_registers(address, count)
        if address in self.rejected_starts:
            raise IllegalDataAddressError()
        return values


def input_requests(unit: MockModbusUnit) -> list[tuple[int, int]]:
    return [(event.address, event.count) for event in unit.read_events if event.register_type == "input"]


@pytest.mark.asyncio
@pytest.mark.parametrize("raw", [False, True], ids=["update", "raw"])
@pytest.mark.parametrize(
    ("api_class", "address", "count", "anchor", "expanded"),
    [(WpmStiebelEltronAPI, 2560, 6, 2500, 66), (Wpm3StiebelEltronAPI, 509, 29, 500, 38), (Wpm3iStiebelEltronAPI, 532, 2, 500, 34)],
)
async def test_wpm_required_start_refusal_recovers(api_class, address: int, count: int, anchor: int, expanded: int, raw: bool) -> None:
    """The required 2560 read can be served from the already answered 2500 start."""
    unit = StartRejectingUnit()
    unit.rejected_starts.add(address)
    api = api_class(unit)
    if raw:
        data = await api.async_read_raw()
        assert data["input"][address] == UNAVAILABLE
        # Prefix words read for the retry are not added as new component fields.
        if api_class is WpmStiebelEltronAPI:
            assert 2547 not in data["input"]
    else:
        await api.async_update()
    assert api.system_values.outside_temperature == 21.5
    requests = input_requests(unit)
    assert (address, count) in requests and (anchor, expanded) in requests
    assert all(count <= 125 for _, count in requests)


@pytest.mark.asyncio
@pytest.mark.parametrize("raw", [False, True])
async def test_separate_optional_reads_also_retry_and_decode_only_target(raw: bool) -> None:
    unit = StartRejectingUnit()
    unit.input[609] = 217
    unit.input[610] = 225
    unit.input[2569] = [260, 12, 2, 3]
    api = WpmStiebelEltronAPI(unit)
    if raw:
        await api.async_read_raw()
    else:
        await api.async_update()
    assert api.extended_system_values.actual_temperature_hk_3 == 21.7
    assert api.extended_system_values.set_temperature_hk_3 == 22.5
    assert api.extended_system_state.extension_version == 260
    assert api.extended_system_state.major_version == 12
    assert (500, 111) in input_requests(unit)
    assert (2500, 73) in input_requests(unit)
    assert (3643, 42) in input_requests(unit)
    assert (3643, 91) in input_requests(unit)
    # No accepted start within 125 words: genuinely absent optional EMI is dropped.
    assert api.extended_energy_system_information.sg_ready_inputs_active is None


@pytest.mark.asyncio
@pytest.mark.parametrize("raw", [False, True])
async def test_no_retry_on_healthy_poll(raw: bool) -> None:
    unit = StartRejectingUnit()
    unit.rejected_starts.clear()
    api = WpmStiebelEltronAPI(unit)
    if raw:
        await api.async_read_raw()
    else:
        await api.async_update()
    assert (2500, 66) not in input_requests(unit)
    assert (500, 111) not in input_requests(unit)


@pytest.mark.asyncio
async def test_lwz_does_not_enable_start_retry() -> None:
    unit = StartRejectingUnit()
    unit.rejected_starts = {5000}
    api = LwzStiebelEltronAPI(unit)
    with pytest.raises(IllegalDataAddressError):
        await api.async_update()
    assert api._group._read_retry is None
    assert input_requests(unit).count((5000, 2)) == 1


@pytest.mark.asyncio
async def test_failed_required_retry_still_fails_poll_without_notifications() -> None:
    unit = StartRejectingUnit()
    # The longer request can still fail although its start previously answered.
    unit.fail_read(2560, IllegalDataAddressError(), register_type="input")
    api = WpmStiebelEltronAPI(unit)
    notifications = []
    api.system_values.add_update_listener(lambda: notifications.append(True))
    with pytest.raises(IllegalDataAddressError):
        await api.async_update()
    assert input_requests(unit)[-2:] == [(2560, 6), (2500, 66)]
    assert not notifications


@pytest.mark.asyncio
async def test_retry_does_not_hide_busy_or_transport_errors() -> None:
    unit = StartRejectingUnit()
    unit.fail_read(2560, ServerDeviceBusyError(), register_type="input")
    api = WpmStiebelEltronAPI(unit)
    with pytest.raises(ServerDeviceBusyError):
        await api.async_update()
    assert (2500, 66) not in input_requests(unit)


@pytest.mark.asyncio
@pytest.mark.parametrize(("address", "count"), [(225, 1), (220, 6)])
async def test_retry_cannot_exceed_125_words(address: int, count: int) -> None:
    unit = StartRejectingUnit()
    unit.rejected_starts = {address}
    retry = ReadStartRetry(unit)
    await retry.read_input_registers(100, 1)
    with pytest.raises(IllegalDataAddressError):
        await retry.read_input_registers(address, count)
    assert input_requests(unit) == [(100, 1), (address, count)]


@pytest.mark.asyncio
async def test_retry_at_125_word_limit_strips_prefix() -> None:
    unit = StartRejectingUnit()
    unit.rejected_starts = {220}
    unit.input[100] = list(range(125))
    retry = ReadStartRetry(unit)
    await retry.read_input_registers(100, 1)
    assert await retry.read_input_registers(220, 5) == [120, 121, 122, 123, 124]
    assert input_requests(unit) == [(100, 1), (220, 5), (100, 125)]


@pytest.mark.asyncio
async def test_new_poll_does_not_reuse_previous_poll_anchor() -> None:
    unit = StartRejectingUnit()
    unit.rejected_starts = {609}
    retry = ReadStartRetry(unit)
    await retry.read_input_registers(500, 108)
    retry.begin_poll()
    with pytest.raises(IllegalDataAddressError):
        await retry.read_input_registers(609, 2)
    assert input_requests(unit) == [(500, 108), (609, 2)]


@pytest.mark.asyncio
async def test_writes_are_forwarded_and_holding_retry_errors_propagate() -> None:
    unit = StartRejectingUnit()
    retry = ReadStartRetry(unit)
    await retry.write_register(1500, 3)
    assert await retry.read_holding_registers(1500, 1) == [3]
    unit.fail_read(1600, IllegalDataAddressError(), register_type="holding")
    with pytest.raises(IllegalDataAddressError):
        await retry.read_holding_registers(1600, 1)
    assert [(event.address, event.count) for event in unit.read_events] == [(1500, 1), (1600, 1), (1500, 101)]


@pytest.mark.asyncio
async def test_required_recovery_reestablishes_anchor_on_each_poll() -> None:
    unit = StartRejectingUnit()
    api = WpmStiebelEltronAPI(unit)
    for _ in range(2):
        unit.read_events.clear()
        await api.async_update()
        requests = input_requests(unit)
        assert requests.index((2500, 47)) < requests.index((2560, 6)) < requests.index((2500, 66))
        # Successful optional retries remain active, preserving the returned NaNs.
        assert (609, 2) in requests and (500, 111) in requests
        assert api.extended_system_values.actual_temperature_hk_3 is None


@pytest.mark.asyncio
async def test_overlapping_update_and_raw_polls_do_not_share_anchor_lifetime() -> None:
    class PausedUnit(StartRejectingUnit):
        def __init__(self) -> None:
            super().__init__()
            self.paused = asyncio.Event()
            self.release = asyncio.Event()

        async def read_input_registers(self, address: int, count: int) -> list[int]:
            if address == 2560 and not self.paused.is_set():
                self.paused.set()
                await self.release.wait()
            return await super().read_input_registers(address, count)

    unit = PausedUnit()
    api = WpmStiebelEltronAPI(unit)
    update = asyncio.create_task(api.async_update())
    await asyncio.wait_for(unit.paused.wait(), timeout=1)
    reads_before = len(unit.read_events)
    raw_started = asyncio.Event()

    async def read_raw():
        raw_started.set()
        return await api.async_read_raw()

    raw_task = asyncio.create_task(read_raw())
    try:
        await asyncio.wait_for(raw_started.wait(), timeout=1)
        assert len(unit.read_events) == reads_before
        assert not raw_task.done()
        unit.release.set()
        _, raw = await asyncio.wait_for(asyncio.gather(update, raw_task), timeout=1)
        assert raw["input"][2560] == UNAVAILABLE
        assert input_requests(unit).count((2500, 66)) == 2
    finally:
        unit.release.set()
        for task in (update, raw_task):
            if not task.done():
                task.cancel()
        await asyncio.gather(update, raw_task, return_exceptions=True)


@pytest.mark.asyncio
@pytest.mark.parametrize("error_class", [ServerDeviceBusyError, ModbusError])
async def test_optional_retry_transient_failure_propagates_and_keeps_component(error_class) -> None:
    class RetryFailureUnit(StartRejectingUnit):
        fail_retry = True

        async def read_input_registers(self, address: int, count: int) -> list[int]:
            if self.fail_retry and (address, count) == (500, 111):
                raise error_class()
            return await super().read_input_registers(address, count)

    unit = RetryFailureUnit()
    api = WpmStiebelEltronAPI(unit)
    notifications = []
    api.system_values.add_update_listener(lambda: notifications.append(True))
    with pytest.raises(error_class):
        await api.async_update()
    assert not notifications
    assert api.extended_system_values in api._group._optional
    unit.fail_retry = False
    await api.async_update()
    assert notifications == [True]


@pytest.mark.asyncio
async def test_block_served_by_retry_then_refused_fails_the_poll() -> None:
    """A block the retry recovered counts as answered when it is refused later."""
    unit = StartRejectingUnit()
    unit.input[609] = [217, 225]
    api = WpmStiebelEltronAPI(unit)
    await api.async_update()
    assert api.extended_system_values.actual_temperature_hk_3 == 21.7

    # Refuse the direct read and the expanded retry that covers 609.
    unit.fail_read(609, IllegalDataAddressError(), register_type="input")
    with pytest.raises(IllegalDataAddressError):
        await api.async_update()

    unit.fail_read(609, None, register_type="input")
    unit.input[609] = [218, 225]
    await api.async_update()
    assert api.extended_system_values.actual_temperature_hk_3 == 21.8
