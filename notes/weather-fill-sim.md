# Weather: five years of tape, one fill simulator, one expired ticker

The project started on Kalshi's daily high-temperature contracts for New York. They settle on the National Weather Service's Central Park daily climate report, which is the observed maximum of the station's 5-minute running mean, so the fast free observation feed reads the settlement value low on most days and the accurate rebuild is no faster than the market (a survey, NYC only), and the question became whether makers or takers are paid.

## The maker population is paid, and only recently

Kalshi serves every historical trade back to series inception, unauthenticated, with the taker side on each record. I harvested 11.7 million trade lines (about 559 million contracts) across seven cities from August 2021 to June 2026. Because the maker fee on these series is zero, aggregate maker P&L at settlement is an accounting identity: the taker's price if the taker lost, minus the payout otherwise.

In the 90 to 99 cent decile, where nearly half the volume sits (266M contracts), makers earned +0.63c per contract [+0.32, +0.95] over the five years, and +0.83c [+0.59, +1.07] in 2025 to 2026. Six of ten price deciles were independently positive. Every city was flat or negative before 2025 and positive after: a cross-city regime change that arrived with the volume, consistent with retail takers paying the one-cent tick floor. The pre-registered kill ("confined to 90 to 99c and gone in 2025 to 2026") did not fire.

That is the P&L of the whole maker population, including whoever sits first in the price-time queue. It says nothing about what a newcomer gets.

## The fill simulator: the provable fills lose

To answer that, I recorded a week of NYC order books every five minutes (2,016 slots, 54 markets) and simulated a one-lot maker posting at the touch on every snapshot. Five-minute snapshots see no queue position and no intra-interval trades, so the simulator is explicitly an upper bound. It posted 25,018 quotes and 19,912 were filled within 30 minutes by its loosest rule.

| fill set | n | capture at 30 min | 95% CI |
|---|---|---|---|
| all fills (upper bound) | 19,173 | +0.47c | [+0.42, +0.53] |
| strict: the book traded through the quote | 4,281 | -1.47c | [-1.60, -1.34] |
| strict plus level cleared | 7,057 | -0.77c | [-0.95, -0.60] |
| shrank only (front of queue and cancels) | 12,116 | +1.20c | [+1.13, +1.26] |

The pre-registered kill rule did not fire on the upper bound, and the result still closed the idea. The only fills that are provable, where the book traded through the quote, lose 1.47c each. The adverse move after those fills is 2.15c, about three times the 0.68c half-spread earned, and it does not revert from 5 minutes out to 60; marking the same fills at settlement gives -1.67c. The gradient is monotone: the more certain the fill, the worse the outcome. That is the adverse-selection signature, and the positive aggregate sits entirely in the cancel-contaminated tier where a new entrant at the back of the queue cannot be. For the trade the five year history actually pointed to, selling 1 to 10 cent long shots, the provable fills lost 0.62c [-0.88, -0.36] (n = 506). Snapshots cannot see queue position, so a real maker's result lies somewhere between -1.47c and +0.47c, and the order by order data needed to pin it down was never collected. Weather was closed as a maker strategy in August 2026; the reason of record also included a newcomer's ceiling of under $5,000 a year.

The fee model behind these numbers reproduces all 42 cells of Kalshi's published fee table ([code/fees.py](../code/fees.py)). Getting there found a floating-point bug that overcharged one cent at every price whose fee lands on a cent boundary, and confirmed that the table rounds per order, not per contract, which would matter by a factor of 14 on cheap long shots. Production rounds finer, to a hundredth of a cent, which the account's own fills confirm.

## The expired ticker

My first weather collector broke because I had hard-coded one day's event ticker, and it expired. The fix was structural rather than a new constant: the collector now rediscovers the current open dated event on every run. Whether it would notice Kalshi replacing the whole series ticker was never audited for the weather collector; a later Bitcoin recorder added that check. The failure also led to the rule that the collection, replay and semantic gates fail closed and are never loosened to get a pass. Two observed temperature families were flagged as semantically drifted and kept out of the research set on exactly that basis, with the failing dimension recorded in machine-readable form rather than summarized.
