# Q4c: follow Polymarket into Kalshi, re-timed from the raw tick archive

What happened afterward: the primary cell (X = 5, L = 100 ms, +30 s net) came out -0.62c [-1.30, +0.07] on 607 entries (508 with a +30 s mark) in 178 games; at ideal instant entry (L = 0) it was -0.17c [-0.88, +0.55]. Of 1,879 signals, 1,107 were dropped because Kalshi had already moved at least half the distance. By the rule below the primary is INCONCLUSIVE (upper bound +0.07c) with a negative point estimate. No cell had an interval above zero except NFL at settlement (15 games, noise), so the idea was closed for September data.

This is the docstring of the analysis script, written 2026-10-07 before running. Reproduced with internal paths and storage locations removed.

```
Q4c: "follow Polymarket into Kalshi", re-timed from the RAW Polymarket tick archive.
EXPLORATORY, not a gate. Cells fixed here, 2026-10-07, BEFORE running; not changed
after seeing results.

Why: Q4b lost at our receive time (-0.97c [-1.79, -0.15]) but made +2.2c [+1.4, +3.0]
when each move was timed at the START of its Polymarket second. Q4b used the
per-second reduction, which keeps only the LAST update of each venue second and
stamps it with that update's receive time, so up to 1 s of timing is thrown away.
This re-times every signal from the raw messages: the receive time of the FIRST
message at which the move is visible, which is what a live reader of the same feed
would have seen.

Data: the raw Polymarket market-channel archive for MLB, NFL and soccer (read-only,
streamed, not mirrored), Sep 2-18 2026 (the window the Kalshi book covers).
Receive clock = the off-host recorder (median ~44 ms after the Polymarket venue
stamp). Rows with recv - venue > 2 s dropped (stale replays). Tokens = the moneyline
tokens mapped to a Kalshi game market (same mapping as Q4/Q4b).

Signal, per token, on the tick stream of best bid/ask:
  * in-game: receipt in [game start, game start + 5 h]; Polymarket mid in [3, 97]
  * |mid(t) - mid(t - 2 s)| >= X pp, X in {5, 8}; Polymarket spread <= 2c at t and
    at t - 2 s
  * cooldown: no earlier signal on the same token in the previous 10 s
    (one entry per burst)
  * Kalshi has moved < |dp|/2 the same way between t - 2 s and t
    (else there is nothing to catch)
Entry: Kalshi touch at t + L: buy YES at ask if dp > 0, else NO at 100 - bid.
  L in {0, 100, 250} ms (100 ms = a plausible order arrival from the recorder's
  region; 0 = ideal; 250 = slow).
Outcomes (cents/contract, net of taker fee, 1-lot rounding): markout to Kalshi mid
  at +10, +30, +60 s; settlement.
PRIMARY: X = 5, L = 100 ms, +30 s net. Game-clustered 95% CI (cr1). Also touch size
  and $/game at the touch.
Reading: primary CI lower bound > 0 -> worth a live shadow test; upper bound < 0 ->
  dead on this data; else inconclusive.
```
