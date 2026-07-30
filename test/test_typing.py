"""Tests for the package typing contract."""

from importlib.resources import files


def test_package_declares_pep561_typing() -> None:
    """Downstream type checkers can discover the inline annotations."""
    assert files("pystiebeleltron").joinpath("py.typed").is_file()
