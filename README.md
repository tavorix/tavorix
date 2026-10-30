# Tavorix

Open-source project building a plain-language token risk check for BNB Chain: two separate scores (scam risk and centralization risk), each with its reasons shown.

> **Status: early-stage.** A public demo runs in your browser at [tavorix.xyz/check](https://tavorix.xyz/check). The scanner is not validated: see the initial evaluation sample below. Nothing here is investment, legal, or tax advice. No token has been issued and no token sale is open.

Founder: Dadang Setiawan ([github.com/ddng-dev](https://github.com/ddng-dev))

Demo video: https://www.youtube.com/watch?v=Vl_YmNP8aLM

## Repository layout

| Path | Purpose |
|---|---|
| `scanner/` | Risk Scanner: rule-based checks (18 checks, two scores, JSON report) with 39 automated tests using BNB Chain RPC, DexScreener and GoPlus data |
| `scanner/my_dataset.csv` | Initial labeled sample (23 verified tokens), see `scanner/EVALUATION.md` |
| `docs/` | Architecture notes and dataset methodology |

## Initial evaluation (not an accuracy claim)

A first sample of 23 labeled tokens was scored on 30 October 2026, and the results include every failure, among them all 4 old rugpull examples being missed. Read the limitations before quoting anything: [`scanner/EVALUATION.md`](scanner/EVALUATION.md).

## Roadmap (proposed, depends on team capacity)

## Roadmap (proposed, no fixed dates)

1. **Now:** Public hosted demo (live), documentation, labeled dataset grown from 23 to 35 verified entries.
2. **Next:** Improve detection of old rugpulls (the initial evaluation missed all 4), then publish a small-sample accuracy report including failures.
3. **Later (no date):** Simulation-based honeypot detection, an open API, and a pilot with traders.
Anything beyond this (ML models, other chains, a token) comes only after validation, independent audits and legal review.

## Contact

- Partnerships: partnerships@tavorix.xyz
- Security reports: security@tavorix.xyz (see `SECURITY.md`)
