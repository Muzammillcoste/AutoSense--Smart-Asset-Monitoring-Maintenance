# IEEE upgrade progress

## Phase A — preserved corrected benchmark

- Confirmed branch: `research-paper-v2`.
- Recorded starting commit: `4b0d64e0c6bd06f19f4c7131a8baac9fc44076fa`.
- Verified all required corrected benchmark artifacts without overwriting them.
- Passed `test_protocol.py` (4 tests) and `verify_results.py`.
- The latter verified the final-comparison SHA256, aligned splits, persisted
  predictions and model reloads for all three AutoSense targets.

## C-MAPSS acquisition and pre-registration

- Acquired the authoritative NASA C-MAPSS archive; raw data remain git-ignored
  under `research_v2/external_data/cmapss/`, with hashes and source details in
  `provenance.json`.
- Validated `train_FD001.txt` (100 ordered run-to-failure engines; 26 numeric
  columns) and saved the pre-test seed-42 70/15/15 engine split.
- Performed the training-engine-only near-constant filter and Spearman ranking;
  the selected channels are `sensor_9`, `sensor_11`, `sensor_14`, and
  `sensor_12`.  No validation/test engine influenced either decision.
