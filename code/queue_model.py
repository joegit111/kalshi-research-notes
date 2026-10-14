"""A toy price-time queue, to show why queue position decides a maker's result.

This is a SIMULATION on synthetic data. It is not fitted to any Kalshi tape. It
illustrates the mechanism the real research kept finding: on a one-cent
spread, a resting order at the back of the queue fills mainly when the level
is about to be run through by informed flow, while an order at the front fills
on ordinary noise trades and gets to keep the spread.

Model, per market:
  * A resting one-lot bid at price p with `ahead` contracts queued in front.
  * Uninformed takers arrive as a Poisson stream and eat the queue from the
    front. If they reach our lot before anything else happens, we fill and
    the next price is unchanged: we earn the half-spread.
  * With probability `p_info` per market an informed move happens at a random
    time. It sweeps the whole level, so everyone fills, and the price then
    sits `adverse_cents` against us.
  * Everyone ahead of us also cancels at a rate `cancel_rate`, which moves us
    forward without a trade.

The function returns the expected P&L per fill and the fill probability for a
given queue position. See tests/test_queue_model.py and `python queue_model.py`.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class QueueParams:
    half_spread_cents: float = 0.5     # earned on a benign fill
    adverse_cents: float = 2.0         # lost when the level is swept
    taker_rate: float = 1.0            # uninformed contracts per second
    cancel_rate: float = 0.01          # share of queue ahead cancelling per second
    p_info: float = 0.4                # chance the market sees an informed sweep
    horizon_s: float = 90.0            # we cancel if nothing happened by then


def simulate(ahead: int, params: QueueParams = QueueParams(), n_markets: int = 20000,
             seed: int = 0):
    """Monte Carlo over markets. Returns (fill_rate, mean_pnl_per_fill_cents, share_benign)."""
    rng = np.random.default_rng(seed)
    P = params
    # Time of the informed sweep (inf if none this market)
    sweep_t = np.where(rng.random(n_markets) < P.p_info,
                       rng.uniform(0, P.horizon_s, size=n_markets), np.inf)
    # Time until uninformed takers have eaten `ahead` contracts plus our lot,
    # accounting for cancellations shrinking the queue ahead. Discretise per second.
    benign_t = np.full(n_markets, np.inf)
    remaining = np.full(n_markets, float(ahead), dtype=np.float64)
    alive = np.ones(n_markets, dtype=bool)
    dt = 0.25
    t = 0.0
    while t < P.horizon_s and alive.any():
        eaten = rng.poisson(P.taker_rate * dt, size=n_markets)
        cancelled = rng.binomial(np.maximum(remaining.astype(int), 0), P.cancel_rate * dt)
        remaining = remaining - cancelled - eaten
        newly = alive & (remaining < 0)          # takers reached our lot
        benign_t[newly] = t + dt
        alive &= ~newly
        t += dt
    filled_benign = benign_t < sweep_t
    filled_sweep = np.isfinite(sweep_t) & (sweep_t <= benign_t)
    filled = filled_benign | filled_sweep
    pnl = np.where(filled_benign, P.half_spread_cents, 0.0) + \
        np.where(filled_sweep, -P.adverse_cents, 0.0)
    fill_rate = filled.mean()
    mean_pnl = pnl[filled].mean() if filled.any() else float("nan")
    share_benign = filled_benign.sum() / max(filled.sum(), 1)
    return float(fill_rate), float(mean_pnl), float(share_benign)


if __name__ == "__main__":
    print("queue ahead  fill rate  benign share  P&L per fill (c)")
    for ahead in (0, 10, 50, 200, 500, 1000):
        fr, pnl, benign = simulate(ahead)
        print(f"{ahead:>11}  {fr:>9.2f}  {benign:>12.2f}  {pnl:>+17.2f}")
    print("\nSIMULATED on synthetic data; the shape, not the numbers, is the point.")
