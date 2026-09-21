# Preserved Post-Evaluation Implementation Defect

- Preserved run: `phase3_classical_ml_v1_0_20260808T210000Z`
- Discovered by: frozen pre-training suspicious-correlation audit, reviewed during the formal post-run artifact audit
- Affected feature: `NUM044 vendor_name_token_count`
- Frozen requirement: `docs/ml_feature_registry_v1.0.csv` specifies “Training median; explicit entity missingness retained”; frozen specification sections 5.4 and 7 require missing numeric values to remain missing until train-median imputation.
- Defect: the generic feature initializer treated every name ending in `_count` as a relationship-set count and initialized it to `0.0`. When the vendor entity was missing, `vendor_name_token_count` therefore became zero instead of numeric missing.
- Scope of correction: replace the suffix heuristic with an explicit zero-default registry for true relationship counts. No feature, model family, search configuration, threshold, weighting rule, preprocessing strategy, or decision rule changed.
- Original predictions/results: preserved without overwrite.
- Corrected evaluation: must use a new immutable run ID and retain both results.

This is an implementation correction against the already frozen feature registry, not post-test model tuning.
