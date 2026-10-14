"""Kalshi trading fee, reproduced from the published fee schedule.

The schedule (kalshi.com/docs/kalshi-fee-schedule.pdf, "Last updated and
effective: July 7, 2026") gives the taker fee in dollars as

    fees = round up(M x 0.07 x C x P x (1 - P))

    P = contract price in dollars, C = number of contracts,
    M = per-series multiplier (default 1 for takers, 0 for makers).

Two details decide whether a fee model is right, and both were checked against
the 42 cells of the PDF's General Trading Fees Table (21 prices, at 1 contract
and at 100 contracts). See tests/test_fees.py for the 42 values.

1. The published table rounds up to the whole cent, and fee_cents reproduces
   it exactly. Round-to-nearest matches only 22 of the 42 cells (it misses 5c,
   15c, 25c, 35c, 45c and their mirrors at 100 contracts). Production is finer:
   it rounds up to the centicent ($0.0001), which is what the account's fills
   show (1.74c at 55c, 1.50c at 31c). production_fee_cents models that.
2. C sits inside the round-up, so rounding happens once per order, not once per
   contract. 100 contracts at 1c cost $0.07 in fees, not $1.00. Per-contract
   rounding would make every cheap long-shot untradeable, and it is wrong.

A third detail bit an earlier version of this function: floating point.
0.07 * 100 * 0.10 * 0.90 * 100 evaluates to 63.00000000000002, and a ceiling
pushes that to 64 cents instead of 63. Exact fractions avoid it.

Maker fills carry M = 0 on the general schedule, which matches what the
production fills endpoint reported on the account used for this research
(every maker fill: fee_cost 0.000000; taker fills: 1.50c and 1.74c, see
production_fee_cents).
"""
from __future__ import annotations

import math
from fractions import Fraction

TAKER_RATE = Fraction(7, 100)      # 0.07
MAKER_RATE = Fraction(175, 10000)  # 0.0175, applies only where M != 0


def fee_cents(price_cents: int, contracts: int = 1, multiplier: Fraction | float = 1,
              rate: Fraction = TAKER_RATE) -> int:
    """Fee in whole cents for one order of `contracts` lots at `price_cents`.

    Ceiling to the cent, rounding applied once per order. Exact arithmetic.
    """
    if not 1 <= price_cents <= 99:
        raise ValueError(f"price must be 1..99 cents, got {price_cents}")
    if contracts < 1:
        raise ValueError(f"contracts must be >= 1, got {contracts}")
    m = Fraction(str(multiplier)) if not isinstance(multiplier, Fraction) else multiplier
    if m == 0:
        return 0
    p = Fraction(price_cents, 100)
    exact_dollars = m * rate * contracts * p * (1 - p)
    return math.ceil(exact_dollars * 100)


def taker_fee_cents(price_cents: int, contracts: int = 1) -> int:
    return fee_cents(price_cents, contracts, 1, TAKER_RATE)


def production_fee_cents(price_cents: int, contracts: int = 1) -> Fraction:
    """Taker fee in cents as production charges it: ceiling to the centicent
    ($0.0001), once per order. Returns an exact Fraction of a cent."""
    if not 1 <= price_cents <= 99:
        raise ValueError(f"price must be 1..99 cents, got {price_cents}")
    p = Fraction(price_cents, 100)
    exact_dollars = TAKER_RATE * contracts * p * (1 - p)
    return Fraction(math.ceil(exact_dollars * 10000), 100)


def maker_fee_cents(price_cents: int, contracts: int = 1, multiplier: Fraction | float = 0) -> int:
    """Maker fee. Zero on the general schedule; non-zero only for listed series."""
    return fee_cents(price_cents, contracts, multiplier, MAKER_RATE)


def round_trip_taker_cents(price_cents: int, contracts: int = 1) -> int:
    """Fee to take in and take out at the same price (the floor a taker edge must clear)."""
    return 2 * taker_fee_cents(price_cents, contracts)


def fee_per_contract_cents(price_cents: int, contracts: int = 1) -> float:
    """Average fee per contract, which falls as the order grows (rounding is per order)."""
    return taker_fee_cents(price_cents, contracts) / contracts


if __name__ == "__main__":
    print("price  1-lot  100-lot  fee/contract@100")
    for pc in (1, 5, 10, 25, 50, 75, 90, 95, 99):
        print(f"{pc:>5}  {taker_fee_cents(pc):>5}  {taker_fee_cents(pc, 100):>7}"
              f"  {fee_per_contract_cents(pc, 100):>16.2f}")
