"""Offline checks of the register probe against the mock unit."""

import asyncio
import json

import pytest
from modbus_connection import IllegalDataAddressError, ModbusTimeoutError
from modbus_connection.mock import MockModbusConnection, MockModbusUnit

from pystiebeleltron import UNAVAILABLE
from pystiebeleltron.probe import REGISTER_MAPS, ProbeLimits, _ProbeUnit, build_plan, probe


def mock_unit() -> MockModbusUnit:
    return MockModbusUnit(MockModbusConnection(), 1)


async def no_sleep(_: float) -> None:
    return None


def test_plan_tags_shared_addresses_once() -> None:
    plan = build_plan(["lwz", "wpm"])
    keys = [(space, address) for space, address, _ in plan]
    assert len(keys) == len(set(keys)) == 541
    assert plan[0][:2] == ("input", 0)
    tags = {(space, address): owners for space, address, owners in plan}
    assert tags[("holding", 1020)] == ["lwz"]
    assert tags[("input", 5001)] == ["lwz", "wpm"]
    assert ("input", 608) not in tags


def test_subset_maps_add_no_addresses() -> None:
    """WPM 3 and WPM 3i read a subset of the WPM map."""
    assert len(build_plan(["wpm", "wpm3", "wpm3i"])) == len(build_plan(["wpm"]))


@pytest.mark.asyncio
async def test_single_reads_record_refusal_marker_and_words() -> None:
    unit = mock_unit()
    unit.input[506] = 123
    unit.input[507] = UNAVAILABLE
    unit.fail_read(508, IllegalDataAddressError(), register_type="input")
    report = await probe(unit, ["wpm3i"], sleep=no_sleep)
    rows = {(row["space"], row["address"]): row for row in report.registers}
    assert report.status == "completed"
    assert len(rows) == len(build_plan(["wpm3i"]))
    assert rows[("input", 506)]["words"] == [123]
    assert rows[("input", 507)]["unavailable_offsets"] == [0]
    assert rows[("input", 508)] == {"maps": ["wpm3i"], "space": "input", "address": 508, "count": 1, "status": "exception", "exception_code": 2}
    assert all(event.count == 1 for event in unit.read_events)


class StartRefusingUnit:
    """Refuse input reads that start at ``start``, as some ISGs do (#722)."""

    def __init__(self, unit: MockModbusUnit, start: int) -> None:
        self._unit = unit
        self._start = start

    async def read_input_registers(self, address: int, count: int) -> list[int]:
        if address == self._start:
            raise IllegalDataAddressError()
        return await self._unit.read_input_registers(address, count)

    async def read_holding_registers(self, address: int, count: int) -> list[int]:
        return await self._unit.read_holding_registers(address, count)


@pytest.mark.asyncio
async def test_poll_records_refused_block_start_and_its_retry() -> None:
    report = await probe(StartRefusingUnit(mock_unit(), 509), [], poll="wpm3", sleep=no_sleep)
    assert report.poll_result == {"status": "ok"}
    requests = [(row["address"], row["count"], row["status"]) for row in report.poll_requests]
    assert requests[1:3] == [(509, 29, "exception"), (500, 38, "ok")]


@pytest.mark.asyncio
async def test_failed_poll_keeps_its_requests_and_continues() -> None:
    unit = mock_unit()
    unit.fail_read(1501, IllegalDataAddressError(), register_type="holding")
    report = await probe(unit, ["wpm3"], poll="wpm3", sleep=no_sleep)
    assert report.poll_result == {"status": "exception", "exception_code": 2}
    assert report.poll_requests[-1]["space"] == "holding"
    assert report.poll_requests[-1]["status"] == "exception"
    assert report.status == "completed"
    assert len(report.registers) == len(build_plan(["wpm3"]))


@pytest.mark.asyncio
async def test_poll_ok_lists_the_block_requests() -> None:
    unit = mock_unit()
    report = await probe(unit, [], poll="wpm", sleep=no_sleep)
    assert report.poll_result == {"status": "ok"}
    assert len(report.poll_requests) == len(unit.read_events)
    assert any(row["count"] > 1 for row in report.poll_requests)


@pytest.mark.asyncio
async def test_stops_after_consecutive_transport_errors() -> None:
    unit = mock_unit()
    unit.fail_requests(ModbusTimeoutError("private-host timed out"))
    report = await probe(unit, ["wpm3i"], sleep=no_sleep)
    assert report.status == "stopped_after_transport_errors"
    assert len(unit.read_events) == 3
    assert "private-host" not in json.dumps(report.as_dict())


@pytest.mark.asyncio
async def test_request_limit_cuts_the_poll() -> None:
    unit = mock_unit()
    report = await probe(unit, ["wpm"], poll="wpm", limits=ProbeLimits(max_requests=2), sleep=no_sleep)
    assert report.status == "stopped_at_request_limit"
    assert report.poll_result == {"status": "not_finished"}
    assert len(report.poll_requests) == 2
    assert report.registers == []


@pytest.mark.asyncio
async def test_time_limit_ends_the_single_reads() -> None:
    now = [0.0]

    async def slow_sleep(seconds: float) -> None:
        now[0] += 10

    unit = mock_unit()
    report = await probe(unit, ["wpm3i"], limits=ProbeLimits(max_duration=25), sleep=slow_sleep, clock=lambda: now[0])
    assert report.status == "stopped_at_time_limit"
    assert len(report.registers) == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["write_register", "write_registers", "write_coil", "read_coils", "mask_write_register", "read_write_registers"])
async def test_only_register_reads_reach_the_unit(method: str) -> None:
    unit = mock_unit()
    writes = []
    unit.on_write(writes.append)
    with pytest.raises(AttributeError, match="only reads"):
        getattr(_ProbeUnit(unit, ProbeLimits(), lambda: 0.0), method)
    assert not writes


@pytest.mark.asyncio
async def test_unknown_map_is_rejected() -> None:
    unit = mock_unit()
    with pytest.raises(ValueError, match="Unknown register map"):
        await probe(unit, ["thz"])
    assert not unit.read_events


def test_maps_cover_every_family() -> None:
    assert set(REGISTER_MAPS) == {"lwz", "wpm", "wpm3", "wpm3i"}


class ShortAnswerUnit(StartRefusingUnit):
    """Answer input reads that start at ``start`` with one word too few."""

    async def read_input_registers(self, address: int, count: int) -> list[int]:
        words = await self._unit.read_input_registers(address, count)
        return words[:-1] if address == self._start else words


@pytest.mark.asyncio
async def test_short_poll_answer_is_reported_not_decoded() -> None:
    report = await probe(ShortAnswerUnit(mock_unit(), 500), ["wpm3i"], poll="wpm3i", sleep=no_sleep)
    assert report.poll_result == {"status": "invalid_response"}
    assert report.poll_requests[0]["status"] == "invalid_response"
    assert report.status == "completed"
    assert report.registers[0]["status"] == "invalid_response"
    assert report.registers[1]["status"] == "ok"


class HangingUnit(StartRefusingUnit):
    """Never answer an input read that starts at ``start``."""

    async def read_input_registers(self, address: int, count: int) -> list[int]:
        if address == self._start:
            await asyncio.sleep(60)
        return await self._unit.read_input_registers(address, count)


@pytest.mark.asyncio
async def test_hanging_read_ends_the_run_at_the_time_limit() -> None:
    report = await probe(HangingUnit(mock_unit(), 501), ["wpm3i"], limits=ProbeLimits(max_duration=0.2), sleep=no_sleep)
    assert report.status == "stopped_at_time_limit"
    assert [row["status"] for row in report.registers] == ["ok", "stopped_at_time_limit"]


@pytest.mark.asyncio
async def test_pause_never_outlasts_the_time_limit() -> None:
    now = [0.0]
    pauses = []

    async def fake_sleep(seconds: float) -> None:
        pauses.append(seconds)
        now[0] += seconds

    report = await probe(mock_unit(), ["wpm3i"], limits=ProbeLimits(max_duration=1.0, pause=0.4), sleep=fake_sleep, clock=lambda: now[0])
    assert report.status == "stopped_at_time_limit"
    assert pauses == [0.4, 0.4, pytest.approx(0.2)]
