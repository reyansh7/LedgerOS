# Phase 6A.1 Structural Reachability & Traversal-Direction Audit

## A. Executive finding

Useful exact 2-hop and 3-hop paths physically exist. They are largely inaccessible to Graph Retrieval v1.0 because the frozen motif vocabulary is almost entirely one-hop and its only multi-hop motif is directionally unusable from every eligible validation anchor. Safe reverse diagnostic traversal raises depth-2/3 reachability without an observed explosion, but this is not an implemented retrieval model.

## B. Frozen artifact verification

PASS: all 13 mandatory raw-byte SHA-256 values matched. No frozen or Phase 6A artifact was modified.

## C. Research question

The audit separates physical graph reachability, frozen motif reachability, and actual Graph v1.0 emission. Path generation is label-independent; validation evidence is opened only in the secondary recall stage.

## D. Graph topology summary

The persisted graph contains 155,391 nodes in 14 types and 184,223 deterministic edges across all 22 frozen executable relation types. Traversal is limited to depth 3, exact frozen edges, cutoff-eligible nodes/edges, frozen Vendor/Employee hub exclusions, and simple paths.

## E. Stored-direction depth-1/2/3 reachability

| Exact depth | Anchors with path | Mean | Median | p95 | Max | Total paths |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 316/416 | 0.940 | 1.0 | 2 | 2 | 391 |
| 2 | 129/416 | 0.421 | 0.0 | 2 | 4 | 175 |
| 3 | 9/416 | 0.048 | 0.0 | 0 | 4 | 20 |

| Anchor type | Depth | Anchors with path | Mean | Median | p95 | Max |
|---|---:|---:|---:|---:|---:|---:|
| bank_transaction | 1 | 0/26 | 0.000 | 0.0 | 0 | 0 |
| bank_transaction | 2 | 0/26 | 0.000 | 0.0 | 0 | 0 |
| bank_transaction | 3 | 0/26 | 0.000 | 0.0 | 0 | 0 |
| gl_journal | 1 | 14/14 | 2.000 | 2.0 | 2 | 2 |
| gl_journal | 2 | 14/14 | 2.571 | 2.0 | 4 | 4 |
| gl_journal | 3 | 9/14 | 1.429 | 2.0 | 4 | 4 |
| invoice | 1 | 139/195 | 0.713 | 1.0 | 1 | 1 |
| invoice | 2 | 0/195 | 0.000 | 0.0 | 0 | 0 |
| invoice | 3 | 0/195 | 0.000 | 0.0 | 0 | 0 |
| payment | 1 | 163/181 | 1.238 | 1.0 | 2 | 2 |
| payment | 2 | 115/181 | 0.768 | 1.0 | 2 | 2 |
| payment | 3 | 0/181 | 0.000 | 0.0 | 0 | 0 |

Stored direction alone mostly follows child/source records toward parents/targets; it offers little investigative expansion from invoice, payment, or bank-transaction anchors.

## F. Safe-reverse diagnostic depth-1/2/3 reachability

| Exact depth | Anchors with path | Mean | Median | p95 | Max | Total paths |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 416/416 | 8.010 | 7.0 | 16 | 20 | 3332 |
| 2 | 340/416 | 10.762 | 10.0 | 28 | 34 | 4477 |
| 3 | 340/416 | 13.370 | 10.0 | 35 | 64 | 5562 |

| Anchor type | Depth | Anchors with path | Mean | Median | p95 | Max |
|---|---:|---:|---:|---:|---:|---:|
| bank_transaction | 1 | 26/26 | 1.154 | 1.0 | 2 | 2 |
| bank_transaction | 2 | 0/26 | 0.000 | 0.0 | 0 | 0 |
| bank_transaction | 3 | 0/26 | 0.000 | 0.0 | 0 | 0 |
| gl_journal | 1 | 14/14 | 2.000 | 2.0 | 2 | 2 |
| gl_journal | 2 | 14/14 | 9.143 | 8.0 | 12 | 12 |
| gl_journal | 3 | 14/14 | 35.286 | 29.0 | 64 | 64 |
| invoice | 1 | 195/195 | 11.292 | 13.0 | 17 | 20 |
| invoice | 2 | 163/195 | 6.508 | 5.0 | 16 | 21 |
| invoice | 3 | 163/195 | 7.287 | 6.0 | 24 | 31 |
| payment | 1 | 181/181 | 5.923 | 6.0 | 8 | 9 |
| payment | 2 | 163/181 | 17.017 | 15.0 | 30 | 34 |
| payment | 3 | 163/181 | 20.149 | 20.0 | 36 | 48 |

## G. Directionality audit

The 22 relations classify as `{'FORWARD_ONLY_NATURAL': 0, 'SAFE_REVERSIBLE_CANDIDATE': 16, 'REVERSE_HUB_RISK': 6, 'REVERSE_SEMANTICALLY_INVALID': 0, 'NEEDS_REVIEW': 0}`. 15/16 structurally safe relations already have frozen v1.0 reverse permission. `AUDIT_EVENT_FOR_VENDOR` is exact with maximum reverse degree 1 but remains excluded from View B by the separate frozen Vendor prohibition; six other Vendor/Employee relations are reverse-hub risks. Persisted edge orientation frequently requires a reverse step, but no validation-anchor path in View B requires reverse permission absent from v1.0. Classification is advisory only.

## H. Payment-allocation traversal analysis

The exact allocation-node chain `INVOICE <- ALLOCATION_TO_INVOICE - PAYMENT_ALLOCATION -> ALLOCATION_OF_PAYMENT -> PAYMENT` occurs in 88 safe-diagnostic paths across 56 validation anchors and 7180 paths globally. These edges already exist; no relationship was synthesized.

The global frozen graph also supports `PURCHASE_ORDER -> INVOICE` (5024 paths), `PURCHASE_ORDER -> INVOICE -> PAYMENT` (4434), `INVOICE -> PAYMENT -> GL_ENTRY` (14468), and `PURCHASE_ORDER -> INVOICE -> PAYMENT -> GL_ENTRY` (8952). Their validation-anchor counts are zero for purchase-order-starting chains because the authorized routes contain no purchase-order anchors, not because the edges are absent.

## I. GL source traversal analysis

Safe reverse traversal gives new GL-entry reachability over stored direction to 353 anchors at depth 1, 233 at exact depth 2, and 250 at exact depth 3. Each GL edge retains its source_transaction_id-backed provenance.

## J. Approval traversal analysis

`INVOICE -> APPROVAL_EVENT` is realized by 339 exact reverse paths across 152 validation anchors and 17429 paths globally. Relation-level reverse degree is reported in `relation_directionality_audit.json`.

## K. Audit-event traversal analysis

Entity-local operational-entity-to-audit-event traversal yields 610 one-hop paths across 355 validation anchors and 27894 paths globally. Actor/Employee continuation was not performed.

## L. Frozen motif coverage

Under the primary safe-reverse denominator, frozen motifs represent 5/76 distinct direction-aware typed sequences: **6.579%**. 347/416 cases with raw paths have at least one represented sequence; mean per-case sequence coverage is 12.014%.

## M. Hop-survival funnel

`416 anchors -> 390 applicable -> 347 first-hop -> 0 second-hop -> 0 third-hop`. The frozen design contains seven one-hop motifs, one two-hop motif, and zero three-hop motifs.

## N. Explanation of zero multi-hop output

There were 195 eligible attempts of the sole multi-hop motif and 0 passed hop 1. Exactly 100.000% failed because `INVOICE_REFERENCES_PO:reverse` was attempted from INVOICE rather than PURCHASE_ORDER. Disabled relation-level reverse permission, edge absence, hub policy, temporal policy, ranking/budget, and implementation behavior each account for 0% of the zero multi-hop outcome. Seven other motifs terminate after one edge, and no three-hop motif exists.

## O. Raw graph vs motif gap taxonomy

Unrepresented safe-topology sequence incidences: `{'NO_MOTIF_FOR_ANCHOR_TYPE': 26, 'MOTIF_DIRECTION_MISMATCH': 302, 'RELATION_DIRECTION_MISMATCH': 0, 'MOTIF_TOO_SHORT': 444, 'MOTIF_SEQUENCE_MISSING': 4245, 'HUB_RESTRICTION': 0, 'TEMPORAL_RESTRICTION': 0, 'EDGE_NOT_PRESENT': 0, 'IMPLEMENTATION_EXECUTION_GAP': 0, 'OTHER / NOT SAFELY ATTRIBUTABLE': 0}`. Case-primary categories: `{'NO_MOTIF_FOR_ANCHOR_TYPE': 26, 'MOTIF_DIRECTION_MISMATCH': 24, 'RELATION_DIRECTION_MISMATCH': 0, 'MOTIF_TOO_SHORT': 21, 'MOTIF_SEQUENCE_MISSING': 319, 'HUB_RESTRICTION': 0, 'TEMPORAL_RESTRICTION': 0, 'EDGE_NOT_PRESENT': 26, 'IMPLEMENTATION_EXECUTION_GAP': 0, 'OTHER / NOT SAFELY ATTRIBUTABLE': 0}`. The machine-readable artifact separates sequence gaps, failed motif attempts, and hub incidents to avoid double-counting mechanisms.

## P. Reachability explosion / hub risk

Safe reverse traversal produced p50 31.0, p90 62, p95 68, p99 78, and max 91 paths per route anchor across depths 1–3. No uncontrolled expansion was observed under the frozen hub exclusions; this does not authorize broader traversal.

## Q. Cycle analysis

Simple-path enforcement removed 8433 repeated-record candidates ({'depth_2': 3332, 'depth_3': 5101}). No additional cycle rule was used.

## R. Fixed motifs vs typed grammar

Fixed motifs are easiest to audit but brittle across anchor orientation and lifecycle continuations. A typed grammar is structurally more expressive and remained bounded in this diagnostic when constrained to exact entity-local relations, depth 3, frozen hubs, cutoff eligibility, and simple paths. Both options remain PROPOSAL_ONLY; see `typed_traversal_grammar_analysis.md`.

## S. Relational-RAG comparison

| Retrieval/topology | 1-hop anchors | 2-hop anchors | 3-hop anchors | Required-doc diagnostic recall |
|---|---:|---:|---:|---:|
| Relational-RAG | N/A | N/A | N/A | 66.716% |
| Frozen motif Graph v1.0 | 347 | 0 | 0 | 31.642% |
| Raw graph stored direction | 316 | 129 | 9 | 19.701% |
| Raw graph safe-reverse diagnostic | 416 | 340 | 340 | 77.239% |

Relational-RAG remains the serious baseline (66.716% micro Recall@40 versus Graph v1.0 at 31.642%). Any later graph design must show value beyond exact one-hop relational expansion, not merely beyond Dense RAG.

## T. Structural recommendation for Graph v1.1

`CONSIDER_TYPED_TRAVERSAL_GRAMMAR` (PROPOSAL_ONLY). Many exact multi-hop lifecycle sequences exist, fixed-motif sequence coverage is low, and constrained expansion is bounded in this corpus. This recommends an independently reviewed design experiment, not a freeze or implementation. Relational-RAG should remain the primary comparator and may remain the preferred production architecture if a future graph experiment does not add evidence beyond it.

## U. Scientific-integrity audit

PASS. Every prohibited-action field in `scientific_integrity.json` is false. Diagnostic reverse topology is true and remained in memory/output-only analysis.

## V. Deviations

No substantive protocol deviation. Exact-multi GL journal routes are counted once in case-level metrics while both resolved GL_ENTRY anchors are enumerated. Motif-coverage ambiguity is resolved with a direction-aware typed-sequence definition documented in the JSON artifact.

## W. Proposed next action

Independent researcher review should decide whether to authorize separate v1.1 fixed-motif, safe-bidirectional, and typed-grammar experiments. Do not implement or evaluate a modified retriever before that decision.

RECOMMEND DESIGN GRAPH v1.1 WITH TYPED FINANCIAL TRAVERSAL GRAMMAR
