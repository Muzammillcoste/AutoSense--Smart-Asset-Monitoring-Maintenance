# IEEE experiment artifacts

This directory contains the versioned scripts used for the IEEE-upgrade
experiments.  They are deliberately separate from `research_v2/results`,
which preserves the original corrected benchmark.

All AutoSense scripts use the committed chronological protocol from
`research_v2/protocol.py`.  C-MAPSS scripts require the authoritative FD001
files under `research_v2/external_data/cmapss/` and do not use a mirror with
unknown provenance.
