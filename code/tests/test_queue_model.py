import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from queue_model import QueueParams, simulate  # noqa: E402


def test_front_of_queue_beats_back():
    fr0, pnl0, b0 = simulate(0, n_markets=8000, seed=1)
    fr_back, pnl_back, b_back = simulate(800, n_markets=8000, seed=1)
    assert pnl0 > pnl_back
    assert b0 > b_back            # front fills are mostly benign
    assert fr0 >= fr_back


def test_back_of_queue_fills_are_mostly_sweeps():
    _, pnl, benign = simulate(1000, n_markets=8000, seed=2)
    assert benign < 0.5
    assert pnl < 0


def test_no_informed_flow_means_no_adverse_selection():
    p = QueueParams(p_info=0.0)
    fr, pnl, benign = simulate(30, p, n_markets=4000, seed=3)
    assert fr > 0.9
    assert benign == 1.0
    assert abs(pnl - p.half_spread_cents) < 1e-9
