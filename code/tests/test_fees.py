"""The 42 cells of Kalshi's General Trading Fees Table, effective 2026-07-07.

Each row: (price in cents, fee for 1 contract in cents, fee for 100 contracts in cents).
Transcribed from kalshi.com/docs/kalshi-fee-schedule.pdf.
"""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fees import fee_cents, maker_fee_cents, taker_fee_cents  # noqa: E402

PUBLISHED_TABLE = [
    (1, 1, 7),
    (5, 1, 34),
    (10, 1, 63),
    (15, 1, 90),
    (20, 2, 112),
    (25, 2, 132),
    (30, 2, 147),
    (35, 2, 160),
    (40, 2, 168),
    (45, 2, 174),
    (50, 2, 175),
    (55, 2, 174),
    (60, 2, 168),
    (65, 2, 160),
    (70, 2, 147),
    (75, 2, 132),
    (80, 2, 112),
    (85, 1, 90),
    (90, 1, 63),
    (95, 1, 34),
    (99, 1, 7),
]


def test_table_has_42_cells():
    assert len(PUBLISHED_TABLE) * 2 == 42


@pytest.mark.parametrize("price,fee1,fee100", PUBLISHED_TABLE)
def test_matches_published_table(price, fee1, fee100):
    assert taker_fee_cents(price, 1) == fee1
    assert taker_fee_cents(price, 100) == fee100


def test_all_42_cells_at_once():
    hits = sum((taker_fee_cents(p, 1) == f1) + (taker_fee_cents(p, 100) == f100)
               for p, f1, f100 in PUBLISHED_TABLE)
    assert hits == 42


def test_round_to_nearest_would_fail():
    """Documents why ceiling was chosen: nearest-cent matches only 22 of 42 cells."""
    def nearest(price, c):
        return round(0.07 * c * (price / 100) * (1 - price / 100) * 100 + 1e-12)
    hits = sum((nearest(p, 1) == f1) + (nearest(p, 100) == f100)
               for p, f1, f100 in PUBLISHED_TABLE)
    assert hits == 22


def test_per_contract_rounding_would_fail():
    """Rounding each contract then multiplying gives $1.00 on 100 lots at 1c; the PDF says $0.07."""
    per_contract = 100 * taker_fee_cents(1, 1)
    assert per_contract == 100
    assert taker_fee_cents(1, 100) == 7


def test_float_ceiling_bug_is_avoided():
    """0.07*100*0.10*0.90*100 == 63.00000000000002 in floating point; ceil gives 64."""
    assert math.ceil(0.07 * 100 * 0.10 * 0.90 * 100) == 64
    assert taker_fee_cents(10, 100) == 63


def test_symmetry_in_price():
    for p in range(1, 100):
        assert taker_fee_cents(p, 100) == taker_fee_cents(100 - p, 100)


def test_maker_fee_zero_by_default():
    for p in (1, 50, 99):
        assert maker_fee_cents(p, 1000) == 0


def test_maker_fee_with_multiplier_one():
    # 0.0175 * 100 * 0.5 * 0.5 = $0.4375 -> 44 cents
    assert maker_fee_cents(50, 100, multiplier=1) == 44


def test_bad_inputs():
    with pytest.raises(ValueError):
        fee_cents(0)
    with pytest.raises(ValueError):
        fee_cents(100)
    with pytest.raises(ValueError):
        fee_cents(50, 0)


def test_production_rounds_to_centicent():
    from fractions import Fraction
    from fees import production_fee_cents
    assert production_fee_cents(55) == Fraction(174, 100)   # live fill, 1.74c
    assert production_fee_cents(31) == Fraction(150, 100)   # live fill, 1.50c
