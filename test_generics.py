#!/usr/bin/env python3
"""Test script to verify the generic Property implementation."""

from pystiebeleltron.wpm_can import (
    Property,
    DecimalType,
    BoolType,
    DefaultType,
    WPMProperties,
)


def test_decimal_type():
    """Test DecimalType serialization/deserialization."""
    converter = DecimalType()

    # Test positive value
    assert converter.deserialize(250) == 25.0
    assert converter.serialize(25.0) == 250

    # Test negative value (two's complement)
    assert converter.deserialize(0xFFF6) == -1.0  # -10 in 0.1 units
    assert converter.serialize(-1.0) == 0xFFF6

    print("✓ DecimalType tests passed")


def test_bool_type():
    """Test BoolType serialization/deserialization."""
    converter = BoolType()

    assert converter.deserialize(0) is False
    assert converter.deserialize(1) is True
    assert converter.serialize(True) == 1
    assert converter.serialize(False) == 0

    print("✓ BoolType tests passed")


def test_property_class():
    """Test Property class with generics."""
    # Create a property with DecimalType
    temp_prop: Property[float] = Property("TEST_TEMP", 0x1234, DecimalType())

    # Test serialization through property
    raw = temp_prop.serialize(25.5)
    assert raw == 255

    # Test deserialization through property
    value = temp_prop.deserialize(255)
    assert value == 25.5

    print("✓ Property class tests passed")


def test_wpm_properties():
    """Test WPMProperties class."""
    # Verify properties are properly typed
    assert isinstance(WPMProperties.AUSSENTEMP.type_converter, DecimalType)
    assert isinstance(WPMProperties.KUEHLMODE.type_converter, BoolType)
    assert isinstance(WPMProperties.BETRIEBS_STATUS.type_converter, DefaultType)

    # Test a specific property
    temp = WPMProperties.AUSSENTEMP
    assert temp.name == "AUSSENTEMP"
    assert temp.id == 0x000c

    # Test serialization/deserialization
    raw = temp.serialize(15.5)
    assert raw == 155
    value = temp.deserialize(155)
    assert value == 15.5

    print("✓ WPMProperties tests passed")


if __name__ == "__main__":
    test_decimal_type()
    test_bool_type()
    test_property_class()
    test_wpm_properties()
    print("\n✅ All tests passed!")
