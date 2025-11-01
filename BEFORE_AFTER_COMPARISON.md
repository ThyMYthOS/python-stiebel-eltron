# Before/After Comparison: Property Refactoring

## Property Type System

### Before (Enum-based)
```python
class PropertyType(Enum):
    """Property value types."""
    DEC_VAL = "dec_val"      # Decimal (×0.1)
    CENT_VAL = "cent_val"    # Centimal (×0.01)
    BOOL = "bool"            # Boolean
    BYTE = "byte"            # Single byte
    LITTLE_ENDIAN = "little" # Little endian uint16
    LITTLE_BOOL = "little_bool"  # Little endian bool
    BETRIEBSART = "betriebsart"  # Operating mode
    DOUBLE_VAL = "double_val"    # Double word (not implemented)
```

### After (OOP with Generics)
```python
class PropertyType(ABC, Generic[T]):
    """Base class for property type converters."""

    @abstractmethod
    def deserialize(self, raw_value: int) -> T:
        """Convert raw uint16 value to typed value."""
        pass

    @abstractmethod
    def serialize(self, value: T) -> int:
        """Convert typed value to raw uint16."""
        pass

# Concrete implementations
class DecimalType(PropertyType[float]):
    def deserialize(self, raw_value: int) -> float:
        signed_value = raw_value - 0x10000 if raw_value > 0x7FFF else raw_value
        return signed_value * 0.1

    def serialize(self, value: float) -> int:
        raw = int(round(value * 10))
        if raw < 0:
            raw = raw + 0x10000
        return raw & 0xFFFF

class BoolType(PropertyType[bool]):
    def deserialize(self, raw_value: int) -> bool:
        return bool(raw_value)

    def serialize(self, value: bool) -> int:
        return 1 if value else 0

# ... and 6 more concrete types
```

## Property Class

### Before
```python
@dataclass
class Property:
    """Represents a CAN bus property."""
    name: str
    id: int
    type: PropertyType = PropertyType.DEC_VAL  # Enum value
```

### After
```python
@dataclass
class Property(Generic[T]):
    """Represents a CAN bus property with type-safe serialization."""
    name: str
    id: int
    type_converter: PropertyType[T]  # Converter instance

    def deserialize(self, raw_value: int) -> T:
        """Deserialize raw value to typed value."""
        return self.type_converter.deserialize(raw_value)

    def serialize(self, value: T) -> int:
        """Serialize typed value to raw value."""
        return self.type_converter.serialize(value)
```

## Property Definitions

### Before
```python
class WPMProperties:
    """Common properties for WPM heat pumps."""

    # System temperatures
    AUSSENTEMP = Property("AUSSENTEMP", 0x000c, PropertyType.DEC_VAL)
    SPEICHERISTTEMP = Property("SPEICHERISTTEMP", 0x000e, PropertyType.DEC_VAL)
    SPEICHERSOLLTEMP = Property("SPEICHERSOLLTEMP", 0x0003, PropertyType.DEC_VAL)

    # Heat pump status
    BETRIEBS_STATUS = Property("BETRIEBS_STATUS", 0x0176)  # No type specified
    PROGRAMMSCHALTER = Property("PROGRAMMSCHALTER", 0x0112, PropertyType.BETRIEBSART)
    FEHLERMELDUNG = Property("FEHLERMELDUNG", 0x0001)

    # Heating circuit
    STEIGUNG_HK1 = Property("STEIGUNG_HK1", 0x010e, PropertyType.CENT_VAL)
    HEIZUNGSDRUCK = Property("HEIZUNGSDRUCK", 0x4f46, PropertyType.CENT_VAL)

    # Cooling
    KUEHLMODE = Property("KUEHLMODE", 0x0287, PropertyType.BOOL)

    # Time
    JAHR = Property("JAHR", 0x0124, PropertyType.LITTLE_ENDIAN)
    MONAT = Property("MONAT", 0x0123, PropertyType.LITTLE_ENDIAN)
```

### After
```python
class WPMProperties:
    """Common properties for WPM heat pumps."""

    # System temperatures (with type annotations!)
    AUSSENTEMP: Property[float] = Property("AUSSENTEMP", 0x000c, DecimalType())
    SPEICHERISTTEMP: Property[float] = Property("SPEICHERISTTEMP", 0x000e, DecimalType())
    SPEICHERSOLLTEMP: Property[float] = Property("SPEICHERSOLLTEMP", 0x0003, DecimalType())

    # Heat pump status
    BETRIEBS_STATUS: Property[int] = Property("BETRIEBS_STATUS", 0x0176, DefaultType())
    PROGRAMMSCHALTER: Property[int] = Property("PROGRAMMSCHALTER", 0x0112, BetriebsartType())
    FEHLERMELDUNG: Property[int] = Property("FEHLERMELDUNG", 0x0001, DefaultType())

    # Heating circuit
    STEIGUNG_HK1: Property[float] = Property("STEIGUNG_HK1", 0x010e, CentimalType())
    HEIZUNGSDRUCK: Property[float] = Property("HEIZUNGSDRUCK", 0x4f46, CentimalType())

    # Cooling
    KUEHLMODE: Property[bool] = Property("KUEHLMODE", 0x0287, BoolType())

    # Time
    JAHR: Property[int] = Property("JAHR", 0x0124, LittleEndianType())
    MONAT: Property[int] = Property("MONAT", 0x0123, LittleEndianType())
```

## API Internal Methods

### Before
```python
class WPMCanAPI:
    def _convert_value_from_raw(self, raw_value: int, prop_type: PropertyType) -> Any:
        """Convert raw uint16 value to the appropriate type."""
        signed_value = raw_value - 0x10000 if raw_value > 0x7FFF else raw_value

        if prop_type == PropertyType.DEC_VAL:
            return signed_value * 0.1
        elif prop_type == PropertyType.CENT_VAL:
            return signed_value * 0.01
        elif prop_type == PropertyType.BOOL:
            return bool(raw_value)
        # ... many more elif statements
        else:
            return raw_value

    def _convert_value_to_raw(self, value: Any, prop_type: PropertyType) -> int:
        """Convert typed value to raw uint16."""
        if prop_type == PropertyType.DEC_VAL:
            raw = int(round(value * 10))
        elif prop_type == PropertyType.CENT_VAL:
            raw = int(round(value * 100))
        # ... many more elif statements
        else:
            raw = int(value)

        if raw < 0:
            raw = raw + 0x10000
        return raw & 0xFFFF
```

### After
```python
class WPMCanAPI:
    # No more conversion methods! Type conversion is delegated to PropertyType instances

    def write_property(self, property: Property[Any], value: Any, ...) -> None:
        # Convert using the property's type converter
        raw_value = property.type_converter.serialize(value)
        # ... rest of method

    def get_property_value(self, property: Property[Any]) -> Optional[Any]:
        raw_value = self._data.get(property.id)
        if raw_value is None:
            return None
        # Convert using the property's type converter
        return property.type_converter.deserialize(raw_value)
```

## Usage Comparison

### Before
```python
# Creating a property
temp = Property("MY_TEMP", 0x1234, PropertyType.DEC_VAL)  # Enum value

# API handled conversion internally
api.write_property(temp, 25.5)
value = api.get_property_value(temp)

# No direct access to conversion logic
# Had to modify WPMCanAPI._convert_value_to_raw() to add new types
```

### After
```python
# Creating a property with type annotation
temp: Property[float] = Property("MY_TEMP", 0x1234, DecimalType())

# API still handles conversion, but delegates to property
api.write_property(temp, 25.5)
value = api.get_property_value(temp)

# Direct access to conversion logic
raw = temp.serialize(25.5)      # 255
value = temp.deserialize(255)   # 25.5

# Or use converter directly
converter = DecimalType()
raw = converter.serialize(25.5)  # 255

# Adding new types is easy - just create a new PropertyType[T] subclass
class MyCustomType(PropertyType[MyType]):
    def deserialize(self, raw_value: int) -> MyType:
        # Custom logic
        pass

    def serialize(self, value: MyType) -> int:
        # Custom logic
        pass
```

## Key Improvements

1. **Type Safety**: Properties are now `Property[float]`, `Property[bool]`, `Property[int]` instead of untyped `Property`
2. **Extensibility**: New types can be added by subclassing `PropertyType[T]` without modifying existing code
3. **Encapsulation**: Each type knows how to serialize/deserialize itself
4. **Testability**: Type converters can be tested independently from the API
5. **Clarity**: No more giant if/elif chains - each converter is self-contained
6. **Maintainability**: Separation of concerns - API logic separate from type conversion
7. **IDE Support**: Better autocomplete and type checking with Generic[T]

## Migration Path

For users of the API, **no changes required**! The public API remains the same:
- `api.write_property(property, value)` - still works
- `api.get_property_value(property)` - still works
- `WPMProperties.AUSSENTEMP` - still works

Only internal implementation changed from enum-based to OOP generic-based.
