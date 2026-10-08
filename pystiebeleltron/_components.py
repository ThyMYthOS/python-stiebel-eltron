"""Reading the components of one controller, including the ones it may not serve."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from typing import Mapping

from modbus_connection import IllegalDataAddressError, ModbusUnit
from modbus_connection.model import Component, ComponentGroup, Raw

from ._read_retry import ReadStartRetry

_LOGGER = logging.getLogger(__package__)


def _merge_raw(
    into: Raw,
    more: Mapping[str, Mapping[int, int | bool]],
) -> None:
    """Merge a raw ``{space: {address: value}}`` map into an accumulator in place."""
    for space, values in more.items():
        into.setdefault(space, {}).update(values)


def _sorted_raw(raw: Raw) -> Raw:
    """The same raw map with every space's addresses ascending."""
    return {space: dict(sorted(values.items())) for space, values in raw.items()}


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
    device on that address - is not dropped: its values would otherwise read as
    current until the object is rebuilt, and clearing them would take a public
    way to invalidate a ``Component``'s cache, which ``modbus_connection`` does
    not expose. The refusal fails the poll instead, and the block is read again
    on the next one.

    With retry_register_start, polls retry an illegal-address register read once from a start already
    answered in the same poll, if the expanded read fits within 125 registers.
    Input and holding starts are tracked separately; writes never retry. Each
    refused block costs one failed request and at most one extra read per poll.
    Other errors are unchanged. An anchor does not guarantee the retry succeeds.
    Optional blocks recovered this way remain in the poll: their returned words
    are decoded normally, including the unavailable sentinel. A successful
    expanded read does not establish that every included register exists.

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
        *,
        retry_register_start: bool = False,
    ) -> None:
        """Pool ``required`` into one read; read each of ``optional`` on its own."""
        self._read_retry = ReadStartRetry(unit) if retry_register_start else None
        self._poll_lock = asyncio.Lock()
        read_unit: ModbusUnit = self._read_retry if self._read_retry is not None else unit
        self._required = list(required)
        self._group = ComponentGroup(read_unit, self._required)
        self._optional = list(optional)
        self._optional_readers: dict[Component, Component | ComponentGroup] = {
            component: ComponentGroup(read_unit, [component]) if self._read_retry is not None else component
            for component in self._optional
        }
        # Optional components the controller has answered at least once, and
        # those of them whose refusal has been logged since their last answer.
        self._served: list[Component] = []
        self._refusal_logged: list[Component] = []

    def _mark_served(self, component: Component) -> None:
        """Remember that the controller has answered this optional component."""
        if component not in self._served:
            self._served.append(component)
        if component in self._refusal_logged:
            self._refusal_logged.remove(component)

    def _drop_unserved(self, component: Component, err: IllegalDataAddressError) -> None:
        """Stop reading a refused optional component, unless it was answered before.

        A refusal of a block the controller has served is a failed read: the
        error propagates and fails the poll, so its listeners go stale instead
        of showing the last values as current.
        """
        if component in self._served:
            # The read error alone looks like a controller without the block,
            # so say once why the poll fails until the block is answered again.
            if component not in self._refusal_logged:
                self._refusal_logged.append(component)
                _LOGGER.warning(
                    "The controller refused the registers of %s although it answered them before, so polls fail until it answers them again; reload the integration if this persists: %s",
                    type(component).__name__,
                    err,
                )
            raise err
        self._optional.remove(component)
        del self._optional_readers[component]
        _LOGGER.info(
            "The controller does not serve the registers of %s, so they stay unavailable and are not read again: %s",
            type(component).__name__,
            err,
        )

    async def async_update(self) -> None:
        """Read the required components, then the optional ones still in play.

        Raises whatever the pooled read raises. An optional block answered with
        illegal data address is not an error of the poll: that is how a
        controller says it does not have the block. Any other answer means the
        registers are there and the read went wrong, so it fails the poll and
        the block is read again next time. So does illegal data address for a
        block the controller has already answered: it has the registers, and
        dropping the block would keep its last values as if they were current.

        Nothing is notified until every read that could still fail the poll has
        succeeded. Reading in sequence would otherwise let a poll tell listeners
        the required values are fresh and then raise over a later optional
        block, leaving them acting on half a poll - which one pooled read never
        did.
        """
        async with self._poll_lock:
            if self._read_retry is not None:
                self._read_retry.begin_poll()
            await self._group.async_update(notify=False)
            updated = []
            for component in list(self._optional):
                try:
                    await self._optional_readers[component].async_update(notify=False)
                # The only answer that means "not built in": device failure and
                # device busy both say the registers are there and the read went
                # wrong, so they stay uncaught and fail the poll.
                except IllegalDataAddressError as err:
                    self._drop_unserved(component, err)
                else:
                    self._mark_served(component)
                    updated.append(component)

            for component in (*self._required, *updated):
                component.notify()

    async def async_read_raw(self) -> Raw:
        """Read every component the controller serves, in one poll."""
        async with self._poll_lock:
            if self._read_retry is not None:
                self._read_retry.begin_poll()
            raw: Raw = await self._group.async_read_raw(notify=False)

            updated = []
            for component in list(self._optional):
                try:
                    _merge_raw(raw, await self._optional_readers[component].async_read_raw(notify=False))
                # The only answer that means "not built in": device failure and
                # device busy both say the registers are there and the read went
                # wrong, so they stay uncaught and fail the poll.
                except IllegalDataAddressError as err:
                    self._drop_unserved(component, err)
                else:
                    self._mark_served(component)
                    updated.append(component)

            for component in (*self._required, *updated):
                component.notify()

            return _sorted_raw(raw)
