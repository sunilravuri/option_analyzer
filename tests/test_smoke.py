"""Smoke test to verify the package imports correctly."""

from option_analyzer import __version__


def test_version():
    assert __version__ == "0.1.0"
