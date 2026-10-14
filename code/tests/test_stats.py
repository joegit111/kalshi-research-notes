import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stats import cr1, tcrit, westfall_young_maxt  # noqa: E402


def test_tcrit_values():
    assert tcrit(21) == 2.086
    assert tcrit(11) == 2.228
    assert tcrit(31) == 1.96
    with pytest.raises(ValueError):
        tcrit(1)


def test_cr1_matches_reference_implementation():
    """Vectorised cr1 must match a plain-Python loop version to 1e-12."""
    rng = np.random.default_rng(7)
    for n, g in ((1000, 22), (37, 3), (5, 2)):
        x = rng.normal(size=n) * 30
        w = rng.integers(1, 500, size=n).astype(float)
        c = rng.integers(0, g, size=n)
        r = cr1(x, w, c)
        W = w.sum()
        mean = (x * w).sum() / W
        by = {}
        for xi, wi, ci in zip(x, w, c):
            by[ci] = by.get(ci, 0.0) + wi * (xi - mean)
        G = len(by)
        var = (G / (G - 1)) * sum(s * s for s in by.values()) / (W * W)
        assert abs(r.mean - mean) < 1e-12
        assert abs(r.se - var ** 0.5) < 1e-12
        assert r.n_clusters == G


def test_cr1_coverage_near_nominal_with_day_effects():
    """Known truth 0 with shared day shocks: CR1 with t(G-1) covers about 95%."""
    rng = np.random.default_rng(3)
    G, per_day, reps = 12, 100, 600
    cover = 0
    for _ in range(reps):
        cluster = np.repeat(np.arange(G), per_day)
        x = rng.normal(0, 1, size=G)[cluster] + rng.normal(0, 2, size=G * per_day)
        r = cr1(x, None, cluster)
        cover += (r.lo <= 0 <= r.hi)
    rate = cover / reps
    assert 0.91 <= rate <= 0.985, rate


def test_cr1_naive_se_undercovers_when_days_are_correlated():
    """The reason for clustering: an iid standard error is far too narrow here."""
    rng = np.random.default_rng(4)
    G, per_day, reps = 12, 100, 400
    cover_naive = 0
    for _ in range(reps):
        cluster = np.repeat(np.arange(G), per_day)
        x = rng.normal(0, 1, size=G)[cluster] + rng.normal(0, 2, size=G * per_day)
        se_naive = x.std(ddof=1) / np.sqrt(x.size)
        m = x.mean()
        cover_naive += (m - 1.96 * se_naive <= 0 <= m + 1.96 * se_naive)
    assert cover_naive / reps < 0.75


def test_cr1_input_validation():
    with pytest.raises(ValueError):
        cr1([])
    with pytest.raises(ValueError):
        cr1([1.0, 2.0], [1.0, 1.0], [0, 0])   # one cluster
    with pytest.raises(ValueError):
        cr1([1.0, 2.0], [1.0], [0, 1])


def test_westfall_young_controls_false_positives_under_null():
    """Many overlapping null cells: per-cell tests fire often, the family-wise test rarely."""
    rng = np.random.default_rng(11)
    G, per_day, K = 15, 150, 20
    cluster = np.repeat(np.arange(G), per_day)
    per_cell_hits, family_hits = 0, 0
    trials = 12
    for _ in range(trials):
        base = rng.normal(0, 1, size=G)[cluster] + rng.normal(0, 3, size=G * per_day)
        cells = []
        for _k in range(K):
            mask = rng.random(G * per_day) < 0.6
            cells.append(np.where(mask, base + rng.normal(0, 1, size=base.size), np.nan))
        res = westfall_young_maxt(cells, cluster, n_draws=300, seed=int(rng.integers(1e9)))
        per_cell_hits += res.significant_per_cell.sum()
        family_hits += res.significant_family.any()
        assert res.crit_family > res.crit_per_cell
    # family-wise error should be at most a few of the 12 trials
    assert family_hits <= 3
    # per-cell fires on a decent fraction of the 240 cell tests, more than the family-wise count
    assert per_cell_hits > family_hits


def test_westfall_young_keeps_a_real_effect():
    rng = np.random.default_rng(5)
    G, per_day, K = 20, 200, 10
    cluster = np.repeat(np.arange(G), per_day)
    noise = rng.normal(0, 0.3, size=G)[cluster] + rng.normal(0, 2, size=G * per_day)
    cells = [noise + rng.normal(0, 0.5, size=noise.size) for _ in range(K - 1)]
    cells.append(noise + 1.5)   # a strong true effect in the last cell
    res = westfall_young_maxt(cells, cluster, n_draws=400, seed=2)
    assert res.significant_family[-1]
    assert res.adjusted_p[-1] < 0.05
    # step-down adjusted p-values are monotone in observed |t|
    order = np.argsort(-res.t_obs)
    assert np.all(np.diff(res.adjusted_p[order]) >= -1e-12)


def test_westfall_young_rejects_bad_shapes():
    cluster = np.repeat(np.arange(4), 10)
    with pytest.raises(ValueError):
        westfall_young_maxt([np.zeros(5)], cluster, n_draws=10)
