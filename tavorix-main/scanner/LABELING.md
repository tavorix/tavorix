# Dataset labeling rules

Labels: `rugpull`, `honeypot`, `scam_other`, `healthy`.

- **rugpull:** liquidity removed or creators dumped most supply, confirmed by on-chain data AND an independent report.
- **honeypot:** buys succeed, sells blocked or heavily taxed for non-creators, confirmed by simulation AND an independent report.
- **healthy:** at least 12 months old, liquidity still present, no confirmed scam reports, meaningful organic holders.
- Every row needs two evidence sources (on-chain link plus report). If you cannot verify, leave it out.
- Target: 100 to 200 rows, roughly balanced between scam and healthy. Hold out 30% as a test set that the rules are never tuned on.
- Metrics to report: precision, recall, false-positive rate on the held-out set.
