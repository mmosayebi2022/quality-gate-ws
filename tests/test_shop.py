import pytest
from app.shop import calculate_total, apply_discount


def test_calculate_total():
    assert calculate_total([10, 20, 30]) == 60


def test_apply_discount():
    assert apply_discount(100, 10) == 90


def test_apply_discount_invalid_percent():
    with pytest.raises(ValueError):
        apply_discount(100, 150)


def test_calculate_tax():
    from app.shop import calculate_tax
    assert calculate_tax(100, "DE", True, True) == 0
    assert calculate_tax(100, "DE", False, False) == 19.0
    assert calculate_tax(100, "FR", True, False) == 20.0
    assert calculate_tax(100, "US", False, False) == 10.0
