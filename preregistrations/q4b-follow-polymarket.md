# Q4b: follow Polymarket into Kalshi (sudden, clean, in-game)

What happened afterward: at our receive time the primary cell lost -0.97c [-1.79, -0.15], which by the rule below disproved the idea as attainable. The optimistic "secfloor" variant made +2.2c [+1.4, +3.0], which led to Q4c, where it was shown to be a timestamp artifact.

This is the docstring of the analysis script, written 2026-10-07 before running. Reproduced with internal paths removed.

```
Q4b: last narrow test of "follow Polymarket into Kalshi". EXPLORATORY, not a gate.
Written 2026-10-07 BEFORE running; the cells below are fixed here and not changed
after seeing results.

Why: Q4 found every "Polymarket moved X pp -> take Kalshi" cell negative, but its
in-game X5 cell held to settlement was INCONCLUSIVE (-0.78c [-1.62, +0.05]). The one
untested refinement is "sudden, clean, in-game": a big move between consecutive
Polymarket seconds on a tight Polymarket book, while Kalshi has not yet caught up.
This is a no-hindsight test: it starts from the Polymarket move, not from a Kalshi move.

Signal (per Polymarket moneyline token mapped to a Kalshi game market):
  * consecutive per-second rows of the same token, gap <= 2 s ("sudden"),
    |dp| >= X pp, X in {5, 8}
  * Polymarket spread <= 2c on both rows; row fresh (recv - venue <= 2 s, as Q4)
  * in-game (receipt after game start, same start source as Q4)
  * Kalshi has moved < |dp|/2 the same way since the previous Polymarket row
    (else there is nothing to catch)
Entry: take the Kalshi touch at our receipt (Y = 0): buy YES at the ask if dp > 0,
  else NO at 100 - bid.
  Timing variants: "recv" = our receive time (attainable); "secfloor" = start of the
  Polymarket venue second (optimistic, NOT attainable: an upper bound on what speed
  could buy).
Outcomes (cents per contract, net of taker fee): markout to Kalshi mid at +10 s,
  +30 s, +60 s; settlement.
PRIMARY: X = 5, recv timing, +30 s net. Game-clustered 95% CI (cr1, as Q4).
Reading: primary CI upper bound < 0 -> the idea is disproved on this data. If the
  optimistic secfloor variant is also < 0, faster Polymarket data would not rescue
  it either.
```
