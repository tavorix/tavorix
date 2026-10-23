# Risk Scanner v1 checks (rule-based)

| # | Check | Signal |
|---|---|---|
| 1 | Hidden mint function | Owner can create new supply |
| 2 | Blacklist / pause / transfer lock | Owner can freeze holders |
| 3 | Buy/sell tax | Tax above threshold, or tax changeable by owner |
| 4 | Honeypot simulation | Simulated sell fails or loses most value |
| 5 | Holder concentration | Top wallets hold large share (excluding LP and burn) |
| 6 | LP lock | LP not locked, or unlock soon |
| 7 | Contract age and verification | Very new, or source not verified |
| 8 | Ownership | Owner not renounced and has dangerous powers |
| 9 | Proxy / upgradeable | Logic can change after launch |
| 10 | Deployer history | Deployer linked to earlier scam tokens |

Output: score 0-100 plus a plain-language reason for each triggered check. Scores are risk estimates, never safety guarantees.
