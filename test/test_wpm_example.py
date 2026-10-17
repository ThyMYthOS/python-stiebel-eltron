"""The WPM example never leaves the heat pump on its demo setpoint."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from modbus_connection import ModbusTimeoutError
from modbus_connection.mock import MockModbusConnection, MockModbusUnit

spec = importlib.util.spec_from_file_location("wpm_example", Path(__file__).parents[1] / "examples/wpm-example.py")
assert spec is not None and spec.loader is not None
example = importlib.util.module_from_spec(spec)
spec.loader.exec_module(example)


class LostAnswerUnit(MockModbusUnit):
    """Apply the first write, then raise as if its answer never arrived."""

    def __init__(self) -> None:
        super().__init__(MockModbusConnection(), 1)
        self.lost_answers = 1

    async def write_register(self, address: int, value: int) -> None:
        await super().write_register(address, value)
        if self.lost_answers:
            self.lost_answers -= 1
            raise ModbusTimeoutError()


@pytest.mark.asyncio()
async def test_example_restores_the_setpoint_and_closes_after_a_lost_write_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    unit = LostAnswerUnit()
    unit.holding[1509] = 450  # comfort_temperature_dhw, 0.1-scaled: 45.0 °C
    closed: list[bool] = []

    class Connection:
        def __init__(self, params: object) -> None:
            pass

        def for_unit(self, device: int) -> MockModbusUnit:
            return unit

        async def close(self) -> None:
            closed.append(True)

    monkeypatch.setattr(example, "ModbusConnection", Connection)
    monkeypatch.setattr(example.asyncio, "sleep", _no_sleep)

    with pytest.raises(ModbusTimeoutError):
        await example.main("isg.invalid")

    assert unit.holding[1509] == 450
    assert closed == [True]


async def _no_sleep(seconds: float) -> None:
    return None
