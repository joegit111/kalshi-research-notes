# Pre-registrations

The private repo holds about 30 frozen pre-registration documents plus several tests whose cells were fixed in a code docstring before running. The rule is simple: write down the cell, the metric, the clustering and the verdict rule before running, timestamp and commit it (the frozen documents also record a SHA-256), and never re-tune after seeing the numbers. Of the three here, Q4b and Q4c were committed before their results; the early-market spec was timestamped in the file and committed together with its results. Three real examples are here, lightly sanitized (internal paths and bucket names removed, no numbers changed). Each starts with a two-line header saying what happened afterward.

| file | what it registered | outcome |
|---|---|---|
| [early-market-hold.md](early-market-hold.md) | Hold-to-settlement value of an early-market maker fill at the back of the queue, August estimate and September confirmation | DOES NOT HOLD: -0.71c August, -0.85c September, negative on 31 of 32 days |
| [q4b-follow-polymarket.md](q4b-follow-polymarket.md) | Sudden, clean, in-game Polymarket move as a signal to take Kalshi | Lost at receive time (-0.97c); the optimistic timing variant (+2.2c) turned out to be a timestamp artifact |
| [q4c-follow-polymarket-retimed.md](q4c-follow-polymarket-retimed.md) | The same idea re-timed from raw ticks, the way a live reader would see them | -0.62c at 100 ms; Kalshi had already half-moved on 59% of signals; closed |
