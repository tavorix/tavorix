# Tavorix Token Check: evaluation (initial samples, NOT an accuracy claim)

Two small evaluation rounds are recorded here, newest first. Neither one is a validated accuracy measurement. Both are published with every failure so anyone can check them.

## Round 2 (31 October 2026): 34 labeled tokens

**Data.** `my_dataset.csv`: 34 rows labeled `rugpull` (10) or `healthy` (24). The 4 rows labeled `uncertain` were not scored. Each row follows the two-source rule in `LABELING.md`; several rows have weaker evidence, see Limitations.

**Method.** Every token was re-scanned live with `collect.py`, then scored with `python evaluate.py features.csv --threshold 40`. A token counts as flagged when its scam-risk score is 40 or higher. The threshold was fixed in advance and was not tuned on this data. `evaluate.py` scores every row it is given, so there is no held-out test split in this round: the numbers describe the whole sample.

**Results (scam = positive class).**

| Metric | Value | 95% interval (Wilson) |
|---|---|---|
| Precision | 0.333 (3 of 9 flagged) | 0.12 to 0.65 |
| Recall | 0.300 (3 of 10 rugpulls) | 0.11 to 0.60 |
| False-positive rate | 0.250 (6 of 24 healthy) | 0.12 to 0.45 |

True positives 3, false negatives 7, false positives 6, true negatives 18. With so few rows the intervals are very wide.

**Caught (3 of 10 rugpulls):** DecentraWorld (DEWO, 95), Day of Defeat (DOD, 65), FinSoul original token (FSL, 40, exactly at the threshold).

**Missed (7 of 10 rugpulls):** Squid Game V1 (0), Santa Coin (15), Lucky Star Currency (0), Flare (25), Smash Cash (0), TIGER (0), SuperHeavy (35).

**False alarms (6 of 24 healthy tokens):** 1INCH (55), ANKR (55), FRONT (40), HOOK (40), EDU (60), KNC (90).

### Per-token scores

| Token | Label | Scam score | Result |
|---|---|---|---|
| World Liberty Financial (WLFI) | healthy | 20 | true negative |
| Squid Game V1 | rugpull | 0 | missed |
| Santa Coin | rugpull | 15 | missed |
| Lucky Star Currency (LSC) | rugpull | 0 | missed |
| PancakeSwap (CAKE) | healthy | 5 | true negative |
| Venus (XVS) | healthy | 35 | true negative |
| Trust Wallet Token (TWT) | healthy | 35 | true negative |
| SafePal (SFP) | healthy | 5 | true negative |
| FLOKI | healthy | 0 | true negative |
| 1inch (1INCH) | healthy | 55 | false alarm |
| DODO | healthy | 25 | true negative |
| Coin98 (C98) | healthy | 5 | true negative |
| Flare | rugpull | 25 | missed |
| Binance-Peg BSC-USD (USDT) | healthy | 5 | true negative |
| Ankr (ANKR) | healthy | 55 | false alarm |
| Kava (KAVA, BNB Chain version) | healthy | 20 | true negative |
| Frontier (FRONT) | healthy | 40 | false alarm |
| Litentry (LIT) | healthy | 5 | true negative |
| Hooked Protocol (HOOK) | healthy | 40 | false alarm |
| EDU Coin (EDU) | healthy | 60 | false alarm |
| BakerySwap (BAKE) | healthy | 25 | true negative |
| Aster (ASTER) | healthy | 5 | true negative |
| Bubblemaps (BMT) | healthy | 5 | true negative |
| Kyber Network Crystal (KNC, Binance-Peg) | healthy | 90 | false alarm |
| DecentraWorld (DEWO) | rugpull | 95 | caught |
| Day of Defeat (DOD) | rugpull | 65 | caught |
| Giggle Fund (GIGGLE) | healthy | 30 | true negative |
| ChainGPT (CGPT) | healthy | 5 | true negative |
| Smash Cash (SMASH) | rugpull | 0 | missed |
| TIGER | rugpull | 0 | missed |
| Biswap (BSW) | healthy | 5 | true negative |
| SuperHeavy (Web3Memes) | rugpull | 35 | missed |
| Mobox (MBOX) | healthy | 5 | true negative |
| FinSoul (FSL) original token | rugpull | 40 | caught |

### What this shows

- The scanner misses most of these rugpulls. The four rugpulls from round 1 (Squid Game V1, Santa Coin, Lucky Star Currency, Flare) are all still missed.
- The three caught rugpulls score high because of traits still visible today (a high sell tax on DEWO and DOD, an unverified contract on FSL). Most missed rugpulls show few or no triggered checks. A likely explanation, not yet tested, is that the scanner reads each token's current state, not its state before the incident.
- The six false alarms are the same six healthy tokens flagged in round 1. They are driven by large single-wallet holdings, unlocked liquidity, deployer history and thin pools on BNB Chain. The scanner cannot tell a treasury, bridge or vesting wallet from an ordinary large holder.
- None of this is an accuracy claim.

## Round 1 (30 October 2026): 23 labeled tokens

4 rugpulls and 19 healthy tokens, threshold 40, not tuned. Result: 0 true positives, 4 false negatives, 6 false positives, 13 true negatives (precision 0.000, recall 0.000, false-positive rate 0.316). Missed rugpulls: Squid Game V1, Santa Coin, Lucky Star Currency, Flare. Flagged healthy tokens: 1INCH, ANKR, FRONT, HOOK, EDU, KNC. The original round 1 text is kept in the repository history.

## Limitations

1. All rugpulls are old incidents scanned in their current state. The test does not show whether the scanner catches an active scam. Honeypot detection was not tested.
2. The sample is very small (10 rugpulls, 24 healthy tokens), so the metrics are unstable and the intervals are wide. `LABELING.md` targets 100 to 200 rows.
3. One labeler, no independent review.
4. Label strength varies. CertiK calls Smash Cash a "potential" rug pull, Fairyproof calls SuperHeavy "highly suspected", and the Day of Defeat team disputes the rug-pull classification. For most rugpull rows we matched deployer addresses and report details but did not inspect the theft or liquidity-removal transactions ourselves.
5. Several healthy tokens are bridged, pegged or cross-chain (for example USDT, KNC, FLOKI, BMT), and some have very thin pools on BNB Chain.
6. Live data changes between scans. For example, FRONT scored 25 in a manual scan on 29 October and 40 in this run. Some dataset notes record the earlier manual scans.
7. No held-out test split was used in this round, and there is no comparison with other scanners.
8. Rows with only one evidence source were not scored (Zcash Binance-Peg was moved to `uncertain`).

## Next steps

1. Freeze a held-out test list before any tuning, so changes are never measured on the data they were tuned on.
2. Improve detection of old rugpulls (the main gap shown above), then re-measure on new rows only.
3. Add active scam and honeypot examples with two evidence sources each.
4. Investigate a supply-percentage bug: one scan printed a holder share above 100%.

This is not investment, legal or tax advice. Scores are estimates from public data and can be wrong.
