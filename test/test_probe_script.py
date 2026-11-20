"""Check the probe script's time limit around the connection, with mocks only."""

import argparse
import asyncio
import importlib.util
import io
import time
from pathlib import Path

import pytest
from modbus_connection import ModbusConnectionError
from modbus_connection.mock import MockModbusConnection, MockModbusUnit

spec = importlib.util.spec_from_file_location("probe_script", Path(__file__).parents[1] / "scripts/probe.py")
script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(script)


class SlowClosingConnection:
    """A connection whose close waits for a reconnect that takes ``delay`` seconds."""

    def __init__(self, delay: float) -> None:
        self._unit = MockModbusUnit(MockModbusConnection(), 1)
        self._delay = delay
        self.close_started = False

    def for_unit(self, unit_id: int) -> MockModbusUnit:
        return self._unit

    async def close(self) -> None:
        self.close_started = True
        await asyncio.sleep(self._delay)


@pytest.mark.asyncio
async def test_slow_close_does_not_outlast_the_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = SlowClosingConnection(delay=30)

    async def connect(args: argparse.Namespace) -> SlowClosingConnection:
        return connection

    monkeypatch.setattr(script, "connect_from_args", connect)
    monkeypatch.setattr(script, "CLOSE_GRACE", 0.1)
    args = argparse.Namespace(unit=1, poll="wpm3i", maps=None, max_duration=0.2)
    output = io.StringIO()
    start = time.monotonic()
    assert await script._run(args, output) == 0
    assert time.monotonic() - start < 2
    assert connection.close_started
    assert '"poll": "wpm3i"' in output.getvalue()


class FailingCloseConnection(SlowClosingConnection):
    """A connection whose close fails with a connection error."""

    async def close(self) -> None:
        self.close_started = True
        raise ModbusConnectionError("connection lost")


@pytest.mark.asyncio
async def test_failed_close_keeps_the_report(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = FailingCloseConnection(delay=0)

    async def connect(args: argparse.Namespace) -> FailingCloseConnection:
        return connection

    monkeypatch.setattr(script, "connect_from_args", connect)
    args = argparse.Namespace(unit=1, poll="wpm3i", maps=None, max_duration=0.2)
    output = io.StringIO()
    assert await script._run(args, output) == 0
    assert connection.close_started
    assert '"poll": "wpm3i"' in output.getvalue()


@pytest.mark.parametrize("value", ["inf", "nan", "0", "-5", "soon"])
def test_max_duration_must_be_finite_and_positive(value: str) -> None:
    with pytest.raises(SystemExit):
        script._parse_args(["192.0.2.1", "--max-duration", value])


def test_poll_none_needs_maps() -> None:
    with pytest.raises(SystemExit):
        script._parse_args(["192.0.2.1", "--poll", "none"])
    assert script._parse_args(["192.0.2.1", "--poll", "none", "--maps", "wpm3i"]).maps == ["wpm3i"]


def test_run_that_raises_leaves_no_report(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    async def crash(args: argparse.Namespace, output: object) -> int:
        output.write("{")  # type: ignore[attr-defined]
        raise KeyError("new controller model")

    monkeypatch.setattr(script, "_run", crash)
    report = tmp_path / "report.json"
    with pytest.raises(KeyError):
        script.main(["192.0.2.1", "--output", str(report)])
    assert not report.exists()


def test_existing_report_is_kept_when_creating_fails(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    report.write_text("earlier run", encoding="utf-8")
    assert script.main(["192.0.2.1", "--output", str(report)]) == 1
    assert report.read_text(encoding="utf-8") == "earlier run"
