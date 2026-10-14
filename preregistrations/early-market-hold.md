# Early-market maker hold: pre-specification

What happened afterward: the primary cell came out -0.712c [-0.827, -0.598] in August and -0.851c [-1.139, -0.562] in September, bootstrap intervals agreeing, negative on 31 of 32 settlement days. Verdict against the rule in section 3: DOES NOT HOLD. The early-market effect in the historical prints is real and reproduces, but it belongs entirely to the front of the queue (+0.40c there in both months), which a one-lot joiner cannot reach.

Written 2026-09-17T17:24:35Z, repo HEAD recorded. Reproduced with internal paths and field names removed and the em-dashes replaced; no numbers or rules changed. This spec was timestamped inside the file and committed together with its results, not before them.

EXPLORATORY RESEARCH ONLY. Not a gate, not a verdict, not research, backtest or trading eligibility of any kind. No orders, no authenticated Kalshi calls, no AWS, no commits.

This file is written before any number in this workstream has been computed. The workstream's data and analysis directories contain nothing but this file at the moment of writing. In particular no September number, no re-weighted 178-day number and no August hold-to-settlement-by-time-to-close number has been computed by me.

## 1. The question

For a slow, one-contract, passive (maker) order that joins an existing touch at the back of the queue, with 35 to 100 ms latency and no informed cancel, is the hold-to-settlement value of a fill positive when the order is posted early in the 15-minute contract's life, and does that survive out of sample?

Both sides must be pooled. August 2026 contained a roughly +25% BTC rally, so any one-sided (YES-only or NO-only) number in that window carries the rally.

## 2. Honest statement of where the hypothesis came from

This is not a blind test. The order in which evidence was seen matters and is recorded here.

| evidence | period | already seen before this workstream? |
|---|---|---|
| 178-day prints strata: makers earn most early, lose late | 2025-12-10 to 2026-06-05 | YES. This is the hypothesis source. The exact stratum (time to close 900 to 600 s, +0.636c final / +1.355c cleared) was read before this file was written. |
| Time-to-settlement and early-only studies in the August exploratory pass: the maker round trip falls monotonically with life-fraction; first fifth +0.188c, last fifth +0.042c | August 2026 | YES. August has been looked at, on a different metric (maker-in, maker-out round trip, not hold-to-settlement) and in a different simulator. The early-only study also records that under a realistic latency model the best early-only cutoff is -0.039c [-0.069, -0.009], still negative. |
| Replay table T8, both sides, RU model: -0.69c per fill [-0.87, -0.55] held to settlement over all time-to-close >= 300 s | August 2026 | YES, but pooled over time-to-close, not split. |
| Shadow-order August hold-to-settlement split by time-to-close | August 2026 | NO, new. August is therefore a partly fresh test: the metric and the simulator are new, the window is not. |
| Shadow-order September hold-to-settlement split by time-to-close | 2026-09-06 to 2026-09-17 | NO, new, and the window is new. This is the clean confirmation set. |

Consequence, fixed in advance: August is the estimation sample, September is the confirmation sample. If August is positive and September is not, the finding does not hold. If both are positive, the September CI is the one quoted, with a power statement, because G is about 10 to 11 clusters there.

Known trap on this dataset, recorded in advance: a known-dead sister series (KXBTCD) previously manufactured out-of-sample-positive bands under the same search machinery. "Positive in a second sample" is necessary, not sufficient. The verdict section of the handoff must also say what else supports or undermines the effect (mechanism, symmetry across sides, stability by month, sensitivity to the fill-model mix).

## 3. The PRIMARY cell (one cell, declared now)

| element | value |
|---|---|
| data | shadow-order replay outputs: August and September market files |
| trigger | T1 CLOCK |
| sides | YES and NO pooled, equal weight per fill (one fill = one observation, whatever side it is on) |
| queue model | R0 back-of-queue, which in these files is the union of R0 and the trade-through R1 |
| latency | L = 35 ms |
| cancel policy | never cancel |
| entry time-to-close | ttc_s in [600, 900): the order's trigger instant is 900 to 600 s before the market close |
| metric | hold-to-settlement P&L per fill, in cents. Maker fee $0, no exit, no spread crossed. |
| exclusions | markets with no settlement result; one September market already excluded upstream; August 08-08 and 08-09 have no book |
| cluster | settlement (close) UTC date, CR1 day-clustered 95% CI, t critical with df = G - 1 |
| second CI | pairs-cluster bootstrap, 10,000 resamples of days with replacement, percentile interval |

Primary verdict rule, fixed now:

HOLDS: the September pooled mean is positive AND its day-clustered 95% CI excludes zero AND its pairs-bootstrap 95% CI excludes zero.
DOES NOT HOLD: the September 95% CI excludes zero on the negative side.
CANNOT TELL: anything else. Every CANNOT TELL is reported with the minimum effect September could have detected at 80% power.

## 4. SECONDARY cells (declared now; all are secondary, none can rescue a failed primary)

S1. Same cell with ttc_s in [300, 600) and ttc_s in [60, 300). If a guard or the trigger construction excluded orders in a bucket, say so and report the count rather than silently dropping it.
S2. Queue models R1, RB and C0 for the primary ttc bucket. C0 is an unattainable ceiling and is labelled as such everywhere.
S3. Trigger T3 SHADOW for the primary ttc bucket, with the systematic sub-sample weight applied.
S4. Latency L = 100 ms and L = 0 for the primary cell.
S5. Cancel policies: the 20 s timer (a fill counts only if it came within 20 s + L of posting) and cancel-on-touch-move (a fill counts only if it came before the touch first moved, + L), primary cell.
S6. Mid markouts at +5 s, +30 s and +300 s for the same cells, to see whether adverse selection itself is lower early. Benchmark: mid = midpoint of the best YES bid and 100 minus the best NO bid, from the touch series at or before the mark instant, on our clock. A mark at or after close is the settlement value.
S7. YES-only and NO-only beside every pooled number.

## 5. What else will be computed (descriptive, not verdict-bearing)

D1. Population real fills (August and September): hold-to-settlement by ttc bucket x crowding x back-of-queue state, at-touch only.
D2. 178-day prints: maker hold-to-settlement by ttc x class x event size x maker side x month, contract- and print-weighted; matched cleared-vs-final inside ttc buckets; back-of-queue re-weighting with the August-calibrated fill-model mixes renormalised within each ttc bucket, with a day bootstrap.
D3. Mechanism per ttc bucket: mid-price volatility per second, spread in ticks, queue-ahead at entry, aggressor-size mix, mid markout path.
D4. Economics at one lot: fills per day in the early window, capital locked, per-market and per-day P&L for a both-sides sequential one-lot, worst day, drawdown, days needed for 80% power, what breaks at size.

## 6. Multiplicity discipline

The handoff must state exactly how many cells were looked at, counting every (trigger x side x latency x queue model x cancel policy x ttc bucket x metric) combination that was printed, not only the ones quoted. The primary cell is one cell and is not re-defined after the September numbers are seen.

## 7. Things that will NOT be done

No re-tuning of the ttc bucket edges after seeing a result. The edges 900/600/300/60 s are copied from the 178-day strata that generated the hypothesis. No dropping of days, markets or sides after seeing them, except the pre-declared exclusions in section 3. No claim of eligibility of any kind.
