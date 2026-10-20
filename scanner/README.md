# Risk Scanner (planned)

Input: BNB Smart Chain token address. Output: risk score (0-100) with explanations.

v1 checks (rule-based): hidden mint, blacklist/pause functions, buy/sell tax, honeypot simulation, holder concentration, LP lock status, contract age, deployer history.

Success criteria: publish precision/recall on a labeled dataset of historical rugpulls and healthy tokens before any public launch.

## Run the tests (no network needed)
    python3 -m unittest discover -s tests -v

## Measure accuracy
1. Fill `dataset_template.csv` (labels + evidence), following `LABELING.md`.
2. Implement `tavorix_scanner/data.py` to collect each token's facts, and save them as a CSV like `features_template.csv`.
3. Split rows 70/30 (train/test). Tune weights and threshold on train only.
4. `python3 evaluate.py test_features.csv --threshold 40` and publish precision, recall and false-positive rate.

Weights in `checks.py` are initial guesses, not validated. Scores are risk estimates, never safety guarantees.
