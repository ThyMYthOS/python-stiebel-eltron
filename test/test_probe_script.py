"""Check the probe script's time limit around the connection, with mocks only."""

import argparse
import asyncio
import importlib.util
import io
import time
from pathlib import Path

import pytest
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
