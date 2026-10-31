# Tavorix

Open-source project building a plain-language token risk check for BNB Chain: two separate scores (scam risk and centralization risk), each with its reasons shown.

**Status: early-stage.** A public demo runs in your browser at [tavorix.xyz/check](https://tavorix.xyz/check). The scanner is not validated: see the evaluation below, which includes every failure. Nothing here is investment, legal, or tax advice. No token has been issued and no token sale is open.

Founder: Dadang Setiawan ([github.com/ddng-dev](https://github.com/ddng-dev))

Demo video: https://www.youtube.com/watch?v=Vl_YmNP8aLM

## Repository layout

| Path | Purpose |
|---|---|
| `scanner/` | Risk Scanner: rule-based checks (18 checks, two scores, JSON report) with 42 automated tests using BNB Chain RPC, DexScreener and GoPlus data |
| `scanner/my_dataset.csv` | Labeled sample (34 scored tokens plus 4 uncertain rows), see `scanner/EVALUATION.md` |
| `docs/` | Architecture notes and dataset methodology |

## Evaluation (not an accuracy claim)

Round 2 (31 October 2026) scored 34 labeled tokens (10 rugpulls, 24 healthy) at a fixed threshold of 40. The scanner caught 3 of the 10 rugpulls and falsely flagged 6 of the 24 healthy tokens. The sample is very small, so the intervals are wide, and all rugpulls are old incidents scanned in their current state. Round 1 (30 October 2026, 23 tokens) caught none of its 4 rugpulls. Every failure is published. Read the limitations before quoting anything: [scanner/EVALUATION.md](scanner/EVALUATION.md).

## Roadmap (proposed, no fixed dates)

1. **Now:** Public hosted demo (live), documentation, a frozen held-out test list, and more active scam and honeypot examples in the labeled dataset.
2. **Next:** Improve detection of old rugpulls (the evaluation missed 7 of 10) and fix a supply-percentage reading bug, then re-measure on new rows only and publish the results including failures.
3. **Later (no date):** Simulation-based honeypot detection, an open API, and a pilot with traders.

Anything beyond this (ML models, other chains, a token) comes only after validation, independent audits and legal review.

## Contact

- Partnerships: partnerships@tavorix.xyz
- Security reports: security@tavorix.xyz (see `SECURITY.md`)
