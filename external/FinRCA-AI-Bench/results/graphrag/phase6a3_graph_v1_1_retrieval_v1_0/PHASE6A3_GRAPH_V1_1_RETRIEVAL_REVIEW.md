# Phase 6A.3 Graph v1.1 Retrieval Review

## A. Executive finding

Graph v1.1 candidate traversal is technically conformant and deterministic, but the frozen policy does not authorize an unambiguous Top-40 selector. Retrieval evaluation stopped before validation gold. BLOCKED — GRAPH v1.1 EVIDENCE-SELECTION POLICY REQUIRES SEPARATE FREEZE

## B. Frozen Graph v1.1 lineage

73 raw-byte lineage checks passed across 57 distinct paths.

## C. Implementation conformance

Runtime traversal loads all 30 transitions from the frozen registry, applies default deny, exact edge/type/direction/provenance/cutoff checks, depth 3, simple paths, context termination, GL termination, and hub prohibitions.

## D. Ranking/evidence-selection compatibility decision

BLOCKED_AMBIGUOUS. Selection and gold evaluation are not authorized.

## E. Exact anchor resolution

416 cases resolve exactly to 430 roots and reproduce the authoritative Phase 6A anchor resolutions.

## F. Candidate traversal statistics

13,371 paths; per-case p50/p95/p99/max 31/68/78/91.

## G. Multi-hop traversal statistics

Depth counts: {'1': 3332, '2': 4477, '3': 5562}. These are structural candidate counts, not retrieval success.

## H. Depth distribution

Depth 1/2/3 paths: 3,332/4,477/5,562.

## I. Candidate record distribution

Per-case candidate records p50/p95/p99/max 20/38/43/50.

## J. 40-record budget pressure

9 cases exceed 40 candidates; 33 candidate incidences lie above a hypothetical per-case count of 40. No records were dropped because selection was not run.

## K. Relational-RAG baseline verification

NOT RUN — EVIDENCE-SELECTION POLICY BLOCKED BEFORE GOLD

## L. Graph v1.1 primary retrieval metrics

NOT RUN — EVIDENCE-SELECTION POLICY BLOCKED BEFORE GOLD

## M. Relational-RAG vs Graph v1.1

NOT RUN — EVIDENCE-SELECTION POLICY BLOCKED BEFORE GOLD

## N. Candidate-pool vs Top40 recall

NOT RUN — EVIDENCE-SELECTION POLICY BLOCKED BEFORE GOLD

## O. Full evidence coverage

NOT RUN — EVIDENCE-SELECTION POLICY BLOCKED BEFORE GOLD

## P. Multi-hop-only evidence contribution

NOT RUN — EVIDENCE-SELECTION POLICY BLOCKED BEFORE GOLD

## Q. Depth-2 contribution

NOT RUN — EVIDENCE-SELECTION POLICY BLOCKED BEFORE GOLD

## R. Depth-3 contribution

NOT RUN — EVIDENCE-SELECTION POLICY BLOCKED BEFORE GOLD

## S. Transition contribution

Candidate usage is recorded pre-gold. Selected-path usage and gold contribution are not computable because selection and evaluation did not run.

## T. Path-class contribution

Candidate path-class sequences are frozen. Gold contribution is not computable.

## U. Anchor-type breakdown

{"bank_transaction":{"candidate_paths":{"count":26,"maximum":2,"mean":1.1538461538461537,"median":1.0,"p50_nearest_rank":1,"p75_nearest_rank":1,"p90_nearest_rank":2,"p95_nearest_rank":2,"p99_nearest_rank":2,"total":30},"candidate_unique_records":{"count":26,"maximum":3,"mean":2.1538461538461537,"median":2.0,"p50_nearest_rank":2,"p75_nearest_rank":2,"p90_nearest_rank":3,"p95_nearest_rank":3,"p99_nearest_rank":3,"total":56},"case_count":26,"paths_by_exact_depth":{"1":30,"2":0,"3":0}},"gl_journal":{"candidate_paths":{"count":14,"maximum":78,"mean":46.42857142857143,"median":39.0,"p50_nearest_rank":38,"p75_nearest_rank":58,"p90_nearest_rank":76,"p95_nearest_rank":78,"p99_nearest_rank":78,"total":650},"candidate_unique_records":{"count":14,"maximum":36,"mean":21.642857142857142,"median":18.5,"p50_nearest_rank":18,"p75_nearest_rank":26,"p90_nearest_rank":35,"p95_nearest_rank":36,"p99_nearest_rank":36,"total":303},"case_count":14,"paths_by_exact_depth":{"1":28,"2":128,"3":494}},"invoice":{"candidate_paths":{"count":195,"maximum":64,"mean":25.087179487179487,"median":24,"p50_nearest_rank":24,"p75_nearest_rank":32,"p90_nearest_rank":45,"p95_nearest_rank":51,"p99_nearest_rank":57,"total":4892},"candidate_unique_records":{"count":195,"maximum":40,"mean":18.087179487179487,"median":18,"p50_nearest_rank":18,"p75_nearest_rank":22,"p90_nearest_rank":27,"p95_nearest_rank":35,"p99_nearest_rank":39,"total":3527},"case_count":195,"paths_by_exact_depth":{"1":2202,"2":1269,"3":1421}},"payment":{"candidate_paths":{"count":181,"maximum":91,"mean":43.08839779005525,"median":42,"p50_nearest_rank":42,"p75_nearest_rank":58,"p90_nearest_rank":68,"p95_nearest_rank":74,"p99_nearest_rank":87,"total":7799},"candidate_unique_records":{"count":181,"maximum":50,"mean":24.76795580110497,"median":24,"p50_nearest_rank":24,"p75_nearest_rank":32,"p90_nearest_rank":38,"p95_nearest_rank":40,"p99_nearest_rank":47,"total":4483},"case_count":181,"paths_by_exact_depth":{"1":1072,"2":3080,"3":3647}}}

## V. Bank-transaction limitation

Payment↔BankTransaction and BankStatement membership remain absent. No heuristic or Tier-B linkage was introduced.

## W. Failure attribution

All 416 cases have SELECTION_FAILURE solely because the evidence-selection policy is ambiguous; this is not a traversal implementation failure and no gold miss taxonomy was computed.

## X. Context composition

Candidate node-type composition is recorded; selected context composition is not computable.

## Y. Token analysis

NOT COMPUTABLE — no selected evidence context exists and no token cap was introduced.

## Z. Latency

Graph load 3163.310 ms; candidate generation per-case median/p95/p99/max 0.249/0.564/0.832/291.323 ms. Selection and end-to-end selected retrieval are not computable.

## AA. Determinism

PASS_100_PERCENT_SEMANTIC_CONTENT_EQUIVALENCE; 5 semantic retrieval components matched across two complete candidate runs.

## AB. Test results

Phase 6A.3 tests: PASS (PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/graphrag/test_phase6a3_graph_v1_1.py -q). Full repository suite was not run because unrelated tests may open prohibited held-out/gold resources; this isolation choice is deliberate.

## AC. Scientific integrity

PASS; validation gold and held-out gold were not opened, and no LLM/API/embedding/semantic/Tier-B activity occurred.

## AD. Known limitations

No empirical Recall@40 or evidence-coverage conclusion is possible until a separate evidence-selection freeze authorizes deterministic Top-40 behavior.

## AE. Interpretation

The candidate implementation reproduces the frozen structural topology. This does not establish retrieval effectiveness.

## AF. Phase 6B readiness recommendation

Phase 6B readiness is not assessed because the mandatory selection preflight blocked before gold evaluation.

BLOCKED — GRAPH v1.1 EVIDENCE-SELECTION POLICY REQUIRES SEPARATE FREEZE
