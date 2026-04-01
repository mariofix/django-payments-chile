from __future__ import annotations

from django_payments_chile.version import __version__


def test_version():
    actual = __version__
    expected = "2026.4.0"
    if actual != expected:
        raise AssertionError(f"Expected version {expected}, got {actual}")
