# Tavorix Token Check: initial evaluation sample

**Status: initial sample, NOT an accuracy claim.** 23 labeled tokens, one labeler, results below include every failure. Run on 30 October 2026.

## What was measured

- Data: `my_dataset.csv` (23 verified rows: 4 `rugpull`, 19 `healthy`). Rows without a verifier (trial or uncertain rows) were excluded.
- Method: `collect.py` re-scanned every address live (BNB Chain RPC, DexScreener, GoPlus), then `evaluate.py features.csv --threshold 40 --details`.
- A token counts as "flagged" when its **scam-risk score is 40 or higher**. Scam is the positive class. The threshold is the default and was **not tuned**; because nothing was tuned, all 23 rows act as test data (no separate held-out split was made).
- The scanner was not changed before or during this run.

## Result

| Metric | Value |
|---|---|
| True positives | 0 |
| False negatives | 4 |
| False positives | 6 |
| True negatives | 13 |
| Precision | 0.000 |
| Recall | 0.000 |
| False-positive rate | 0.316 |

**Missed (all 4 rugpulls):** SQUID V1 (scam score 0), Santa Coin (15), Lucky Star Currency (0), Flare (25).
**Flagged healthy tokens (6 of 19):** 1INCH (55), ANKR (55), FRONT (40), HOOK (40), EDU (60), KNC (90).
Healthy tokens in the medium range but below 40: XVS (35), TWT (35).

## Per-token scores

| Label | Token | Scam risk | Centralization | Flagged at 40 |
|---|---|---|---|---|
| rugpull | SQUID V1 | 0 | 15 | no |
| rugpull | Santa Coin | 15 | 0 | no |
| rugpull | Lucky Star Currency | 0 | 45 | no |
| rugpull | Flare | 25 | 45 | no |
| healthy | CAKE | 5 | 30 | no |
| healthy | XVS | 35 | 5 | no |
| healthy | TWT | 35 | 20 | no |
| healthy | SFP | 5 | 0 | no |
| healthy | FLOKI | 0 | 0 | no |
| healthy | 1INCH | 55 | 30 | **yes** |
| healthy | DODO | 25 | 25 | no |
| healthy | C98 | 5 | 40 | no |
| healthy | USDT (Binance-Peg) | 5 | 45 | no |
| healthy | ANKR | 55 | 30 | **yes** |
| healthy | KAVA (BNB Chain) | 20 | 5 | no |
| healthy | FRONT | 40 | 30 | **yes** |
| healthy | LIT | 5 | 0 | no |
| healthy | HOOK | 40 | 30 | **yes** |
| healthy | EDU | 60 | 20 | **yes** |
| healthy | BAKE | 25 | 30 | no |
| healthy | ASTER | 5 | 0 | no |
| healthy | BMT | 5 | 5 | no |
| healthy | KNC (Binance-Peg) | 90 | 15 | **yes** |

Signals that most often pushed healthy tokens up: one wallet holding a large share (`top_holder`), unlocked liquidity, `deployer_history`, thin main pool (`low_liquidity`), and mint rights. The scanner cannot tell a treasury, bridge or vesting wallet from an ordinary large holder.

## Limitations (please read before quoting any number)

1. **Post-incident test.** All 4 rugpulls are old incidents (2021 to 2023) scanned in October 2026. The scan shows today's state, not the state before the exit. This does not test detection of scams that are still active, and **honeypot detection was not tested at all**.
2. **Very small sample.** Only 4 scam rows, so recall and precision are extremely unstable. Do not read 0.000 as a general measure of the scanner.
3. **One labeler.** Labels were assigned by the project owner using BscScan, CoinGecko and CertiK reports. There was no independent review.
4. **Weaker evidence than our own rules ask for.** `LABELING.md` asks for two evidence sources per row. The USDT row has only one link, and several CoinGecko links were built from the coin name and not opened. Some CoinGecko contract addresses were matched only by start and end.
5. **Atypical tokens.** USDT (also the official-USDT example on our site), KAVA, KNC and BMT are bridged, pegged or cross-chain tokens. EDU and KNC have very thin main pools (about 522 USD and 1,568 USD), which may not reflect where the tokens really trade.
6. **Live data drifts.** Two rows changed between earlier scans and this run (KAVA 5 to 20, FRONT 25 to 40). The numbers above are from this run.
7. **No statistical claim.** There is no confidence interval, and no comparison against other scanners.

## What happens next

- Add still-active scam and honeypot examples (with two independent evidence sources each) to test the scanner's main use case.
- Improve the weak spots (treasury versus ordinary holder, thin-pool weighting) and re-test only on **new** rows that were not used to make the changes.
- Publish every update here, including failures.

*Not investment, legal or tax advice.*
