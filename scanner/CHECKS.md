# Checks (18)

| # | Check | Type | Data source |
|---|---|---|---|
| 1 | Honeypot (sell) test | Scam signal | GoPlus (only counted when a tradable pool exists) |
| 2 | Impersonates a known token | Scam signal | BNB Chain RPC (name and symbol), GoPlus; known tokens listed in config.py |
| 3 | Can mint new tokens | Centralization | Bytecode scan, GoPlus |
| 4 | Can blacklist wallets | Centralization | Bytecode scan, GoPlus |
| 5 | Can pause transfers | Centralization | Bytecode scan, GoPlus |
| 6 | High buy/sell tax | Scam signal | GoPlus (only counted when a tradable pool exists) |
| 7 | Tax can be changed | Scam signal | GoPlus |
| 8 | Single large holder | Scam signal | GoPlus |
| 9 | Top-10 holder concentration | Scam signal | GoPlus |
| 10 | Liquidity not locked | Scam signal | On-chain LP balances, GoPlus |
| 11 | Liquidity unlocks soon | Scam signal | Not available yet |
| 12 | Recently launched | Scam signal | DexScreener (age of oldest pool) |
| 13 | Source code not verified | Scam signal | GoPlus |
| 14 | Owner not renounced | Centralization | BNB Chain RPC |
| 15 | Upgradeable contract | Centralization | BNB Chain RPC, GoPlus |
| 16 | Deployer linked to scams | Scam signal | GoPlus |
| 17 | Owner is a single wallet | Centralization | BNB Chain RPC |
| 18 | Thin liquidity | Scam signal | DexScreener, on-chain pools |

Two scores come out of these: a **scam-risk score** (scam signals) and a **centralization score** (control powers). Checks with no data are shown as "no data" and are never counted as safe. Weights are initial guesses and are not validated.

Notes:
- Honeypot and tax results come from a trade simulation. If the token has no tradable pool, a "clear" result is shown as "no data" instead.
- The impersonation check only knows the tokens listed in `tavorix_scanner/config.py` (`KNOWN_TOKENS`: USDT and WBNB so far). Add more only with official addresses you verified on BscScan. It will not catch every look-alike name.
