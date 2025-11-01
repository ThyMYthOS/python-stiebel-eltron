# Async API Refactoring Summary

## Overview
Refactored the WPMCanAPI to be a pure async API using python-can's async capabilities. All blocking operations have been converted to async/await patterns.

## Key Changes

### 1. Connection Methods
**Before:**
```python
def connect(self) -> None:
    """Connect to the CAN bus."""

async def async_connect(self) -> None:
    """Asynchronously connect to the CAN bus."""
    self.connect()  # Wrapper around sync method
```

**After:**
```python
async def connect(self) -> None:
    """Connect to the CAN bus asynchronously."""
    # Direct async implementation
```

### 2. Message Listening
**Before:**
```python
def start_listening(self) -> None:
    """Start listening for CAN messages."""
    self._notifier = can.Notifier(self.bus, [self._handle_can_message])

def stop_listening(self) -> None:
    """Stop listening for CAN messages."""
    if self._notifier:
        self._notifier.stop()
```

**After:**
```python
async def _read_loop(self) -> None:
    """Async loop to read CAN messages."""
    reader = can.AsyncBufferedReader()
    notifier = can.Notifier(self.bus, [reader], loop=asyncio.get_running_loop())

    try:
        while self._running:
            msg = await reader.get_message()
            if msg:
                self._handle_can_message(msg)
    finally:
        notifier.stop()

async def start_listening(self) -> None:
    """Start listening for CAN messages asynchronously."""
    self._running = True
    self._reader_task = asyncio.create_task(self._read_loop())

async def stop_listening(self) -> None:
    """Stop listening for CAN messages asynchronously."""
    self._running = False
    if self._reader_task:
        self._reader_task.cancel()
        try:
            await self._reader_task
        except asyncio.CancelledError:
            pass
```

### 3. Property Operations
**Before:**
```python
def request_property(self, property: Property, ...) -> None:
    """Sync request"""

async def async_request_property(self, property: Property, ...) -> None:
    """Async wrapper"""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, self.request_property, property, member)
```

**After:**
```python
async def request_property(self, property: Property[Any], ...) -> None:
    """Pure async request - no executor needed"""
```

### 4. Context Manager
**Before:**
```python
def __enter__(self) -> "WPMCanAPI":
    """Sync context manager entry."""
    self.connect()
    return self

def __exit__(self, ...) -> None:
    """Sync context manager exit."""
    self.close()
```

**After:**
```python
async def __aenter__(self) -> "WPMCanAPI":
    """Async context manager entry."""
    await self.connect()
    await self.start_listening()
    return self

async def __aexit__(self, ...) -> None:
    """Async context manager exit."""
    await self.close()
```

## Removed Methods

All `async_*` wrapper methods have been removed since all methods are now async by default:
- ❌ `async_connect()` → ✅ `connect()`
- ❌ `async_close()` → ✅ `close()`
- ❌ `async_request_property()` → ✅ `request_property()`
- ❌ `async_write_property()` → ✅ `write_property()`
- ❌ `async_update()` → ✅ `update()`

## API Method Summary

### Async Methods (must use `await`)
- `async def connect() -> None` - Connect to CAN bus
- `async def close() -> None` - Disconnect from CAN bus
- `async def start_listening() -> None` - Start message reader loop
- `async def stop_listening() -> None` - Stop message reader loop
- `async def request_property(property, member=None) -> None` - Request property value
- `async def write_property(property, value, member=None) -> None` - Write property value
- `async def update(properties=None) -> None` - Request multiple properties

### Synchronous Methods (no `await` needed)
- `def get_property_value(property) -> Optional[Any]` - Get cached property value
- `def get_raw_value(property_id) -> Optional[int]` - Get cached raw value
- `def register_callback(property_id, callback) -> None` - Register update callback
- `def unregister_callback(property_id, callback) -> None` - Unregister callback

### Context Manager
- `async with WPMCanAPI(...) as api:` - Async context manager

## Usage Examples

### Basic Connection
**Before:**
```python
api = WPMCanAPI(interface='can0', bustype='socketcan')
await api.async_connect()
api.start_listening()

# Do work...

api.stop_listening()
await api.async_close()
```

**After:**
```python
api = WPMCanAPI(interface='can0', bustype='socketcan')
await api.connect()
await api.start_listening()

# Do work...

await api.stop_listening()
await api.close()
```

### Context Manager
**Before:**
```python
with WPMCanAPI(interface='can0') as api:  # Sync context manager
    api.start_listening()
    await api.async_request_property(prop)
```

**After:**
```python
async with WPMCanAPI(interface='can0') as api:  # Async context manager
    # start_listening() called automatically
    await api.request_property(prop)
```

### Request Properties
**Before:**
```python
await api.async_request_property(WPMProperties.AUSSENTEMP)
await asyncio.sleep(0.5)
temp = api.get_property_value(WPMProperties.AUSSENTEMP)
```

**After:**
```python
await api.request_property(WPMProperties.AUSSENTEMP)
await asyncio.sleep(0.5)
temp = api.get_property_value(WPMProperties.AUSSENTEMP)
```

### Write Properties
**Before:**
```python
await api.async_write_property(WPMProperties.KOMFORTTEMPERATUR, 21.5)
```

**After:**
```python
await api.write_property(WPMProperties.KOMFORTTEMPERATUR, 21.5)
```

### Update Multiple Properties
**Before:**
```python
await api.async_update([
    WPMProperties.AUSSENTEMP,
    WPMProperties.VORLAUFISTTEMP,
])
```

**After:**
```python
await api.update([
    WPMProperties.AUSSENTEMP,
    WPMProperties.VORLAUFISTTEMP,
])
```

## Benefits

1. **Cleaner API**: No more `async_*` prefix confusion - all I/O operations are async
2. **Better Performance**: Uses python-can's `AsyncBufferedReader` for true async message reading
3. **Proper Resource Management**: Async context manager handles cleanup correctly
4. **Task Cancellation**: Proper cancellation of background tasks with asyncio
5. **Consistency**: All methods follow the same async pattern
6. **Type Safety**: All maintained with Generic[T] property types

## Migration Guide

### Update All Method Calls

1. Replace `api.async_connect()` with `await api.connect()`
2. Replace `api.start_listening()` with `await api.start_listening()`
3. Replace `api.async_request_property()` with `await api.request_property()`
4. Replace `api.async_write_property()` with `await api.write_property()`
5. Replace `api.async_update()` with `await api.update()`
6. Replace `api.stop_listening()` with `await api.stop_listening()`
7. Replace `api.async_close()` with `await api.close()`
8. Replace `with WPMCanAPI() as api:` with `async with WPMCanAPI() as api:`

### Example Migration

**Before:**
```python
async def main():
    api = WPMCanAPI(interface='can0', bustype='socketcan')

    try:
        await api.async_connect()
        api.start_listening()

        await api.async_request_property(WPMProperties.AUSSENTEMP)
        await asyncio.sleep(0.5)

        temp = api.get_property_value(WPMProperties.AUSSENTEMP)
        print(f"Temperature: {temp}°C")

        await api.async_write_property(WPMProperties.KOMFORTTEMPERATUR, 21.5)

        await api.async_update()

    finally:
        api.stop_listening()
        await api.async_close()
```

**After:**
```python
async def main():
    api = WPMCanAPI(interface='can0', bustype='socketcan')

    try:
        await api.connect()
        await api.start_listening()

        await api.request_property(WPMProperties.AUSSENTEMP)
        await asyncio.sleep(0.5)

        temp = api.get_property_value(WPMProperties.AUSSENTEMP)
        print(f"Temperature: {temp}°C")

        await api.write_property(WPMProperties.KOMFORTTEMPERATUR, 21.5)

        await api.update()

    finally:
        await api.stop_listening()
        await api.close()
```

Or even simpler with async context manager:

**After (with context manager):**
```python
async def main():
    async with WPMCanAPI(interface='can0', bustype='socketcan') as api:
        await api.request_property(WPMProperties.AUSSENTEMP)
        await asyncio.sleep(0.5)

        temp = api.get_property_value(WPMProperties.AUSSENTEMP)
        print(f"Temperature: {temp}°C")

        await api.write_property(WPMProperties.KOMFORTTEMPERATUR, 21.5)
        await api.update()
```

## Technical Details

### AsyncBufferedReader
The API now uses python-can's `AsyncBufferedReader` which:
- Provides a queue-based async interface for CAN messages
- Integrates properly with asyncio event loop
- Allows proper cancellation and cleanup
- Eliminates need for thread executors

### Task Management
- Background reader task is created with `asyncio.create_task()`
- Task is properly cancelled and awaited during shutdown
- Handles `asyncio.CancelledError` gracefully

### No Sync API
The API is now **pure async** - there are no synchronous versions of I/O operations. This enforces proper async usage patterns and prevents blocking the event loop.
