# Dataset labeling rules

Labels: `rugpull`, `honeypot`, `scam_other`, `healthy`, `uncertain`.

- **rugpull:** liquidity removed or creators dumped most supply, confirmed by an independent report AND an on-chain link for the same token address (the token or its deployer on BscScan matches the report).
- **honeypot:** buys succeed, sells blocked or heavily taxed for non-creators, confirmed by simulation AND an independent report.
- **healthy:** at least 12 months old, liquidity still present, no confirmed scam reports, meaningful organic holders, and the contract address matches a second source (for example the BscScan label plus the CoinGecko contract list).
- **uncertain:** only one source so far, unclear identity or status (bridge tokens, name copies, unlabeled contracts). These rows are kept but are NOT scored.
- Every scored row needs two evidence sources (on-chain link plus report or aggregator). If you cannot verify, use `uncertain` or leave it out.
- Be honest about label strength. If a report only says "potential" or "highly suspected", or the project disputes it, write that in `notes`. If the theft or liquidity-removal transaction was not inspected, say so in `notes`.
- Never label a token as scam only because the scanner scored it high. That would make the test circular.
- Record in `notes` the scan result and the scan date. Old incidents are scanned in their current state, which can differ from the state before the incident.
- Target: 100 to 200 rows, roughly balanced between scam and healthy, including active scams and honeypots, not only old rugpulls.
- Held-out test set: before any tuning, freeze a list of test rows (about 30%) and never tune rules, weights or thresholds on them. Round 2 of `EVALUATION.md` did not use a held-out split.
- Metrics to report: precision, recall and false-positive rate, with confidence intervals, together with every failure.
