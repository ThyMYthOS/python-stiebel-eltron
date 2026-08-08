"""Reading the components of one controller, including the ones it may not serve."""

from __future__ import annotations

import logging
from collections.abc import Iterable

from modbus_connection import BlockReadError, ExceptionCode, ModbusUnit
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
    object, so no later poll wastes a round trip on it.

    A machine that does not have the block refuses it on the very first read,
    before any value was stored, so its fields read ``None`` from then on, the
    same as a value the controller reports as unavailable. A block that answered
    once and is refused later - a module switched off, new firmware, a different
    device on that address - keeps the values of its last successful read
    instead, until the object is rebuilt. Clearing them would take a public way
    to invalidate a ``Component``'s cache, which ``modbus_connection`` does not
    expose.

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
        self._required = list(required)
        self._group = ComponentGroup(unit, self._required)
        self._optional = list(optional)

    async def async_update(self) -> None:
        """Read the required components, then the optional ones still in play.

        Raises whatever the pooled read raises. An optional block answered with
        illegal data address is not an error of the poll: that is how a
        controller says it does not have the block. Any other answer means the
        registers are there and the read went wrong, so it fails the poll and
        the block is read again next time.

        Nothing is notified until every read that could still fail the poll has
        succeeded. Reading in sequence would otherwise let a poll tell listeners
        the required values are fresh and then raise over a later optional
        block, leaving them acting on half a poll - which one pooled read never
        did.
        """
        await self._group.async_update(notify=False)
        updated = []
        for component in list(self._optional):
            try:
                await component.async_update(notify=False)
            except BlockReadError as err:
                # The only answer that means "not built in": device failure and
                # device busy both say the registers are there and the read
                # went wrong.
                if err.exception_code != ExceptionCode.ILLEGAL_DATA_ADDRESS:
                    raise
                self._optional.remove(component)
                _LOGGER.info(
                    "The controller does not serve the registers of %s, so they stay unavailable and are not read again: %s",
                    type(component).__name__,
                    err,
                )
            else:
                updated.append(component)

        for component in (*self._required, *updated):
            component.notify()
