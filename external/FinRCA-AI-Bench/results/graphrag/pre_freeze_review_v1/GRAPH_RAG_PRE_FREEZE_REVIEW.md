# GraphRAG Pre-Freeze Review

This is a label-independent schema/relation audit only. No graph, graph index, traversal engine, inference, new embedding, query builder, prompt, prediction, or production behavior was created.

## A. Artifact verification

- Authoritative index SHA-256: `527b5980f1544dda5eab4581f8cb9c498e2a8e7633e4c061dd232b8cff05e3a6` (`PASS`)
- Vector matrix: `155391` × `1536`, dtype `float32` (`PASS`)
- Logical text-manifest SHA-256: `8842865bd6e688f824a0b16450301fb547c62c4ba495099d605753ebaf2ff00d` (`PASS`)
- Corpus count: `155391` (`PASS`)
- Corpus hashes: documents `43fe8841d3cbfc64c403349c2336c631c9f6ca9dc35f3e86af1c4ae993441b8c`, metadata `e30183ea1e17af182ad24a3177e776a869ed55718872ba6cc1a169506b4f96fb`, record IDs `1850249832dbb9c75ddddfa8e82615dd1db138cdd83cb2dc455029035e1b0058`
- Per-document text-hash, ordinal, three-file alignment, metadata parity, and operational-schema mismatch counts are all zero.

| Record type | Canonical key | Temporal eligibility | Count |
| --- | --- | --- | --- |
| VENDOR | vendor_id | created_at | 500 |
| VENDOR_CHANGE | change_id | changed_at | 186 |
| PURCHASE_ORDER | po_id | po_date | 5000 |
| PO_LINE | po_line_id | inherits PURCHASE_ORDER.po_date via exact po_id | 11231 |
| INVOICE | invoice_id | created_at | 8147 |
| INVOICE_LINE | invoice_line_id | inherits INVOICE.created_at via exact invoice_id | 18299 |
| APPROVAL_EVENT | approval_event_id | event_timestamp | 17429 |
| PAYMENT | payment_id | created_at | 6200 |
| PAYMENT_ALLOCATION | payment_id, invoice_id, allocation_date | allocation_date | 7180 |
| GL_ENTRY | journal_line_id | posting_date | 46755 |
| BANK_TRANSACTION | bank_transaction_id | posted_date | 6261 |
| BANK_STATEMENT | bank_statement_id | statement_date | 54 |
| EMPLOYEE | employee_id | delivered cutoff snapshot; no row timestamp | 120 |
| AUDIT_EVENT | event_id | timestamp | 28029 |

## B. Node registry

All 14 expected operational record types are present; their counts total `155391`. No synthetic node type was introduced. `GL_JOURNAL` is explicitly excluded because no journal-header source record exists; `journal_id` remains a `GL_ENTRY` grouping/context attribute.

Canonical integrity: `0` duplicate record IDs, `0` duplicate canonical IDs, `0` malformed IDs, `0` missing primary keys, and `0` orphaned composite-key components.

The complete field-use registry is in `graph_node_registry_v1_draft.json`.

## C. Tier A relations

Degree values below are target in-degrees over the complete target domain; p95 uses deterministic nearest-rank calculation.

| Relationship | Evidence field | Resolution | Observed cardinality | Orphans | Degree / hub risk | Recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| PO_LINE_TO_PURCHASE_ORDER | po_id | 100.0000% | N:1 (many source nodes to one target node) | 0 | max=4; p95=4 | READY_FOR_FREEZE |
| INVOICE_TO_PURCHASE_ORDER | po_id | 100.0000% | N:1 (many source nodes to one target node) | 0 | max=2; p95=1 | READY_FOR_FREEZE |
| INVOICE_LINE_TO_PO_LINE | po_line_id | 100.0000% | N:1 (many source nodes to one target node) | 0 | max=2; p95=1 | READY_FOR_FREEZE |
| INVOICE_LINE_TO_INVOICE | invoice_id | 100.0000% | N:1 (many source nodes to one target node) | 0 | max=4; p95=4 | READY_FOR_FREEZE |
| APPROVAL_EVENT_TO_INVOICE | invoice_id | 100.0000% | N:1 (many source nodes to one target node) | 0 | max=4; p95=3 | READY_FOR_FREEZE |
| PAYMENT_ALLOCATION_TO_PAYMENT | payment_id | 100.0000% | N:1 (many source nodes to one target node) | 0 | max=2; p95=2 | READY_FOR_FREEZE |
| PAYMENT_ALLOCATION_TO_INVOICE | invoice_id | 100.0000% | N:1 (many source nodes to one target node) | 0 | max=3; p95=2 | READY_FOR_FREEZE |
| VENDOR_CHANGE_TO_VENDOR | vendor_id | 100.0000% | N:1 (many source nodes to one target node) | 0 | max=6; p95=2 | restricted traversal |
| PURCHASE_ORDER_TO_VENDOR | vendor_id | 100.0000% | N:1 (many source nodes to one target node) | 0 | max=362; p95=30 | restricted traversal |
| INVOICE_TO_VENDOR | vendor_id | 100.0000% | N:1 (many source nodes to one target node) | 0 | max=592; p95=48 | restricted traversal |
| PAYMENT_TO_VENDOR | vendor_id | 100.0000% | N:1 (many source nodes to one target node) | 0 | max=217; p95=37 | restricted traversal |
| PAYMENT_TO_INVOICE_VIA_ALLOCATION | explicit PAYMENT_ALLOCATION provenance | 100.0000% | M:N | 0 | max=3; p95=2 | READY_FOR_FREEZE |

`PAYMENT → INVOICE` is exposed only through explicit, cutoff-eligible `PAYMENT_ALLOCATION` provenance. Vendor relations are exact but not automatically traversable.

## D. GL transaction-type audit

| transaction_type | Rows | Non-null source ID | Deterministic target | Unresolved | Status |
| --- | --- | --- | --- | --- | --- |
| bank_fee | 220 | 220 | BANK_TRANSACTION | 0 | READY_FOR_FREEZE |
| credit_memo | 189 | 189 | INVOICE | 0 | READY_FOR_FREEZE |
| fx_settlement | 94 | 94 | BANK_TRANSACTION | 0 | READY_FOR_FREEZE |
| invoice | 33674 | 33674 | INVOICE | 0 | READY_FOR_FREEZE |
| invoice_cancellation | 94 | 94 | INVOICE | 0 | READY_FOR_FREEZE |
| payment | 12390 | 12390 | PAYMENT | 0 | READY_FOR_FREEZE |
| payment_reversal | 94 | 94 | PAYMENT | 0 | READY_FOR_FREEZE |

All mapping decisions use exact canonical IDs and type agreement. No nearest-ID or semantic matching was used. Full prefix distributions and all-node-type match matrices are in `gl_transaction_type_audit.json`.

## E. Audit-event entity-type audit

| entity_type | Rows | Non-null ID | Canonical target | Unresolved | Ambiguous | Status |
| --- | --- | --- | --- | --- | --- | --- |
| bank_transaction | 247 | 247 | BANK_TRANSACTION | 0 | 0 | READY_FOR_FREEZE |
| gl_journal | 95 | 95 | None | 95 | 0 | UNRESOLVED |
| invoice | 16147 | 16147 | INVOICE | 0 | 0 | READY_FOR_FREEZE |
| payment | 6500 | 6500 | PAYMENT | 0 | 0 | READY_FOR_FREEZE |
| purchase_order | 5000 | 5000 | PURCHASE_ORDER | 0 | 0 | READY_FOR_FREEZE |
| vendor | 40 | 40 | VENDOR | 0 | 0 | READY_FOR_FREEZE |

`gl_journal` is intentionally unresolved at the canonical-node layer. Exact `journal_id` grouping matches are reported only as context; they do not authorize a `GL_JOURNAL` node or traversal edge.

## F. Employee reference audit

| Source field | Populated | Employee matches | Unmatched | Resolved | Classification |
| --- | --- | --- | --- | --- | --- |
| APPROVAL_EVENT.approver_id | 17429 | 9291 | 8138 | 53.3077% | CONDITIONAL |
| AUDIT_EVENT.actor_id | 28029 | 5040 | 22989 | 17.9814% | CONDITIONAL |
| VENDOR_CHANGE.changed_by | 186 | 186 | 0 | 100.0000% | APPROVED_TIER_A |
| PURCHASE_ORDER.created_by | 5000 | 5000 | 0 | 100.0000% | APPROVED_TIER_A |

Unmatched system/service/shared-role actors are preserved as operational context. No synthetic Employee was created and no unmatched actor was discarded.

## G. Payment-bank candidate audit

Exact-reference behavior: `6200` populated payment references, `6261` populated bank payment references, `6053` distinct matching references, and `6161` candidate pairs. There are `147` unmatched payments and `100` unmatched bank transactions at the reference-only stage.

| Candidate predicate | Pairs | Payments matched | Bank rows matched | Ambiguous payments | Ambiguous bank rows |
| --- | --- | --- | --- | --- | --- |
| REFERENCE_ONLY | 6161 | 6053 | 6161 | 108 | 0 |
| REFERENCE_PLUS_CURRENCY | 6114 | 6006 | 6114 | 108 | 0 |
| REFERENCE_PLUS_BANK_ACCOUNT | 0 | 0 | 0 | 0 | 0 |
| REFERENCE_PLUS_ABS_AMOUNT | 5704 | 5657 | 5704 | 47 | 0 |
| REFERENCE_PLUS_DEBIT_DIRECTION | 6114 | 6053 | 6114 | 61 | 0 |
| REFERENCE_PLUS_CURRENCY_ABS_AMOUNT | 5704 | 5657 | 5704 | 47 | 0 |
| REFERENCE_PLUS_CURRENCY_ABS_AMOUNT_DEBIT | 5657 | 5657 | 5657 | 0 | 0 |
| REFERENCE_PLUS_CURRENCY_ACCOUNT_ABS_AMOUNT_DEBIT | 0 | 0 | 0 | 0 | 0 |
| REFERENCE_PLUS_CURRENCY_ABS_AMOUNT_DEBIT_POSTED_ON_OR_AFTER | 5657 | 5657 | 5657 | 0 | 0 |
| REFERENCE_PLUS_ALL_AND_POSTED_ON_OR_AFTER | 0 | 0 | 0 | 0 | 0 |

No embedding resolution or collision winner selection was performed. The maximum temporal window is **UNRESOLVED — REQUIRES POLICY FREEZE**; observed date lags are descriptive only.

## H. Temporal integrity audit

| Node type | Rows | Eligible | After cutoff | Missing availability | Metadata mismatch |
| --- | --- | --- | --- | --- | --- |
| VENDOR | 500 | 500 | 0 | 0 | 0 |
| VENDOR_CHANGE | 186 | 186 | 0 | 0 | 0 |
| PURCHASE_ORDER | 5000 | 5000 | 0 | 0 | 0 |
| PO_LINE | 11231 | 11231 | 0 | 0 | 0 |
| INVOICE | 8147 | 8147 | 0 | 0 | 0 |
| INVOICE_LINE | 18299 | 18299 | 0 | 0 | 0 |
| APPROVAL_EVENT | 17429 | 17429 | 0 | 0 | 0 |
| PAYMENT | 6200 | 6200 | 0 | 0 | 0 |
| PAYMENT_ALLOCATION | 7180 | 7180 | 0 | 0 | 0 |
| GL_ENTRY | 46755 | 46755 | 0 | 0 | 0 |
| BANK_TRANSACTION | 6261 | 6261 | 0 | 0 | 0 |
| BANK_STATEMENT | 54 | 54 | 0 | 0 | 0 |
| EMPLOYEE | 120 | 120 | 0 | 0 | 0 |
| AUDIT_EVENT | 28029 | 28029 | 0 | 0 | 0 |

Every proposed edge is separately checked under `eligible(source) AND eligible(target) AND eligible(provenance)`. A derived edge becomes available no earlier than the latest participating evidence. `due_date`, `expected_delivery_date`, and bank `transaction_date` were not substituted for the frozen availability fields.

## I. Leakage audit

Status: **PASS**. The audit scanned `310782` JSONL records, structured key paths, all serialized field headers, source artifact names, and practical semantic variants. It found `0` prohibited key/header hits and `0` prohibited content hits. No prohibited ground-truth file was opened to construct or run the scan.

## J. Hub-risk audit

Vendor and Employee nodes are retained but classified for restricted traversal: exact anchoring/direct attachment is allowed, while unconstrained reverse-neighborhood expansion is prohibited. `bank_account_id`, `gl_account`, `department`, `cost_center`, `currency`, `source_system`, dates, statuses, and `journal_id` remain context/filtering attributes and cannot become bridge nodes. Exact observed fan-out statistics are in `graph_hub_risk_audit.json`.

## K. Draft relation registry

| Relation | Source | Target | Tier | Traversable | Status |
| --- | --- | --- | --- | --- | --- |
| LINE_OF_PO | PO_LINE | PURCHASE_ORDER | TIER_A_EXACT | True | READY_FOR_FREEZE |
| INVOICE_REFERENCES_PO | INVOICE | PURCHASE_ORDER | TIER_A_EXACT | True | READY_FOR_FREEZE |
| INVOICE_LINE_REFERENCES_PO_LINE | INVOICE_LINE | PO_LINE | TIER_A_EXACT | True | READY_FOR_FREEZE |
| LINE_OF_INVOICE | INVOICE_LINE | INVOICE | TIER_A_EXACT | True | READY_FOR_FREEZE |
| APPROVAL_FOR_INVOICE | APPROVAL_EVENT | INVOICE | TIER_A_EXACT | True | READY_FOR_FREEZE |
| ALLOCATION_OF_PAYMENT | PAYMENT_ALLOCATION | PAYMENT | TIER_A_EXACT | True | READY_FOR_FREEZE |
| ALLOCATION_TO_INVOICE | PAYMENT_ALLOCATION | INVOICE | TIER_A_EXACT | True | READY_FOR_FREEZE |
| PAYMENT_ALLOCATED_TO_INVOICE | PAYMENT | INVOICE | TIER_A_EXPLICIT_PROVENANCE | True | READY_FOR_FREEZE |
| VENDOR_CHANGE_FOR_VENDOR | VENDOR_CHANGE | VENDOR | TIER_A_EXACT | False | READY_FOR_FREEZE |
| PO_FOR_VENDOR | PURCHASE_ORDER | VENDOR | TIER_A_EXACT | False | READY_FOR_FREEZE |
| INVOICE_FOR_VENDOR | INVOICE | VENDOR | TIER_A_EXACT | False | READY_FOR_FREEZE |
| PAYMENT_FOR_VENDOR | PAYMENT | VENDOR | TIER_A_EXACT | False | READY_FOR_FREEZE |
| APPROVAL_EVENT_APPROVER_EMPLOYEE | APPROVAL_EVENT | EMPLOYEE | TIER_A_EXACT_MATCHED_SUBSET | False | CONDITIONAL |
| AUDIT_EVENT_ACTOR_EMPLOYEE | AUDIT_EVENT | EMPLOYEE | TIER_A_EXACT_MATCHED_SUBSET | False | CONDITIONAL |
| PURCHASE_ORDER_CREATED_BY_EMPLOYEE | PURCHASE_ORDER | EMPLOYEE | TIER_A_EXACT_MATCHED_SUBSET | False | READY_FOR_FREEZE |
| VENDOR_CHANGE_CHANGED_BY_EMPLOYEE | VENDOR_CHANGE | EMPLOYEE | TIER_A_EXACT_MATCHED_SUBSET | False | READY_FOR_FREEZE |
| GL_SOURCE_BANK_TRANSACTION | GL_ENTRY | BANK_TRANSACTION | TIER_A_TYPED_EXACT | True | READY_FOR_FREEZE |
| GL_SOURCE_INVOICE | GL_ENTRY | INVOICE | TIER_A_TYPED_EXACT | True | READY_FOR_FREEZE |
| GL_SOURCE_PAYMENT | GL_ENTRY | PAYMENT | TIER_A_TYPED_EXACT | True | READY_FOR_FREEZE |
| AUDIT_EVENT_FOR_BANK_TRANSACTION | AUDIT_EVENT | BANK_TRANSACTION | TIER_A_TYPED_EXACT | True | READY_FOR_FREEZE |
| AUDIT_EVENT_FOR_INVOICE | AUDIT_EVENT | INVOICE | TIER_A_TYPED_EXACT | True | READY_FOR_FREEZE |
| AUDIT_EVENT_FOR_PAYMENT | AUDIT_EVENT | PAYMENT | TIER_A_TYPED_EXACT | True | READY_FOR_FREEZE |
| AUDIT_EVENT_FOR_PURCHASE_ORDER | AUDIT_EVENT | PURCHASE_ORDER | TIER_A_TYPED_EXACT | True | READY_FOR_FREEZE |
| AUDIT_EVENT_FOR_VENDOR | AUDIT_EVENT | VENDOR | TIER_A_TYPED_EXACT | False | READY_FOR_FREEZE |
| PAYMENT_CANDIDATE_BANK_TRANSACTION | PAYMENT | BANK_TRANSACTION | TIER_B_CANDIDATE | False | UNRESOLVED |

Only `READY_FOR_FREEZE` relations are recommended for the frozen core. `CONDITIONAL`, `UNRESOLVED`, and `REJECTED` designs remain non-traversable until a separately approved policy change.

## L. Proposed path motifs

| Motif | Edge sequence | Tier B allowed | Priority | Status |
| --- | --- | --- | --- | --- |
| PO_WITH_INVOICES | INVOICE_REFERENCES_PO:reverse | False | 1 | READY_FOR_FREEZE |
| PO_WITH_LINES | LINE_OF_PO:reverse | False | 1 | READY_FOR_FREEZE |
| PO_INVOICE_LINES | INVOICE_REFERENCES_PO:reverse → LINE_OF_INVOICE:reverse | False | 2 | READY_FOR_FREEZE |
| INVOICE_PAYMENTS | PAYMENT_ALLOCATED_TO_INVOICE:reverse | False | 1 | READY_FOR_FREEZE |
| INVOICE_APPROVALS | APPROVAL_FOR_INVOICE:reverse | False | 1 | READY_FOR_FREEZE |
| INVOICE_AUDIT_EVENTS | AUDIT_EVENT_FOR_INVOICE:reverse | False | 1 | READY_FOR_FREEZE |
| PAYMENT_GL_ENTRIES | GL_SOURCE_PAYMENT:reverse | False | 1 | READY_FOR_FREEZE |
| GL_ENTRY_SOURCE_TRANSACTION | GL_SOURCE_{INVOICE\|PAYMENT\|BANK_TRANSACTION}:forward | False | 1 | READY_FOR_FREEZE |
| INVOICE_PAYMENT_BANK | PAYMENT_ALLOCATED_TO_INVOICE:reverse → PAYMENT_CANDIDATE_BANK_TRANSACTION:forward | True | 2 | UNRESOLVED |
| GL_PAYMENT_BANK | GL_SOURCE_PAYMENT:forward → PAYMENT_CANDIDATE_BANK_TRANSACTION:forward | True | 2 | UNRESOLVED |

Unrestricted BFS is prohibited. Every motif is label-independent, cutoff-gated, provenance-preserving, hub-restricted, and subject to the existing maximum of 40 raw source records.

### Deterministic ranking policy draft

The proposed order is: exact anchor; direct Tier A; complete Tier A multi-hop paths; deterministic joins; frozen Tier B corroborated candidates; audit/event context; then targeted semantic fallback only for unresolved gaps. Ties resolve by tier, hop count, registry order, and ascending canonical `record_id`. No reranker is trained and no weight is optimized on held-out labels. The exact token cap remains a human freeze item.

## M. Unresolved questions

- PAYMENT↔BANK_TRANSACTION: exact bank-account namespaces do not receive any inferred crosswalk; a maximum temporal window is UNRESOLVED — REQUIRES POLICY FREEZE. The edge remains excluded from traversal.
- AUDIT_EVENT entity_type=gl_journal: entity_id addresses journal_id grouping values, not canonical GL_ENTRY IDs. No GL_JOURNAL node is allowed; traversal remains unresolved/excluded.
- APPROVAL_EVENT.approver_id and AUDIT_EVENT.actor_id include non-Employee system/shared-role actors. Exact Employee matches can be conditional edges; unmatched actor strings remain context.
- The exact GraphRAG token cap comparable with Standard RAG and per-motif multiplicity behavior require human policy freeze; the raw-source cap remains 40.
- Vendor and Employee reverse-expansion restrictions require explicit reviewer acceptance before implementation.

## N. Recommended freeze decision

Recommended scope: freeze only the deterministic `READY_FOR_FREEZE` node/relation/motif core. Keep every conditional or unresolved item explicitly excluded from traversal, especially payment-bank candidates and `gl_journal` grouping references. This recommendation does not authorize GraphRAG implementation.

No blocking condition was found for freezing the deterministic READY_FOR_FREEZE core. CONDITIONAL and UNRESOLVED relations must remain excluded from traversal.

RECOMMEND 7/7 GO FOR GRAPH RAG REGISTRY FREEZE
