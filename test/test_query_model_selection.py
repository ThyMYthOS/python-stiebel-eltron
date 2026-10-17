"""The query script reads each reported controller model with the right API."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import pytest
from modbus_connection.mock import MockModbusUnit

from pystiebeleltron import ControllerModel
from pystiebeleltron.lwz import LwzStiebelEltronAPI
from pystiebeleltron.wpm import WpmStiebelEltronAPI
from pystiebeleltron.wpm3 import Wpm3StiebelEltronAPI
from pystiebeleltron.wpm3i import Wpm3iStiebelEltronAPI

spec = importlib.util.spec_from_file_location("query_script", Path(__file__).parents[1] / "scripts/query.py")
assert spec is not None and spec.loader is not None
query = importlib.util.module_from_spec(spec)
spec.loader.exec_module(query)


def test_every_controller_model_has_an_api() -> None:
    """A new model id must say which register map it answers before the script can use it."""
    assert set(query.API_BY_MODEL) == set(ControllerModel)


@pytest.mark.parametrize(
    ("model_id", "api_class"),
    [
        (103, LwzStiebelEltronAPI),
        (104, LwzStiebelEltronAPI),
        (390, Wpm3StiebelEltronAPI),
        (391, Wpm3iStiebelEltronAPI),
        (449, WpmStiebelEltronAPI),
        # An LWZ_R290 is a THZ behind an ISG Connect: named like an LWZ, served like a WPM.
        (551, WpmStiebelEltronAPI),
    ],
)
@pytest.mark.asyncio()
async def test_detected_model_selects_its_register_map(mock_modbus_unit: MockModbusUnit, model_id: int, api_class: type[object]) -> None:
    mock_modbus_unit.input[5001] = model_id

    api = await query._build_api(argparse.Namespace(model=None), mock_modbus_unit)

    assert type(api) is api_class


@pytest.mark.asyncio()
async def test_forced_model_skips_detection(mock_modbus_unit: MockModbusUnit) -> None:
    api = await query._build_api(argparse.Namespace(model="lwz"), mock_modbus_unit)

    assert type(api) is LwzStiebelEltronAPI
    assert not mock_modbus_unit.read_events
