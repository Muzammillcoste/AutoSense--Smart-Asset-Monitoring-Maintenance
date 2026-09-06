# IEEE upgrade progress

## Phase A — preserved corrected benchmark

- Confirmed branch: `research-paper-v2`.
- Recorded starting commit: `4b0d64e0c6bd06f19f4c7131a8baac9fc44076fa`.
- Verified all required corrected benchmark artifacts without overwriting them.
- Passed `test_protocol.py` (4 tests) and `verify_results.py`.
- The latter verified the final-comparison SHA256, aligned splits, persisted
  predictions and model reloads for all three AutoSense targets.
