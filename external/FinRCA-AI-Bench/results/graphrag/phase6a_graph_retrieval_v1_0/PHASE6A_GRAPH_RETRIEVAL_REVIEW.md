# Phase 6A Deterministic Graph Retrieval Review

## A. Executive conclusion

Implemented the offline deterministic GraphRAG v1.0 retrieval core from the immutable registries: a local graph snapshot, exact anchors, eight motif-bounded traversals, path-first deterministic ranking, a 40-record selector, evidence packets, two ablations, and validation evidence-retrieval evaluation. No LLM, API call, new embedding, semantic fallback, Tier B edge, synthetic node, unrestricted graph search, or held-out test evaluation was performed.

## B. Frozen lineage verification

Status: **PASS**. Phase 5 index `527b5980f1544dda5eab4581f8cb9c498e2a8e7633e4c061dd232b8cff05e3a6`; corpus text manifest `8842865bd6e688f824a0b16450301fb547c62c4ba495099d605753ebaf2ff00d`; vector count 155391; dimensions 1536; cutoff `2026-06-30`.

All seven registry-freeze artifacts and all three persisted corpus files matched their required raw-byte SHA-256 values.

## C. Graph build statistics

The snapshot contains **155,391 nodes** across 14 frozen types and **184,223 edges** across all 22 frozen executable relations.

| Relation | Edges | Source | Target | Traversable / reverse |
|---|---:|---|---|---|
| LINE_OF_PO | 11,231 | PO_LINE | PURCHASE_ORDER | true / true |
| INVOICE_REFERENCES_PO | 5,024 | INVOICE | PURCHASE_ORDER | true / true |
| INVOICE_LINE_REFERENCES_PO_LINE | 11,292 | INVOICE_LINE | PO_LINE | true / true |
| LINE_OF_INVOICE | 18,299 | INVOICE_LINE | INVOICE | true / true |
| APPROVAL_FOR_INVOICE | 17,429 | APPROVAL_EVENT | INVOICE | true / true |
| ALLOCATION_OF_PAYMENT | 7,180 | PAYMENT_ALLOCATION | PAYMENT | true / true |
| ALLOCATION_TO_INVOICE | 7,180 | PAYMENT_ALLOCATION | INVOICE | true / true |
| PAYMENT_ALLOCATED_TO_INVOICE | 7,180 | PAYMENT | INVOICE | true / true |
| VENDOR_CHANGE_FOR_VENDOR | 186 | VENDOR_CHANGE | VENDOR | false / false |
| PO_FOR_VENDOR | 5,000 | PURCHASE_ORDER | VENDOR | false / false |
| INVOICE_FOR_VENDOR | 8,147 | INVOICE | VENDOR | false / false |
| PAYMENT_FOR_VENDOR | 6,200 | PAYMENT | VENDOR | false / false |
| PURCHASE_ORDER_CREATED_BY_EMPLOYEE | 5,000 | PURCHASE_ORDER | EMPLOYEE | false / false |
| VENDOR_CHANGE_CHANGED_BY_EMPLOYEE | 186 | VENDOR_CHANGE | EMPLOYEE | false / false |
| GL_SOURCE_BANK_TRANSACTION | 314 | GL_ENTRY | BANK_TRANSACTION | true / true |
| GL_SOURCE_INVOICE | 33,957 | GL_ENTRY | INVOICE | true / true |
| GL_SOURCE_PAYMENT | 12,484 | GL_ENTRY | PAYMENT | true / true |
| AUDIT_EVENT_FOR_BANK_TRANSACTION | 247 | AUDIT_EVENT | BANK_TRANSACTION | true / true |
| AUDIT_EVENT_FOR_INVOICE | 16,147 | AUDIT_EVENT | INVOICE | true / true |
| AUDIT_EVENT_FOR_PAYMENT | 6,500 | AUDIT_EVENT | PAYMENT | true / true |
| AUDIT_EVENT_FOR_PURCHASE_ORDER | 5,000 | AUDIT_EVENT | PURCHASE_ORDER | true / true |
| AUDIT_EVENT_FOR_VENDOR | 40 | AUDIT_EVENT | VENDOR | false / false |

## D. Integrity validation

Integrity status: **PASS**. Duplicate edges: 0; self-edges: 0; orphans: 0; post-cutoff edges: 0; prohibited edges: 0; accidentally materialized excluded edges: 0.

All executable edges retain source-record provenance. Vendor and Employee relations are persisted for auditability with forward and reverse traversal disabled. Attribute bridge expansion is absent.

## E. Exact anchor resolution

Resolved 416/416 validation anchors (100.000%). Outcomes: {'EXACT_MULTI': 14, 'EXACT_SINGLE': 402}. Anchor-type counts: {'bank_transaction': 26, 'gl_journal': 14, 'invoice': 195, 'payment': 181}. For each exact-resolving method the first anchor rank is 1; Graph/Anchor/Relational maximum anchor rank is 2. GL journal inputs resolve only to existing GL_ENTRY lines through the journal grouping attribute; no journal node is created.

## F. Standard RAG validation baseline

The immutable Standard Dense RAG K=40 baseline returned macro Recall@40 1.259%, micro Recall@40 1.493%, hit rate 8.894%, and full-evidence coverage 0.000%.

## G. Anchor-RAG results

Anchor-RAG macro Recall@40: 18.629%; full-evidence coverage: 0.000%; anchor inclusion: 100.000%.

## H. Relational-RAG results

Relational-RAG macro Recall@40: 68.882%; full-evidence coverage: 15.144%; anchor inclusion: 100.000%.

## I. Deterministic Graph Retrieval results

Graph Retrieval macro Recall@40: 36.073%; micro Recall@40: 31.642%; hit rate: 94.231%; full-evidence coverage: 5.048%; anchor inclusion: 100.000%.

## J. Evidence recall comparison

| Retrieval system | Anchor inclusion | Required-doc Recall@40 (micro) | Required-doc Recall@40 (macro) | Full evidence coverage | Avg records | Avg source tokens |
|---|---:|---:|---:|---:|---:|---:|
| Standard Dense RAG | 7.212% | 1.493% | 1.259% | 0.000% | 40.00 | 5582.06 |
| Anchor-RAG | 100.000% | 15.522% | 18.629% | 0.000% | 40.00 | 5583.81 |
| Relational-RAG | 100.000% | 66.716% | 68.882% | 15.144% | 9.01 | 1109.63 |
| Graph Retrieval v1.0 | 100.000% | 31.642% | 36.073% | 5.048% | 3.83 | 492.15 |

Confidence intervals use the same deterministic 10,000-resample bootstrap seed as Phase 5. Detailed intervals and anchor-type breakdowns are machine-readable in `evaluation/`.

## K. Full-evidence coverage comparison

Paired outcomes: `{'both_fail': 395, 'standard_fail_graph_success': 21}`. No cases were filtered.

## L. Candidate-pool versus Top-40 analysis

Graph candidate-pool micro required-evidence recall was 31.642%; selected graph evidence recall was 31.642%. The pool contained 1,179 path incidences and 1,595 unique-record incidences across cases. No record was lost to the 40-record cap. Complete gold-path coverage is **NOT COMPUTABLE FROM AUTHORIZED VALIDATION ARTIFACTS**, because no frozen gold path-instantiation contract exists.

## M. Path and motif diagnostics

| Motif | Eligible cases | Candidate paths | Selected paths | Evidence-hit paths |
|---|---:|---:|---:|---:|
| GL_ENTRY_SOURCE_TRANSACTION | 14 | 28 | 28 | 28 |
| INVOICE_APPROVALS | 195 | 339 | 339 | 283 |
| INVOICE_AUDIT_EVENTS | 195 | 344 | 344 | 296 |
| INVOICE_PAYMENTS | 376 | 88 | 88 | 88 |
| PAYMENT_GL_ENTRIES | 195 | 380 | 380 | 380 |
| PO_INVOICE_LINES | 195 | 0 | 0 | 0 |
| PO_WITH_INVOICES | 195 | 0 | 0 | 0 |
| PO_WITH_LINES | 0 | 0 | 0 | 0 |

Relation frequencies are descriptive and are not interpreted as causal importance. All path rows preserve edge provenance and frozen relation order.

## N. Record-type diversity

Average distinct node types per case: Standard Dense RAG 1.42; Anchor-RAG 1.42; Relational-RAG 4.96; Graph Retrieval v1.0 2.33. Graph Retrieval executed an average of 3.28 motifs and selected 2.83 paths per case. Selected direct/multi-hop path counts were 1179/0. Full record-type and cross-type fractions, including anchor-type breakdowns, are in `evaluation/retrieval_composition.json`.

## O. Hubness analysis

No Vendor or Employee reverse-neighborhood motif exists. Graph mean pairwise retrieval-set Jaccard was 0.000007; its maximum non-anchor record frequency was 2 cases. Per-anchor overlap, recurrent-record counts, case percentages, and top-20 slot shares are in `evaluation/hubness_diagnostics.json`; no hub exception was enabled.

## P. Context-size analysis

| System | Median tokens | p90 | p95 | p99 | Max |
|---|---:|---:|---:|---:|---:|
| Standard Dense RAG | 6003.0 | 6026.5 | 6051.0 | 6053.9 | 6058.0 |
| Anchor-RAG | 6002.0 | 6025.0 | 6050.2 | 6053.0 | 6055.0 |
| Relational-RAG | 950.0 | 1942.5 | 2115.0 | 2386.8 | 2570.0 |
| Graph Retrieval v1.0 | 408.0 | 741.5 | 867.2 | 1000.9 | 1003.0 |

The Phase 6B token cap remains **NOT FROZEN**. These distributions are descriptive and did not alter record selection. Per-anchor-type token and cross-type distributions are persisted in `context_size_diagnostics.json`.

## Q. Latency analysis

| System | Mean ms | Median ms | p95 ms | Max ms |
|---|---:|---:|---:|---:|
| Anchor-RAG | 0.019 | 0.014 | 0.033 | 0.278 |
| evidence_selection | 0.005 | 0.004 | 0.008 | 0.054 |
| exact_anchor_resolution | 0.001 | 0.001 | 0.001 | 0.003 |
| graph_build | 10712.327 | 10712.327 | 10712.327 | 10712.327 |
| graph_load | 3620.972 | 3620.972 | 3620.972 | 3620.972 |
| Graph Retrieval v1.0 | 0.092 | 0.067 | 0.211 | 0.892 |
| motif_traversal | 0.014 | 0.008 | 0.022 | 0.755 |
| path_ranking | 0.005 | 0.003 | 0.011 | 0.049 |
| Relational-RAG | 0.079 | 0.069 | 0.136 | 1.530 |
| Standard Dense RAG | 398.861 | 329.441 | 638.658 | 3376.250 |

Latency is explicitly nondeterministic telemetry and is excluded from retrieval-content equivalence hashes.

## R. Failure attribution

All 416 cases have exactly one terminal retrieval status; all four systems completed with `SUCCESS`. Conservative label-independent evidence-failure counts: `{'ANCHOR_UNRESOLVED': 0, 'REQUIRED_NODE_ABSENT_FROM_CORPUS': 0, 'REQUIRED_RELATION_NOT_IN_FROZEN_GRAPH': 0, 'MOTIF_COVERAGE_GAP': 344, 'TRAVERSAL_FAILURE': 0, 'RANKING_BUDGET_LOSS': 0, 'FULL_RETRIEVAL_SUCCESS': 21, 'AMBIGUOUS_NOT_ATTRIBUTABLE': 51}`. Attribution distinguishes unresolved anchors, missing relations, frozen motif gaps, traversal defects, and Top-40 ranking/budget loss; it does not inspect or infer RCA class. Required-evidence 0%/partial/100% coverage buckets and quartiles are in `required_evidence_coverage_distribution.json`.

## S. Determinism/reproducibility

Graph construction and the complete validation retrieval/ablation pass were each run twice independently. Node bytes, edge bytes, anchor resolutions, path IDs, path rankings, selected paths, selected records, evidence packets, and ablation results matched: **PASS** (100% byte/semantic deterministic equivalence).

Reproduction command (requires a non-existing output directory):

```bash
python3 -m src.graphrag.runner run --output-dir /private/tmp/phase6a_reproduction
```

## T. Deviations

No registry-semantic deviation was made. The exact Phase 6B token cap remains unresolved as required. Full path coverage is not computed because authorized validation evidence provides required records, not a frozen path contract. Runtime timestamps and latency are outside deterministic content hashes.

## U. Limitations

The frozen v1.0 graph deliberately cannot traverse payment-bank candidates, conditional employee identity, Vendor/Employee hubs, semantic similarity, or arbitrary neighborhoods. Motifs are directional as serialized; permitted anchor types that do not satisfy the first directed step yield zero paths rather than an invented reverse rule. Retrieval performance is validation-only and does not establish generation or RCA accuracy.

## V. Phase 6B recommendation

All technical lineage, cutoff, provenance, exclusion, cap, separation, and reproducibility gates passed. The validation retrieval result is fully characterized for researcher review. This recommendation does not authorize inference.

RECOMMEND 8/8 GO FOR PHASE 6B GRAPH RAG INFERENCE FREEZE
