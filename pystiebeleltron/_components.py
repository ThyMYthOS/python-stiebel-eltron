"""Reading the components of one controller, including the ones it may not serve."""

from __future__ import annotations

import logging
from collections.abc import Iterable

from modbus_connection import BlockReadError, ModbusUnit
from modbus_connection.model import Component, ComponentGroup

_LOGGER = logging.getLogger(__package__)


class ControllerComponents:
    """The components of one controller, refreshed in one poll.

    Stiebel documents register blocks that not every controller and firmware
    actually serves - the energy-management extension, the inverter and
    efficiency figures - and no register says which of them a given machine has.
    A controller answers a read of a block it does not implement with a Modbus
    exception (illegal data address), and one such block fails an entire pooled
    read, so a machine without an optional block could not be read at all.

    Hence the split: the components every controller serves are pooled into one
    set of block reads and still fail the poll when they fail, because then
    something is genuinely wrong. An optional component is read on its own, and
    the first time the controller refuses it, it is dropped for the life of this
    object - its fields keep reading as ``None``, the same as a value the
    controller reports as unavailable, and no later poll wastes a round trip on
    it.

    An optional component costs one extra read per poll while the controller
    does serve it. That is the price of being able to tell "this machine does
    not have it" from "this read failed", which the protocol itself does not
    distinguish.
    """

    def __init__(
        self,
        unit: ModbusUnit,
        required: Iterable[Component],
        optional: Iterable[Component] = (),
    ) -> None:
        """Pool ``required`` into one read; read each of ``optional`` on its own."""
        self._group = ComponentGroup(unit, required)
        self._optional = list(optional)

    async def async_update(self) -> None:
        """Read the required components, then the optional ones still in play.

        Raises whatever the pooled read raises. A ``BlockReadError`` from an
        optional component is not an error of the poll: it is how a controller
        says it does not have that block.
        """
        await self._group.async_update()
        for component in list(self._optional):
            try:
                await component.async_update()
            except BlockReadError as err:
                self._optional.remove(component)
                _LOGGER.info(
                    "The controller does not serve the registers of %s, so they stay unavailable and are not read again: %s",
                    type(component).__name__,
                    err,
                )
