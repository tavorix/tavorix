# Tavorix

Open-source project building a plain-language token risk check for BNB Chain: two separate scores (scam risk and centralization risk), each with its reasons shown.

> **Status: early-stage.** A working scanner demo runs locally and is not yet publicly hosted. Smart contract drafts are unaudited and not deployed. Nothing here is investment, legal, or tax advice. No token sale is open, and none is part of Tavorix's funding request.

Founder: dadang setiawan

Demo video: https://www.youtube.com/watch?v=whrqD_Ba2i8

## Repository layout

| Path | Purpose |
|---|---|
| `contracts/` | Unaudited draft contracts for a token concept. Not deployed, not part of the funding request |
| `scanner/` | Risk Scanner: rule-based checks (18 checks, two scores, JSON report) with 39 automated tests using BNB Chain RPC, DexScreener and GoPlus data |
| `docs/` | Architecture notes and dataset methodology |

## Roadmap (proposed, depends on funding and team capacity)

1. **Weeks 1 to 6:** Public hosted demo, documentation, first 50 verified dataset entries.
2. **Weeks 7 to 12:** about 150 verified entries, richer holder and age data, first public accuracy report including failures.
3. **Weeks 13 to 20:** simulation-based honeypot detection, an open API, and a pilot with traders.

Anything beyond this (ML models, other chains, a token) comes only after validation, independent audits and legal review.

## Contact

- Partnerships: partnerships@tavorix.xyz
- Security reports: security@tavorix.xyz (see `SECURITY.md`)
