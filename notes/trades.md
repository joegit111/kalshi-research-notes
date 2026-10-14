# Every real trade

All of these were small by design and every test lost money. They are here because the posting asks for trades made, and because each one taught something a replay could not.

## One Bitcoin contract, bought and sold at 55 cents

2026-09-17, KXBTC15M. The purpose was to prove the order code could get flat on the real exchange before any strategy ran on it. A frozen pre-registration (18 criteria) was committed first, and the enabled build differed from the tested build by one flag.

The entry bought 1 YES at $0.55 and filled on a private fill message 228 ms after the acknowledgement. The flatten was an immediate-or-cancel sell with a $0.52 limit; it filled at $0.55 1.3 s later after seven assessment rounds, and the account was verified flat 2.39 s after the entry. The only cost was the 1.74c taker fee. The strict gate verdict was FAIL, 15 of 18, and the failures were registration defects, not run defects: one criterion counted the flatten's own fill messages as foreign, and two others could not be measured because the very first entry filled. That is recorded beside the verdict rather than reinterpreted, and a corrected second run, below, followed the same morning.

Along the way I measured that maker fills on this account carry a fee of exactly zero and taker fills 1.50c and 1.74c, by reading the fills endpoint rather than the fee schedule.

## A second contract, launched by mistake, -2.5c

2026-09-17, about 1.7 hours later, KXBTC15M. The corrected version of the same test had its own frozen pre-registration and was meant to start later under a supervised launch path. Instead it was started by mistake during a host check that was expected to refuse, and its rules allowed it to run. It bought 1 YES at $0.32 as a maker (fee zero), the book moved to 0.30/0.31 within a second, and the immediate-or-cancel exit sold at $0.31 with a 1.50c taker fee: -2.5c in all. The gate passed 18 of 18. Because any unplanned event stops the chain, the planned overnight sequence stopped there.

## Three capped phases at the open, -$2.07

2026-09-18 to 19, KXBTC15M openings, one $10 cap across all phases, never reset. Before any order that could fill, two probe runs sent 48 pre-signed orders at opens (21 accepted, 0 fills, $0) to establish that queue position 0 was reachable.

Phase A ran 10 openings unattended on 2026-09-18, with fills in 9, and lost $0.44.

Phase B quoted the touch on both sides at the open and left the orders alone for 26 s. Across 14 openings, 8 paired for exactly +1c each and 6 were one-sided; every one-sided market lost. Two exit decisions, one hold to settlement (-$0.50) and one cross (-$0.21), were 83% of the losses. The diagnostic burst at 1c and 99c cost exactly $0.00.

Phase C1 added managed inventory: detect a one-sided fill, cancel the stale opposite leg, re-quote it, and cross on a registered 10c stop. Across 50 openings (49 with fills), 20 paired and 29 were one-sided, and all 29 one-sided markets lost. The mean one-sided loss fell to 3.6c from Phase B's 14.4c, and the loss per opening to 1.7c from 5.7c, a 3.3x improvement that was still a loss. Three emergency crosses fired, all on the 10c stop. The pairing rate fell from 57% to 41% because the re-quote is a cancel-and-replace and destroys the resting exit's queue position. Zero contracts were held to settlement.

Cumulative across phases: -$2.07, reconciling to the cent against the account at three checkpoints. A ledger bug found at the Phase B freeze (exit orders were not mapped, so one-sided markets were credited a settlement they never held) is why there is now a reconciliation gate that prints "do not publish these totals" when the buckets disagree with the account.

## The Miami liquidity incentive, -$17.69

2026-10-09, Miami daily high temperature. Kalshi pays a liquidity incentive on some markets for resting size near the best price on both sides. The plan was to quote the cheap side at 1c post-only and collect the reward while risking $20.

Blocks of 1,000 contracts were hit within 1 to 40 seconds of posting. All 2,000 contracts that filled lost. The reward credited was $2.31, against a net loss of $17.69. The bot also had a bug (a cancel-and-replace churn every 15 s or so) that was found afterward.

The fine print, learned the hard way: the 1,000-contract target counts everyone's size on a side, not yours; both sides must be present every second; your pay is your share of the size; and a per-program reward under $1 is not paid at all. Every simulation I had run before the test missed that last rule. A separate 72-hour replay of the recorded books had already said that quoting both sides with 1 or 100 contracts loses in every market set, and that the one tactic that worked on paper had never been seen paid. The live test confirmed the simulations overstated the net. The follow-up was a shadow recorder and a plan to disprove the remaining tactic out of sample before any further money went in.
