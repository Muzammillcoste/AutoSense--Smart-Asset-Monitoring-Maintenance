# Overleaf package validation

- Source commit SHA: `78a6d57a33e782ad5217f80d490a1c3e1c891421`
- Manuscript title: Benchmarking Multi-Step Sensor Forecasting for Threshold-Based Predictive Maintenance: An Integrated IoT-to-Enterprise Framework
- Final ZIP: `AutoSense_Research_Paper_Overleaf_Final.zip`
- ZIP SHA256: `fe2fda5597b7b4c40824094207f49ddd2bcaa34d1befa199e1076a4a664c0ba7`
- Packaged files: 23 (main.tex is at ZIP root)
- References: 11 citation keys; all resolved; no unused bibliography entries.
- Figures: 12; all relative figure paths resolve in a clean extraction.
- Tables: 8; all `\input` paths resolve.
- Labels/references: 18 labels; all 15 references resolve.
- Numerical-claim verification: 28 prose values checked; 6 source CSV hashes verified for generated tables.
- Layout-source review: C-MAPSS sensor/horizon/stage evidence is one composite float, and the prototype and Vehicle Alert screenshots are one composite float; neither uses manual negative spacing or reduced page margins.
- Rendered float/overflow review: pending Overleaf compilation because the local TeX bundle is unavailable.
- TODO/placeholder/FYP scan: passed.
- Stale-claim scan: passed.
- Clean extraction validation: passed (23 files; main.tex at ZIP root).
- Compilation status: blocked.
- Page count: unavailable.

## Compilation note

Tectonic was attempted from the clean-extracted ZIP. It could not obtain its missing TeX bundle because DNS resolution for `relay.fullyjustified.net` failed (error 11002); no local pdflatex/latexmk is available. Compile this ZIP in Overleaf for the final PDF, page count, and rendered overflow review.

## Packaged files

- `figures/engine_24h_forecast_comparison.pdf`
- `figures/horizon_mae_comparison.pdf`
- `figures/ieee_upgrade/architecture_feature_ablation.pdf`
- `figures/ieee_upgrade/cmapss_external_validation.pdf`
- `figures/ieee_upgrade/cmapss_horizon_mae.pdf`
- `figures/ieee_upgrade/cmapss_stage_error.pdf`
- `figures/ieee_upgrade/multiseed_robustness.pdf`
- `figures/ieee_upgrade/threshold_event_evaluation.pdf`
- `figures/model_mae_comparison.pdf`
- `figures/prototype_interfaces.pdf`
- `figures/salesforce_alert.pdf`
- `figures/system_architecture.pdf`
- `main.tex`
- `references.bib`
- `tables/dataset_protocol.tex`
- `tables/ieee_upgrade/architecture_ablation.tex`
- `tables/ieee_upgrade/cmapss_macro_forecasting.tex`
- `tables/ieee_upgrade/feature_ablation.tex`
- `tables/ieee_upgrade/multiseed_robustness.tex`
- `tables/ieee_upgrade/threshold_events.tex`
- `tables/main_comparison.tex`
- `tables/related_work.tex`
- `tables/window_caption.tex`
