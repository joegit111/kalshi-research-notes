"""Regenerate every chart in charts/ from the small CSVs in data/.

    python charts/make_charts.py

Each chart's title says whether the numbers are MEASURED (computed from recorded
Kalshi data in the private research repo), SIMULATED (a replay on recorded
data under stated assumptions) or FORMULA (derived from the fee schedule).
Requires matplotlib, numpy and pillow (for the one animated GIF).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "charts"
sys.path.insert(0, str(ROOT / "code"))
from fees import production_fee_cents, taker_fee_cents  # noqa: E402

INK = "#1f2a37"
ACCENT = "#1b6ca8"
ACCENT2 = "#c8553d"
GRID = "#d9dee5"

plt.rcParams.update({
    "font.size": 10, "axes.edgecolor": INK, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK, "text.color": INK,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white", "axes.facecolor": "white",
})


def read(name):
    with open(DATA / name, newline="") as fh:
        return list(csv.DictReader(fh))


def num(v):
    return float(v) if v not in ("", None) else np.nan


def mlb_curve():
    rows = read("mlb_latency_curve.csv")
    L = np.array([num(r["latency_s"]) for r in rows])
    d = np.array([num(r["realised_dollars_per_game"]) for r in rows])
    lo = np.array([num(r["realised_lo"]) for r in rows])
    hi = np.array([num(r["realised_hi"]) for r in rows])
    edge = np.array([num(r["edge_cents_vs_2min"]) for r in rows])
    fig, ax1 = plt.subplots(figsize=(8, 4.2), dpi=150)
    ax1.fill_between(L, lo, hi, color=ACCENT, alpha=0.15, linewidth=0)
    ax1.plot(L, d, "o-", color=ACCENT, label="realised pool, $ per game (whole market)")
    ax1.axhline(0, color=INK, linewidth=0.6)
    ax1.set_xlabel("seconds after the pitch stamp when the taker acts")
    ax1.set_ylabel("$ per game, with 95% interval", color=ACCENT)
    ax1.set_xscale("symlog", linthresh=1)
    ax1.set_xticks([0, 0.5, 1, 2, 3, 5, 8, 12, 20, 30])
    ax1.set_xticklabels(["0", "0.5", "1", "2", "3", "5", "8", "12", "20", "30"])
    ax2 = ax1.twinx()
    ax2.plot(L, edge, "s--", color=ACCENT2, label="edge per contract, cents vs price 2 min later")
    ax2.set_ylabel("cents per contract", color=ACCENT2)
    ax2.spines["right"].set_visible(True)
    ax1.yaxis.grid(True, color=GRID)
    ax1.set_axisbelow(True)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper right", fontsize=8, frameon=False)
    ax1.set_title("MEASURED: what a faster baseball run signal was worth on Kalshi\n"
                  "2,375 scoring plays, 341 games, Sept 2026, whole market, net of fees",
                  fontsize=10, loc="left")
    ax1.annotate("free data arrived\nat ~12 s", xy=(12, -159), xytext=(14, 600),
                 fontsize=8, arrowprops=dict(arrowstyle="->", color=INK))
    fig.tight_layout()
    fig.savefig(OUT / "mlb_latency_curve.png")
    plt.close(fig)


def btc_latency():
    rows = read("btc_maker_loop_latency.csv")
    labels = [r["latency_model"] for r in rows]
    v = np.array([num(r["pnl_cents_per_round_trip"]) for r in rows])
    lo = np.array([num(r["lo"]) for r in rows])
    hi = np.array([num(r["hi"]) for r in rows])
    fig, ax = plt.subplots(figsize=(8, 3.6), dpi=150)
    colors = [ACCENT if x >= 0 else ACCENT2 for x in v]
    y = np.arange(len(v))
    ax.barh(y, v, color=colors, height=0.55)
    err_lo = np.where(np.isnan(lo), 0, v - lo)
    err_hi = np.where(np.isnan(hi), 0, hi - v)
    ax.errorbar(v, y, xerr=[err_lo, err_hi], fmt="none", ecolor=INK, capsize=3, linewidth=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels([l.replace("; ", ";\n") for l in labels], fontsize=8)
    ax.invert_yaxis()
    ax.axvline(0, color=INK, linewidth=0.6)
    ax.set_xlabel("cents per round trip, Aug 2026 (22 days of recorded books)")
    ax.xaxis.grid(True, color=GRID)
    ax.set_axisbelow(True)
    ax.set_title("SIMULATED on recorded order books:\nthe maker loop only works at zero latency",
                 fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(OUT / "btc_maker_loop_latency.png")
    plt.close(fig)


def fee_curve():
    prices = np.arange(1, 100)
    one = np.array([taker_fee_cents(int(p), 1) for p in prices])
    hundred = np.array([taker_fee_cents(int(p), 100) / 100 for p in prices])
    exact = 7 * prices * (100 - prices) / 10000
    fig, ax = plt.subplots(figsize=(8, 3.6), dpi=150)
    prod = np.array([float(production_fee_cents(int(p), 1)) for p in prices])
    ax.step(prices, one, where="mid", color=ACCENT2, label="1 contract, published table (whole cents)")
    ax.plot(prices, prod, color="#7a9a3a", linewidth=1.2, label="1 contract, production (1/100 cent)")
    ax.plot(prices, hundred, color=ACCENT, label="100 contracts, per contract")
    ax.plot(prices, exact, color=INK, linewidth=0.7, linestyle=":", label="0.07 x P x (1-P), unrounded")
    ax.set_xlabel("contract price, cents")
    ax.set_ylabel("taker fee, cents per contract")
    ax.legend(frameon=False, fontsize=8, title="the three smooth lines overlap", title_fontsize=8)
    ax.yaxis.grid(True, color=GRID)
    ax.set_axisbelow(True)
    ax.set_title("FORMULA: Kalshi taker fee per contract. The published table rounds per order to the cent;\n"
                 "production rounds to 1/100 cent, so size barely changes the per-contract fee",
                 fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(OUT / "fee_curve.png")
    plt.close(fig)


def soccer_delay():
    rows = read("soccer_trial_feed_delay.csv")
    rows = [r for r in rows if not r["league"].startswith("all") and num(r["goals_clean"]) >= 5]
    rows.sort(key=lambda r: num(r["median_s"]))
    names = [f'{r["league"]} (n = {int(num(r["goals_clean"]))})' for r in rows]
    med = np.array([num(r["median_s"]) for r in rows])
    p25 = np.array([num(r["first_report_minus_kalshi_burst_p25_s"]) for r in rows])
    p75 = np.array([num(r["p75_s"]) for r in rows])
    fig, ax = plt.subplots(figsize=(8, 4.4), dpi=150)
    y = np.arange(len(rows))
    ax.hlines(y, p25, p75, color=ACCENT, linewidth=3, alpha=0.4)
    ax.plot(med, y, "o", color=ACCENT)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=8)
    ax.invert_yaxis()
    ax.axvline(0, color=ACCENT2, linewidth=1)
    ax.text(0.1, len(rows) - 0.6, "Kalshi had already\nrepriced (0 s)", color=ACCENT2, fontsize=8)
    ax.set_xlabel("seconds from Kalshi's price burst to the feed's first report (median, p25 to p75)")
    ax.xaxis.grid(True, color=GRID)
    ax.set_axisbelow(True)
    fig.suptitle("MEASURED: one trial weekend of a paid soccer feed, 560 cleanly timed goals in 59 leagues\n"
                 "first on under 1% overall; leagues with the most goals and at least 5 clean ones shown",
                 fontsize=10, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(OUT / "soccer_trial_feed_delay.png")
    plt.close(fig)


def btc_taker_cent():
    rows = {r["component"]: num(r["cents_per_contract"]) for r in read("btc_where_taker_cent_goes.csv")}
    loss, mk, fee = rows["taker net loss"], rows["to makers (gross)"], rows["to Kalshi fees"]
    fig, ax = plt.subplots(figsize=(8, 2.9), dpi=150)
    ax.barh([0], [mk], color=ACCENT, height=0.5)
    ax.barh([0], [fee], left=[mk], color=ACCENT2, height=0.5)
    ax.text(mk / 2, 0, f"makers\n{mk:.2f}c", ha="center", va="center", color="white", fontsize=10, fontweight="bold")
    ax.text(mk + fee / 2, 0, f"Kalshi fees  {fee:.2f}c", ha="center", va="center", color="white",
            fontsize=11, fontweight="bold")
    ax.set_xlim(0, loss * 1.02)
    ax.set_yticks([])
    ax.set_xlabel(f"cents per contract (a taker's average net loss is {loss:.2f}c)")
    ax.spines["left"].set_visible(False)
    ax.set_title("MEASURED: where the average Bitcoin 15 minute taker's money goes\n"
                 "every public print from a minute after the open to the close, Sep 20 to 26 2026,\n"
                 "1.44 billion contracts, held to settlement",
                 fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(OUT / "btc_where_taker_cent_goes.png")
    plt.close(fig)


def btc_front_back():
    rows = read("btc_front_vs_back.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.8), dpi=150, gridspec_kw={"width_ratios": [1, 1.25]})
    x = np.arange(len(rows))
    w = 0.36
    front = [num(r["front_of_queue_c"]) for r in rows]
    back = [num(r["back_of_queue_c"]) for r in rows]
    labels = ["August", "September"]
    a1.bar(x - w / 2, front, w, color=ACCENT, label="front of the queue")
    a1.bar(x + w / 2, back, w, color=ACCENT2, label="back of the queue")
    for i in range(len(rows)):
        a1.text(x[i] - w / 2, front[i] + 0.04, f"{front[i]:+.2f}", ha="center", fontsize=9)
        a1.text(x[i] + w / 2, back[i] / 2, f"{back[i]:+.2f}", ha="center", va="center", fontsize=9,
                color="white", fontweight="bold")
    a1.axhline(0, color=INK, lw=0.8)
    a1.set_xticks(x, labels)
    a1.set_ylabel("cents per fill, held to settlement")
    a1.set_ylim(-1.0, 0.85)
    a1.legend(frameon=False, fontsize=9, loc="upper center", ncol=2)
    a1.set_title("Same one lot order, two places in line", fontsize=10, loc="left")
    share = [num(r["runover_share"]) for r in rows]
    ro = [num(r["runover_c_each"]) for r in rows]
    rest = [num(r["rest_c_each"]) for r in rows]
    for i, lab in enumerate(labels):
        a2.barh(i, 1 - share[i], color=GRID, height=0.5)
        a2.barh(i, share[i], left=1 - share[i], color=ACCENT2, height=0.5)
        a2.text((1 - share[i]) / 2, i, f"ordinary fills {1 - share[i]:.0%}\n{rest[i]:+.2f}c each",
                ha="center", va="center", fontsize=9)
        a2.text(1 - share[i] / 2, i, f"run over {share[i]:.0%}\n{ro[i]:+.2f}c each",
                ha="center", va="center", fontsize=9, color="white", fontweight="bold")
    a2.set_yticks(range(len(labels)), labels)
    a2.set_xlim(0, 1)
    a2.set_xticks([])
    a2.spines["bottom"].set_visible(False)
    a2.set_title("Back of the queue: the run over fills are the whole loss", fontsize=10, loc="left")
    fig.suptitle("SIMULATED on recorded books: Bitcoin 15 minute, one lot posted 900 to 600 s before close",
                 fontsize=10, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(OUT / "btc_front_vs_back.png")
    plt.close(fig)


def weather_tiers():
    rows = read("weather_fill_tiers.csv")
    fig, ax = plt.subplots(figsize=(8, 3.4), dpi=150)
    y = np.arange(len(rows))[::-1]
    v = np.array([num(r["capture_30min_c"]) for r in rows])
    lo = np.array([num(r["lo"]) for r in rows])
    hi = np.array([num(r["hi"]) for r in rows])
    colors = [ACCENT if a > 0 else ACCENT2 for a in v]
    ax.barh(y, v, color=colors, height=0.55, xerr=[v - lo, hi - v], ecolor=INK, capsize=3)
    ax.set_yticks(y, [f"{r['tier']}\nn = {int(num(r['n'])):,}" for r in rows], fontsize=9)
    ax.axvline(0, color=INK, lw=0.8)
    for yi, a, l, h in zip(y, v, lo, hi):
        ax.text(h + 0.06 if a > 0 else l - 0.06, yi, f"{a:+.2f}c", va="center",
                ha="left" if a > 0 else "right", fontsize=9)
    ax.set_xlim(-2.2, 1.9)
    ax.set_xlabel("cents per fill, 30 minutes later (95% interval)")
    fig.suptitle("SIMULATED on a week of recorded NYC temperature books\n"
                 "the more certain the fill, the worse it is: a newcomer gets the losing ones",
                 fontsize=10, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(OUT / "weather_fill_tiers.png")
    plt.close(fig)


def miami_race():
    rows = read("miami_reading_race.csv")
    fig, ax = plt.subplots(figsize=(8, 3.6), dpi=150)
    x = np.arange(len(rows))
    v = np.array([num(r["taker_edge_c"]) for r in rows])
    lo = np.array([num(r["lo"]) for r in rows])
    hi = np.array([num(r["hi"]) for r in rows])
    colors = [ACCENT2 if "2 to 0" in r["window"] or "0 to 2" in r["window"] else ACCENT for r in rows]
    ax.bar(x, v, color=colors, yerr=[v - lo, hi - v], ecolor=INK, capsize=3, width=0.6)
    ax.set_xticks(x, [r["window"].replace(" s ", " s\n") for r in rows], fontsize=8.5)
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_ylabel("taker edge, cents per contract")
    for xi, a in zip(x, v):
        ax.text(xi + 0.32, a, f"{a:+.1f}", fontsize=8.5, va="center")
    ax.set_title("MEASURED: Miami hourly temperature, 39 days of public trades\n"
                 "taker edge around the moment Kalshi receives a reading that moves the index",
                 fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(OUT / "miami_reading_race.png")
    plt.close(fig)


def nfl_snap():
    rows = read("nfl_size_at_snap.csv")
    fig, ax = plt.subplots(figsize=(7, 3.2), dpi=150)
    x = np.arange(len(rows))
    v = np.array([num(r["displayed_size_at_best"]) for r in rows])
    ax.bar(x, v, color=[ACCENT, "#5f93bf", ACCENT2], width=0.55)
    ax.set_yscale("log")
    ax.set_xticks(x, [r["moment"] for r in rows])
    labels = ["about 116,000", "about 10,000", "900 to 2,000"]
    for xi, a, lab in zip(x, v, labels):
        ax.text(xi, a * 1.25, lab, ha="center", fontsize=9)
    ax.set_ylim(300, 400000)
    ax.set_ylabel("contracts at the best price (log scale)")
    ax.set_title("MEASURED: NFL moneyline, typical displayed size at the best price\n"
                 "the makers leave before the play, not after it", fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(OUT / "nfl_size_at_snap.png")
    plt.close(fig)


def mlb_gif():
    from matplotlib.animation import FuncAnimation, PillowWriter
    rows = [r for r in read("mlb_latency_curve.csv") if num(r["latency_s"]) <= 8]
    lat = np.array([num(r["latency_s"]) for r in rows])
    usd = np.array([num(r["realised_dollars_per_game"]) for r in rows])
    grid = np.linspace(0, 8, 81)
    curve = np.interp(grid, lat, usd)
    fig, ax = plt.subplots(figsize=(7, 3.4), dpi=110)
    ax.set_xlim(0, 8)
    ax.set_ylim(-120, 1350)
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xlabel("seconds after MLB's pitch timestamp")
    ax.set_ylabel("$ per game, whole market")
    ax.set_title("MEASURED: what's left for a taker after a run scores (Kalshi MLB game markets)",
                 fontsize=9.5, loc="left")
    line, = ax.plot([], [], color=ACCENT, lw=2.5)
    dot, = ax.plot([], [], "o", color=ACCENT2, ms=9)
    label = ax.text(4.2, 1100, "", fontsize=16, fontweight="bold", color=INK)
    sub = ax.text(4.2, 960, "", fontsize=9.5, color=INK)
    ax.text(0.1, -95, "fastest free data arrives at about 12 s", fontsize=8.5, color="#6b7785")
    fig.tight_layout()
    n = len(grid)
    frames = list(range(n)) + [n - 1] * 25

    def draw(i):
        line.set_data(grid[: i + 1], curve[: i + 1])
        dot.set_data([grid[i]], [curve[i]])
        label.set_text(f"${max(curve[i], 0):,.0f} left")
        sub.set_text(f"acting {grid[i]:.1f} s after the pitch")
        return line, dot, label, sub

    FuncAnimation(fig, draw, frames=frames, blit=False).save(
        OUT / "mlb_money_left.gif", writer=PillowWriter(fps=14))
    plt.close(fig)


if __name__ == "__main__":
    mlb_curve()
    btc_latency()
    fee_curve()
    soccer_delay()
    btc_taker_cent()
    btc_front_back()
    weather_tiers()
    miami_race()
    nfl_snap()
    mlb_gif()
    for p in sorted([*OUT.glob("*.png"), *OUT.glob("*.gif")]):
        print(f"{p.name}: {p.stat().st_size / 1024:.0f} KB")
