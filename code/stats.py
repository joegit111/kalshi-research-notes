"""Two statistics helpers used throughout the Kalshi research, rewritten cleanly.

1. cr1(): a cluster-robust (CR1) weighted mean with a 95% interval.
   Trades on the same day (or in the same game) are not independent, so the
   standard error is built from per-cluster score sums and scaled by G/(G-1).
   With few clusters the critical value comes from the t distribution with
   G-1 degrees of freedom, not from 1.96. On this project G was often 11 to
   22 days; a known-truth simulation put CR1 coverage at 93.8% to 96.1%
   against a 95% target, so the t correction is what makes it honest.

2. westfall_young_maxt(): a step-down max-t multiplicity correction using a
   wild cluster bootstrap with Rademacher signs. One sign vector per draw is
   applied to every cell at once, which preserves the correlation between
   cells. A cell is significant at the family-wise 5% level only if its |t|
   exceeds the 95th percentile of the max |t*| across cells under the null.
   Applied to the 40 cells that could be rebuilt (two families of 20, August
   and September, out of 440 registered), it took August's 14 per-cell
   significant cells to 11 and September's 5 to 4; the headline cell survived.
   The other 400 cells were never corrected. The lesson was not that the
   estimator was wrong; it was that quoting the winners out of a big grid is.

Both functions are pure numpy and run on synthetic data in tests/test_stats.py.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Two-sided 97.5% t critical values by degrees of freedom (scipy is deliberately
# not a dependency). Above 30 df the normal 1.96 is used.
_T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447,
         7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179,
         13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101,
         19: 2.093, 20: 2.086, 21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064,
         25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045}


def tcrit(n_clusters: int) -> float:
    df = n_clusters - 1
    if df >= 30:
        return 1.96
    if df < 1:
        raise ValueError("need at least 2 clusters")
    return _T975[df]


@dataclass
class ClusterResult:
    n: int
    weight: float
    mean: float
    n_clusters: int
    se: float
    lo: float
    hi: float
    t: float

    def excludes_zero(self) -> bool:
        return self.lo > 0 or self.hi < 0


def cr1(x, w=None, cluster=None) -> ClusterResult:
    """Weighted mean of x with a CR1 cluster-robust 95% interval.

    x: outcomes (e.g. cents per contract). w: weights (e.g. contracts), default 1.
    cluster: integer or string ids (e.g. settlement date). Default: one cluster per row.
    """
    x = np.asarray(x, dtype=np.float64)
    n = x.size
    if n == 0:
        raise ValueError("empty sample")
    w = np.ones(n) if w is None else np.asarray(w, dtype=np.float64)
    cluster = np.arange(n) if cluster is None else np.asarray(cluster)
    if w.shape != x.shape or cluster.shape != x.shape:
        raise ValueError("x, w and cluster must have the same length")
    W = float(w.sum())
    if W <= 0:
        raise ValueError("weights must sum to a positive number")
    mean = float((x * w).sum() / W)
    _, inv = np.unique(cluster, return_inverse=True)
    G = int(inv.max()) + 1
    if G < 2:
        raise ValueError("need at least 2 clusters for a standard error")
    scores = np.bincount(inv, weights=w * (x - mean), minlength=G)
    var = (G / (G - 1)) * float((scores ** 2).sum()) / (W * W)
    se = float(np.sqrt(var))
    t = tcrit(G)
    tstat = mean / se if se > 0 else float("inf")
    return ClusterResult(n=n, weight=W, mean=mean, n_clusters=G, se=se,
                         lo=mean - t * se, hi=mean + t * se, t=tstat)


def _cluster_t(x, w, inv, G, null_mean=0.0):
    """t statistic of the weighted mean against null_mean, CR1 variance."""
    W = w.sum()
    mean = (x * w).sum() / W
    scores = np.bincount(inv, weights=w * (x - mean), minlength=G)
    var = (G / (G - 1)) * (scores ** 2).sum() / (W * W)
    se = np.sqrt(var)
    return (mean - null_mean) / se if se > 0 else np.inf


@dataclass
class MaxTResult:
    t_obs: np.ndarray            # per-cell observed |t|
    crit_per_cell: float         # t critical a single cell would use
    crit_family: float           # 95th percentile of max |t*| across cells
    significant_per_cell: np.ndarray
    significant_family: np.ndarray
    adjusted_p: np.ndarray       # step-down adjusted p-values


def westfall_young_maxt(cells, cluster, weights=None, n_draws=2000, seed=0,
                        alpha=0.05) -> MaxTResult:
    """Step-down max-t family-wise correction over several cells sharing clusters.

    cells: list of 1-D arrays, one per hypothesis, each aligned with `cluster`.
           Rows not belonging to a cell should be NaN.
    cluster: cluster id per row (shared across cells, which is the point).
    weights: optional per-row weights.

    Under the null each cell's outcome is centred (restricted residuals), then
    every cluster's residuals are multiplied by the same +1/-1 draw across all
    cells. The max |t*| over cells is recorded per draw. A cell with observed
    |t| above the 95th percentile of that max distribution is family-wise
    significant. Step-down: after the largest cell is judged, the max is
    recomputed over the remaining cells, so later cells face a smaller bar
    (Westfall and Young 1993, Algorithm 2.8).
    """
    rng = np.random.default_rng(seed)
    cluster = np.asarray(cluster)
    _, inv_all = np.unique(cluster, return_inverse=True)
    G = int(inv_all.max()) + 1
    if G < 2:
        raise ValueError("need at least 2 clusters")
    n = cluster.size
    weights = np.ones(n) if weights is None else np.asarray(weights, dtype=np.float64)

    prepared = []
    t_obs = np.empty(len(cells))
    for k, c in enumerate(cells):
        c = np.asarray(c, dtype=np.float64)
        if c.shape != cluster.shape:
            raise ValueError(f"cell {k} length {c.size} != {n}")
        ok = np.isfinite(c)
        x, w, inv = c[ok], weights[ok], inv_all[ok]
        if np.unique(inv).size < 2:
            raise ValueError(f"cell {k} spans fewer than 2 clusters")
        t_obs[k] = abs(_cluster_t(x, w, inv, G))
        resid = x - (x * w).sum() / w.sum()   # null imposed
        prepared.append((resid, w, inv))

    K = len(cells)
    t_star = np.empty((n_draws, K))
    for d in range(n_draws):
        signs = rng.choice([-1.0, 1.0], size=G)   # one vector for every cell
        for k, (resid, w, inv) in enumerate(prepared):
            t_star[d, k] = abs(_cluster_t(resid * signs[inv], w, inv, G))

    # Step-down: order cells by observed |t| descending; the bar for cell j is
    # the max over cells j..K-1 of each draw.
    order = np.argsort(-t_obs)
    adjusted = np.empty(K)
    crit_fam = float(np.quantile(t_star.max(axis=1), 1 - alpha))
    prev = 0.0
    for rank, k in enumerate(order):
        remaining = order[rank:]
        max_rem = t_star[:, remaining].max(axis=1)
        p = (1 + (max_rem >= t_obs[k]).sum()) / (n_draws + 1)
        p = max(p, prev)                       # enforce monotonicity
        adjusted[k] = p
        prev = p
    crit_cell = tcrit(G)
    return MaxTResult(t_obs=t_obs, crit_per_cell=crit_cell, crit_family=crit_fam,
                      significant_per_cell=t_obs > crit_cell,
                      significant_family=adjusted < alpha, adjusted_p=adjusted)


def demo(n_datasets=40):
    """Synthetic illustration: 20 cells with NO true effect, sharing 15 day clusters.

    Each cell is a different cut of the same days (as when one tape is re-cut
    by side, latency, queue model and so on). For each dataset we ask: was at
    least one cell called significant? One at a time, that happens more often
    than 5% (5 of 40 datasets in the default run, against 2 of 40 after the
    correction).
    Run: python stats.py
    """
    G, per_day, K = 15, 200, 20
    cluster = np.repeat(np.arange(G), per_day)
    any_per_cell, any_family, fam_crits = 0, 0, []
    for seed in range(n_datasets):
        rng = np.random.default_rng(seed)
        day_shock = rng.normal(0, 0.6, size=G)[cluster]
        cells = [day_shock + rng.normal(0, 3.0, size=G * per_day) for _k in range(K)]
        res = westfall_young_maxt(cells, cluster, n_draws=400, seed=seed)
        any_per_cell += bool(res.significant_per_cell.any())
        any_family += bool(res.significant_family.any())
        fam_crits.append(res.crit_family)
    print(f"{n_datasets} synthetic datasets x {K} null cells, {G} day clusters")
    print(f"per-cell t critical {tcrit(G):.3f}; family-wise critical about {np.mean(fam_crits):.3f}")
    print(f"datasets with at least one 'significant' cell, one at a time: {any_per_cell} of {n_datasets}")
    print(f"datasets with at least one significant cell after Westfall-Young: {any_family} of {n_datasets}")


if __name__ == "__main__":
    demo()
