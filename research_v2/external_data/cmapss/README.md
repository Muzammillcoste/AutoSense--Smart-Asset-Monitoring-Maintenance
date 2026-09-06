# NASA C-MAPSS external-data placement

The FD001 raw files are intentionally not committed.  They must be obtained
from the authoritative NASA C-MAPSS archive and placed in this directory as:

- `CMAPSSData.zip` (optional retained source archive)
- `train_FD001.txt`
- `test_FD001.txt`
- `RUL_FD001.txt`

The IEEE-upgrade forecasting experiment uses only `train_FD001.txt`, because
the trajectories run to failure.  `test_FD001.txt` and `RUL_FD001.txt` are
retained only to validate archive completeness and provenance; no future
sensor values are inferred beyond the official test-trajectory truncation.

The acquisition URL, access date, hashes, citation, and usage note are
recorded in `research_v2/ieee_results/provenance.json` after acquisition.
