# Tavorix scanner

Input: BNB Smart Chain token address. Output: two risk estimates (scam risk and centralization), the reasons, evidence coverage, and a per-check matrix. See `CHECKS.md` for the full list of checks and their data sources.

Status: early, rule-based, **not validated**. A public accuracy report is a planned milestone and will include failures.

## Run the tests (no network needed)
    python3 -m unittest discover -s tests -v

## Measure accuracy
1. Fill `dataset_template.csv` (labels + evidence), following `LABELING.md`.
2. Collect each token's facts with `collect.py` (see "Build the accuracy test" below) into a CSV like `features_template.csv`.
3. Split rows 70/30 (train/test). Tune weights and threshold on train only.
4. `python3 evaluate.py test_features.csv --threshold 40` and publish precision, recall and false-positive rate.

Weights in `checks.py` are initial guesses, not validated. Scores are risk estimates, never safety guarantees.

## Scan a real token (needs network; run on your own machine)
    python3 scan.py 0xTOKEN_ADDRESS --rpc https://YOUR_BSC_RPC_URL

Notes:
- BscScan's own API was folded into Etherscan API V2 (use chainid=56). Check the current plan/pricing before relying on it.
- `data.py` currently fills: mint/blacklist/pause/proxy hints (bytecode selector scan), owner renounced and owner type, LP locked %, estimated USD liquidity (biggest WBNB or USDT PancakeSwap v2 pool).
  Optional sources (DexScreener, GoPlus) fill most other checks when reachable; anything still missing stays unknown (None) and is never counted as safe.
  Liquidity and LP lock only look at the token/WBNB PancakeSwap v2 pool (tokens paired with USDT or traded on v3 show unknown).
- Selector and address constants in `config.py` must be verified before use. Bytecode scanning gives hints, not proof.

## Build the accuracy test (no manual copying)
1. In `dataset_template.csv`, add rows: `token_address` and `label` (rugpull, honeypot, scam_other, healthy). Keep evidence columns filled.
2. `python collect.py dataset_template.csv features.csv --rpc $env:RPC` (reads each token from BNB Chain).
3. `python evaluate.py features.csv --threshold 40` for precision, recall and false-positive rate.
Tokens with no code on this chain, or errors, are skipped and listed. Report on a held-out test split only.

## Two scores
- **Scam-risk score**: signals associated with scams (honeypot, low liquidity, unlocked LP, high tax, ...). This drives accuracy tests.
- **Centralization (control) score**: owner/mint/blacklist/pause/proxy powers. Many legitimate tokens (bridge tokens, issuer-controlled tokens) have these, so they are reported separately and do not count as scam risk.

## DexScreener (optional context, no key)
`scan.py` and `collect.py` also ask DexScreener's public API for liquidity across ALL DEX pools and the age of the oldest pool
(used as a proxy for token age). Established tokens (older than 180 days with at least $100k liquidity) get a smaller
"LP not locked" penalty. This rule is a hypothesis: validate it on labeled data, including scams that aged before the rugpull.
If DexScreener is unreachable, the scanner falls back to on-chain data only.

## GoPlus (optional data source, no key)
`scan.py` and `collect.py` also query GoPlus Security's public token_security API (chain 56) for its honeypot/tax simulation,
holder concentration, LP lock, open-source status, mintable/blacklist/pause/proxy flags and creator history. When present these values
override our own guesses. GoPlus is third-party data: it can be wrong, rate-limited or unavailable (then fields stay unknown).
Network calls retry 3 times. Keep checking results against labeled examples.

## Known limitation found in testing
An old, deeply traded scam (SQUID V1) scored low on scam risk when only on-chain + DexScreener data was used, because the
"established token" rule discounted it. Do not treat age and liquidity alone as proof of safety.

## Local demo (token check page)
    python demo/server.py
Open http://127.0.0.1:8000 in your browser, paste a BNB Chain token address, and press Scan.
The server only listens on your own computer. Optional: set `TAVORIX_RPC` to your own RPC URL (keep it private).

## Report details (demo)
The demo JSON report now includes: `evidence_coverage_pct` (share of checks that had data), a `checks` matrix
(flagged / clear / no_data per check), `meta` (network, sources that returned data, UTC timestamp), and a
"Download JSON report" button on the page. Checks with no data are never counted as safe.

## Dataset status
`my_dataset.csv` holds only rows that meet `LABELING.md` (two evidence sources). Rows still waiting for a second source are in `dataset_pending.csv` and are not used for accuracy numbers. The dataset is small and a public accuracy report is still a planned milestone.
