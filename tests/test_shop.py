import pytest
from app.shop import calculate_total, apply_discount


def test_calculate_total():
    assert calculate_total([10, 20, 30]) == 60


def test_apply_discount():
    assert apply_discount(100, 10) == 90


def test_apply_discount_invalid_percent():
    with pytest.raises(ValueError):
        apply_discount(100, 150)
