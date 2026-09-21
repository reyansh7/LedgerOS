# Graph v1.1 Typed Financial Traversal Grammar — Registry Freeze Review

Freeze status: `FROZEN_GRAPH_V1_1_TYPED_GRAMMAR`

This is an internal research-readiness freeze of registry/specification artifacts. It does not implement or evaluate a Graph v1.1 retriever.

## A. Executive decision

Freeze the verified Phase 6A.2 typed grammar as immutable Graph v1.1 specification artifacts. All parent hashes, 30 transition validations, zero semantic-drift checks, topology equivalence, 76/76 structural sequence coverage, hub controls, scientific-integrity controls, and double-build hashes pass.

This decision authorizes only a later implementation review. No retriever, ranking engine, evidence selector, retrieval evaluation, LLM workflow, or Phase 6B activity is authorized here.

## B. Parent artifact verification

The freeze gate independently passed **51 raw-byte checks over 38 distinct parent paths**. Checks include prompt-pinned Phase 6A.2 artifacts, all inventory-listed Phase 6A.2 extras, the complete Phase 6A.1 inventory, five Graph v1.0 registry parents, and the persisted graph nodes/edges. No failed check was normalized, repaired, or regenerated.

| Parent | Expected SHA-256 | Observed SHA-256 | Result |
| --- | --- | --- | --- |
| results/graphrag/phase6a1_motif_diagnostic_v1/PHASE6A1_MOTIF_DIAGNOSTIC_REVIEW.md | 4b32dee5614982ffab50d458e9ee876b98f8a4fa70de25b8d8e76aab4233fec6 | 4b32dee5614982ffab50d458e9ee876b98f8a4fa70de25b8d8e76aab4233fec6 | PASS |
| results/graphrag/phase6a1_motif_diagnostic_v1/phase6a1_artifact_hashes.json | d2c70d76e72fbe16a9210f191facbf8eeaecdd97bbd39c009b036cc4d332d7b5 | d2c70d76e72fbe16a9210f191facbf8eeaecdd97bbd39c009b036cc4d332d7b5 | PASS |
| results/graphrag/phase6a2_typed_grammar_design_v1_1/PHASE6A2_TYPED_GRAMMAR_DESIGN_REVIEW.md | 9ab2abbdacde0b912ec36aede2da22e2ca51b48d0e7e51ea37699e1ce3afbd61 | 9ab2abbdacde0b912ec36aede2da22e2ca51b48d0e7e51ea37699e1ce3afbd61 | PASS |
| results/graphrag/phase6a2_typed_grammar_design_v1_1/forbidden_traversals_v1_1_draft.json | 2b3d0a604df5c5a75121749ccdfa15269c6ea98632f31398085f7c7153d04b74 | 2b3d0a604df5c5a75121749ccdfa15269c6ea98632f31398085f7c7153d04b74 | PASS |
| results/graphrag/phase6a2_typed_grammar_design_v1_1/grammar_fanout_analysis.json | 12e00af5447d9e4fd3db686c95d3d1fb562c48b03dac67de116a1ebd744c5e25 | 12e00af5447d9e4fd3db686c95d3d1fb562c48b03dac67de116a1ebd744c5e25 | PASS |
| results/graphrag/phase6a2_typed_grammar_design_v1_1/grammar_risk_register.json | 34946386c9f424e89c8821ed7fbcb653e04406df13ae0e9fcf68594366833a09 | 34946386c9f424e89c8821ed7fbcb653e04406df13ae0e9fcf68594366833a09 | PASS |
| results/graphrag/phase6a2_typed_grammar_design_v1_1/grammar_structural_coverage.json | 7a2a659b3a5633987b74074fa4c477eb3b7fa1b80a14b20ecb13f4c6f65b8c63 | 7a2a659b3a5633987b74074fa4c477eb3b7fa1b80a14b20ecb13f4c6f65b8c63 | PASS |
| results/graphrag/phase6a2_typed_grammar_design_v1_1/grammar_topology_simulation.json | 63df67774453723df7975b3f8afc2626846583fc3c9dbe82670ced4b1a875696 | 63df67774453723df7975b3f8afc2626846583fc3c9dbe82670ced4b1a875696 | PASS |
| results/graphrag/phase6a2_typed_grammar_design_v1_1/grammar_transition_justifications.json | 5478138031bb3f3cba7ff3138434f4706b3127722d5f2e3d2969f4afec007508 | 5478138031bb3f3cba7ff3138434f4706b3127722d5f2e3d2969f4afec007508 | PASS |
| results/graphrag/phase6a2_typed_grammar_design_v1_1/graph_traversal_grammar_v1_1_draft.json | 007f4ba9eed7c9d00bd5bcab7a6d1752c0fe924614a6cf36f728a41ec14fc0d8 | 007f4ba9eed7c9d00bd5bcab7a6d1752c0fe924614a6cf36f728a41ec14fc0d8 | PASS |
| results/graphrag/phase6a2_typed_grammar_design_v1_1/node_type_traversal_matrix_v1_1_draft.json | f04f01b8106d4e0a59c9d0d3e53dea0f625c1ba3c64465afbc9a9678b09d5d12 | f04f01b8106d4e0a59c9d0d3e53dea0f625c1ba3c64465afbc9a9678b09d5d12 | PASS |
| results/graphrag/phase6a2_typed_grammar_design_v1_1/phase6a2_artifact_hashes.json | db5cdc9f153617a97e1bab845e7e2609fc249514e80e528ecd6ba1c46b93aa39 | db5cdc9f153617a97e1bab845e7e2609fc249514e80e528ecd6ba1c46b93aa39 | PASS |
| results/graphrag/phase6a2_typed_grammar_design_v1_1/scientific_integrity.json | e150be4d9b754303569d5dc85f6c8c552969645cb033d762bfa83ac75aa990ea | e150be4d9b754303569d5dc85f6c8c552969645cb033d762bfa83ac75aa990ea | PASS |
| results/graphrag/phase6a2_typed_grammar_design_v1_1/typed_transition_matrix_v1_1_draft.json | 8a0c2e6d24b5098c9ffdef4da17c33979386a92f365161273349d2a906a2b36c | 8a0c2e6d24b5098c9ffdef4da17c33979386a92f365161273349d2a906a2b36c | PASS |
| results/graphrag/phase6a2_typed_grammar_design_v1_1/v1_motif_to_v1_1_grammar_mapping.json | 2eb77bda03a01cb3923b3c6a3ec40212c34043695480472d3060c9536b0b3102 | 2eb77bda03a01cb3923b3c6a3ec40212c34043695480472d3060c9536b0b3102 | PASS |
| results/graphrag/phase6a_graph_retrieval_v1_0/graph/edges.jsonl | ee364fa677abeda3b25119d5c3c2f1aea5bc8902a28e7f7ecefcddd38a77d9ed | ee364fa677abeda3b25119d5c3c2f1aea5bc8902a28e7f7ecefcddd38a77d9ed | PASS |
| results/graphrag/phase6a_graph_retrieval_v1_0/graph/nodes.jsonl | 87f80fa5e91675b192dd051598a9197c0703650f4daf09c2a7619c031295a167 | 87f80fa5e91675b192dd051598a9197c0703650f4daf09c2a7619c031295a167 | PASS |
| results/graphrag/registry_freeze_v1/graph_freeze_manifest_v1.json | 8097eb64accec2c076d07ed9ae4604d2202d1ca83578cf8557b40f034b7cad76 | 8097eb64accec2c076d07ed9ae4604d2202d1ca83578cf8557b40f034b7cad76 | PASS |
| results/graphrag/registry_freeze_v1/graph_node_registry_v1.json | 4c17ff5c863ed446418fbc2b3b407704519862feddc5f0c81546c210f8e91d10 | 4c17ff5c863ed446418fbc2b3b407704519862feddc5f0c81546c210f8e91d10 | PASS |
| results/graphrag/registry_freeze_v1/graph_path_motifs_v1.json | 36dd0b0d491dd6ef5f46c1dcd38cfe5e9e2ab61c632038b89cdc6ed9e0ec58ef | 36dd0b0d491dd6ef5f46c1dcd38cfe5e9e2ab61c632038b89cdc6ed9e0ec58ef | PASS |
| results/graphrag/registry_freeze_v1/graph_ranking_policy_v1.json | 85a167767f6147c2a51db9cdab47d7157731bb2126ca2cf2c452f4e9bde602f0 | 85a167767f6147c2a51db9cdab47d7157731bb2126ca2cf2c452f4e9bde602f0 | PASS |
| results/graphrag/registry_freeze_v1/graph_relation_registry_v1.json | f8c61e2117c09921d001c4d476ef80d138f362c2ac084850544fc56077a7b0c3 | f8c61e2117c09921d001c4d476ef80d138f362c2ac084850544fc56077a7b0c3 | PASS |

## C. Graph v1.0 lineage

Graph v1.0 remains immutable and independently reconstructible. Its node, relation, motif, ranking, and freeze-manifest hashes match. The persisted graph remains 155,391 nodes across 14 types and 184,223 edges across 22 frozen relation types. Graph v1.1 creates and deletes zero graph edges.

## D. Phase 6A.1 diagnostic lineage

The Phase 6A.1 report and complete hash inventory match their pinned digests. The v1.1 freeze preserves the diagnostic conclusion that the v1.0 multi-hop failure arose from fixed-motif execution constraints, not missing deterministic graph structure. Phase 6A.1 was neither rerun nor modified.

## E. Phase 6A.2 design lineage

Every required Phase 6A.2 proposal artifact and inventory-listed extra matches exactly. Phase 6A.2 references the same Graph v1.0, Phase 6A graph, and Phase 6A.1 lineage verified here. Promotion changes only version/status/filename, serialization, and freeze-validation metadata.

## F. Draft-to-final semantic diff

Machine-readable comparison reports **SEMANTIC_TRANSITION_DIFF_COUNT = 0** and global semantic diff count 0. Transition IDs, node types, relation IDs, directions, classes, hop permissions, continuation and terminal behavior, hub/multiplicity/cycle rules, provenance, temporal rules, node policies, relation dispositions, and forbidden definitions are unchanged.

| Transition | Semantic changes | Result |
| --- | --- | --- |
| TR_APPROVAL_EVENT__APPROVAL_FOR_INVOICE__FORWARD__INVOICE | 0 | PASS |
| TR_AUDIT_EVENT__AUDIT_EVENT_FOR_BANK_TRANSACTION__FORWARD__BANK_TRANSACTION | 0 | PASS |
| TR_AUDIT_EVENT__AUDIT_EVENT_FOR_INVOICE__FORWARD__INVOICE | 0 | PASS |
| TR_AUDIT_EVENT__AUDIT_EVENT_FOR_PAYMENT__FORWARD__PAYMENT | 0 | PASS |
| TR_AUDIT_EVENT__AUDIT_EVENT_FOR_PURCHASE_ORDER__FORWARD__PURCHASE_ORDER | 0 | PASS |
| TR_BANK_TRANSACTION__AUDIT_EVENT_FOR_BANK_TRANSACTION__REVERSE__AUDIT_EVENT | 0 | PASS |
| TR_BANK_TRANSACTION__GL_SOURCE_BANK_TRANSACTION__REVERSE__GL_ENTRY | 0 | PASS |
| TR_GL_ENTRY__GL_SOURCE_BANK_TRANSACTION__FORWARD__BANK_TRANSACTION | 0 | PASS |
| TR_GL_ENTRY__GL_SOURCE_INVOICE__FORWARD__INVOICE | 0 | PASS |
| TR_GL_ENTRY__GL_SOURCE_PAYMENT__FORWARD__PAYMENT | 0 | PASS |
| TR_INVOICE_LINE__INVOICE_LINE_REFERENCES_PO_LINE__FORWARD__PO_LINE | 0 | PASS |
| TR_INVOICE_LINE__LINE_OF_INVOICE__FORWARD__INVOICE | 0 | PASS |
| TR_INVOICE__ALLOCATION_TO_INVOICE__REVERSE__PAYMENT_ALLOCATION | 0 | PASS |
| TR_INVOICE__APPROVAL_FOR_INVOICE__REVERSE__APPROVAL_EVENT | 0 | PASS |
| TR_INVOICE__AUDIT_EVENT_FOR_INVOICE__REVERSE__AUDIT_EVENT | 0 | PASS |
| TR_INVOICE__GL_SOURCE_INVOICE__REVERSE__GL_ENTRY | 0 | PASS |
| TR_INVOICE__INVOICE_REFERENCES_PO__FORWARD__PURCHASE_ORDER | 0 | PASS |
| TR_INVOICE__LINE_OF_INVOICE__REVERSE__INVOICE_LINE | 0 | PASS |
| TR_INVOICE__PAYMENT_ALLOCATED_TO_INVOICE__REVERSE__PAYMENT | 0 | PASS |
| TR_PAYMENT_ALLOCATION__ALLOCATION_OF_PAYMENT__FORWARD__PAYMENT | 0 | PASS |
| TR_PAYMENT_ALLOCATION__ALLOCATION_TO_INVOICE__FORWARD__INVOICE | 0 | PASS |
| TR_PAYMENT__ALLOCATION_OF_PAYMENT__REVERSE__PAYMENT_ALLOCATION | 0 | PASS |
| TR_PAYMENT__AUDIT_EVENT_FOR_PAYMENT__REVERSE__AUDIT_EVENT | 0 | PASS |
| TR_PAYMENT__GL_SOURCE_PAYMENT__REVERSE__GL_ENTRY | 0 | PASS |
| TR_PAYMENT__PAYMENT_ALLOCATED_TO_INVOICE__FORWARD__INVOICE | 0 | PASS |
| TR_PO_LINE__INVOICE_LINE_REFERENCES_PO_LINE__REVERSE__INVOICE_LINE | 0 | PASS |
| TR_PO_LINE__LINE_OF_PO__FORWARD__PURCHASE_ORDER | 0 | PASS |
| TR_PURCHASE_ORDER__AUDIT_EVENT_FOR_PURCHASE_ORDER__REVERSE__AUDIT_EVENT | 0 | PASS |
| TR_PURCHASE_ORDER__INVOICE_REFERENCES_PO__REVERSE__INVOICE | 0 | PASS |
| TR_PURCHASE_ORDER__LINE_OF_PO__REVERSE__PO_LINE | 0 | PASS |

Allowed freeze-normalization differences are artifact version, frozen status, canonical filename, deterministic serialization metadata, fixed timestamp, and label-independent freeze-validation attestations.

## G. Transition inventory

All **30** transitions passed checks A–L. No new relation, edge, or node type was introduced.

| Transition ID | Class | Frozen relation | Direction | Current type | Next type | Accepted-route usage | Freeze validation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TR_APPROVAL_EVENT__APPROVAL_FOR_INVOICE__FORWARD__INVOICE | CONTEXT | APPROVAL_FOR_INVOICE | FORWARD | APPROVAL_EVENT | INVOICE | 0 | PASS |
| TR_AUDIT_EVENT__AUDIT_EVENT_FOR_BANK_TRANSACTION__FORWARD__BANK_TRANSACTION | CONTEXT | AUDIT_EVENT_FOR_BANK_TRANSACTION | FORWARD | AUDIT_EVENT | BANK_TRANSACTION | 0 | PASS |
| TR_AUDIT_EVENT__AUDIT_EVENT_FOR_INVOICE__FORWARD__INVOICE | CONTEXT | AUDIT_EVENT_FOR_INVOICE | FORWARD | AUDIT_EVENT | INVOICE | 0 | PASS |
| TR_AUDIT_EVENT__AUDIT_EVENT_FOR_PAYMENT__FORWARD__PAYMENT | CONTEXT | AUDIT_EVENT_FOR_PAYMENT | FORWARD | AUDIT_EVENT | PAYMENT | 0 | PASS |
| TR_AUDIT_EVENT__AUDIT_EVENT_FOR_PURCHASE_ORDER__FORWARD__PURCHASE_ORDER | CONTEXT | AUDIT_EVENT_FOR_PURCHASE_ORDER | FORWARD | AUDIT_EVENT | PURCHASE_ORDER | 0 | PASS |
| TR_BANK_TRANSACTION__AUDIT_EVENT_FOR_BANK_TRANSACTION__REVERSE__AUDIT_EVENT | TERMINAL_CONTEXT | AUDIT_EVENT_FOR_BANK_TRANSACTION | REVERSE | BANK_TRANSACTION | AUDIT_EVENT | 22 | PASS |
| TR_BANK_TRANSACTION__GL_SOURCE_BANK_TRANSACTION__REVERSE__GL_ENTRY | BACKBONE | GL_SOURCE_BANK_TRANSACTION | REVERSE | BANK_TRANSACTION | GL_ENTRY | 8 | PASS |
| TR_GL_ENTRY__GL_SOURCE_BANK_TRANSACTION__FORWARD__BANK_TRANSACTION | BACKBONE | GL_SOURCE_BANK_TRANSACTION | FORWARD | GL_ENTRY | BANK_TRANSACTION | 0 | PASS |
| TR_GL_ENTRY__GL_SOURCE_INVOICE__FORWARD__INVOICE | BACKBONE | GL_SOURCE_INVOICE | FORWARD | GL_ENTRY | INVOICE | 0 | PASS |
| TR_GL_ENTRY__GL_SOURCE_PAYMENT__FORWARD__PAYMENT | BACKBONE | GL_SOURCE_PAYMENT | FORWARD | GL_ENTRY | PAYMENT | 650 | PASS |
| TR_INVOICE_LINE__INVOICE_LINE_REFERENCES_PO_LINE__FORWARD__PO_LINE | BACKBONE | INVOICE_LINE_REFERENCES_PO_LINE | FORWARD | INVOICE_LINE | PO_LINE | 1036 | PASS |
| TR_INVOICE_LINE__LINE_OF_INVOICE__FORWARD__INVOICE | BACKBONE | LINE_OF_INVOICE | FORWARD | INVOICE_LINE | INVOICE | 0 | PASS |
| TR_INVOICE__ALLOCATION_TO_INVOICE__REVERSE__PAYMENT_ALLOCATION | BACKBONE | ALLOCATION_TO_INVOICE | REVERSE | INVOICE | PAYMENT_ALLOCATION | 863 | PASS |
| TR_INVOICE__APPROVAL_FOR_INVOICE__REVERSE__APPROVAL_EVENT | TERMINAL_CONTEXT | APPROVAL_FOR_INVOICE | REVERSE | INVOICE | APPROVAL_EVENT | 1442 | PASS |
| TR_INVOICE__AUDIT_EVENT_FOR_INVOICE__REVERSE__AUDIT_EVENT | TERMINAL_CONTEXT | AUDIT_EVENT_FOR_INVOICE | REVERSE | INVOICE | AUDIT_EVENT | 1378 | PASS |
| TR_INVOICE__GL_SOURCE_INVOICE__REVERSE__GL_ENTRY | BACKBONE | GL_SOURCE_INVOICE | REVERSE | INVOICE | GL_ENTRY | 2964 | PASS |
| TR_INVOICE__INVOICE_REFERENCES_PO__FORWARD__PURCHASE_ORDER | BACKBONE | INVOICE_REFERENCES_PO | FORWARD | INVOICE | PURCHASE_ORDER | 1974 | PASS |
| TR_INVOICE__LINE_OF_INVOICE__REVERSE__INVOICE_LINE | BACKBONE | LINE_OF_INVOICE | REVERSE | INVOICE | INVOICE_LINE | 2700 | PASS |
| TR_INVOICE__PAYMENT_ALLOCATED_TO_INVOICE__REVERSE__PAYMENT | SUPPORTING | PAYMENT_ALLOCATED_TO_INVOICE | REVERSE | INVOICE | PAYMENT | 913 | PASS |
| TR_PAYMENT_ALLOCATION__ALLOCATION_OF_PAYMENT__FORWARD__PAYMENT | BACKBONE | ALLOCATION_OF_PAYMENT | FORWARD | PAYMENT_ALLOCATION | PAYMENT | 408 | PASS |
| TR_PAYMENT_ALLOCATION__ALLOCATION_TO_INVOICE__FORWARD__INVOICE | BACKBONE | ALLOCATION_TO_INVOICE | FORWARD | PAYMENT_ALLOCATION | INVOICE | 2908 | PASS |
| TR_PAYMENT__ALLOCATION_OF_PAYMENT__REVERSE__PAYMENT_ALLOCATION | BACKBONE | ALLOCATION_OF_PAYMENT | REVERSE | PAYMENT | PAYMENT_ALLOCATION | 3329 | PASS |
| TR_PAYMENT__AUDIT_EVENT_FOR_PAYMENT__REVERSE__AUDIT_EVENT | TERMINAL_CONTEXT | AUDIT_EVENT_FOR_PAYMENT | REVERSE | PAYMENT | AUDIT_EVENT | 454 | PASS |
| TR_PAYMENT__GL_SOURCE_PAYMENT__REVERSE__GL_ENTRY | BACKBONE | GL_SOURCE_PAYMENT | REVERSE | PAYMENT | GL_ENTRY | 844 | PASS |
| TR_PAYMENT__PAYMENT_ALLOCATED_TO_INVOICE__FORWARD__INVOICE | SUPPORTING | PAYMENT_ALLOCATED_TO_INVOICE | FORWARD | PAYMENT | INVOICE | 4808 | PASS |
| TR_PO_LINE__INVOICE_LINE_REFERENCES_PO_LINE__REVERSE__INVOICE_LINE | BACKBONE | INVOICE_LINE_REFERENCES_PO_LINE | REVERSE | PO_LINE | INVOICE_LINE | 415 | PASS |
| TR_PO_LINE__LINE_OF_PO__FORWARD__PURCHASE_ORDER | BACKBONE | LINE_OF_PO | FORWARD | PO_LINE | PURCHASE_ORDER | 329 | PASS |
| TR_PURCHASE_ORDER__AUDIT_EVENT_FOR_PURCHASE_ORDER__REVERSE__AUDIT_EVENT | TERMINAL_CONTEXT | AUDIT_EVENT_FOR_PURCHASE_ORDER | REVERSE | PURCHASE_ORDER | AUDIT_EVENT | 278 | PASS |
| TR_PURCHASE_ORDER__INVOICE_REFERENCES_PO__REVERSE__INVOICE | BACKBONE | INVOICE_REFERENCES_PO | REVERSE | PURCHASE_ORDER | INVOICE | 212 | PASS |
| TR_PURCHASE_ORDER__LINE_OF_PO__REVERSE__PO_LINE | BACKBONE | LINE_OF_PO | REVERSE | PURCHASE_ORDER | PO_LINE | 1036 | PASS |

## H. Transition-class counts

| Class | Frozen transition count |
| --- | --- |
| BACKBONE | 18 |
| SUPPORTING | 2 |
| CONTEXT | 5 |
| TERMINAL_CONTEXT | 5 |

The class assignment of every transition is byte-derived from the approved proposal and was not reinterpreted during freeze.

## I. Frozen relation types used

The grammar uses **15** of the 22 existing Graph v1.0 relation types:

- `ALLOCATION_OF_PAYMENT`
- `ALLOCATION_TO_INVOICE`
- `APPROVAL_FOR_INVOICE`
- `AUDIT_EVENT_FOR_BANK_TRANSACTION`
- `AUDIT_EVENT_FOR_INVOICE`
- `AUDIT_EVENT_FOR_PAYMENT`
- `AUDIT_EVENT_FOR_PURCHASE_ORDER`
- `GL_SOURCE_BANK_TRANSACTION`
- `GL_SOURCE_INVOICE`
- `GL_SOURCE_PAYMENT`
- `INVOICE_LINE_REFERENCES_PO_LINE`
- `INVOICE_REFERENCES_PO`
- `LINE_OF_INVOICE`
- `LINE_OF_PO`
- `PAYMENT_ALLOCATED_TO_INVOICE`

New relation type count: **0**.

## J. Backbone traversal policy

The 18 BACKBONE rows compose exact purchase, invoice, line, allocation, payment, and typed GL-source relationships. Conceptual lifecycle proximity never creates a direct edge: each hop must match its named frozen relation and exact persisted edge.

## K. Context/terminal-context policy

Five CONTEXT rows are exact event-anchor exits permitted only at hop 1. Five TERMINAL_CONTEXT rows collect entity-local approval/audit evidence and stop. A reached GL_ENTRY is also a terminal accounting consequence. Context cannot route through Employee, Vendor, actor identity, or another event neighborhood.

## L. Payment-allocation policy

The explicit `INVOICE ↔ PAYMENT_ALLOCATION ↔ PAYMENT` model remains the provenance-complete backbone. The already-frozen direct Payment↔Invoice projection remains SUPPORTING only with its exact PAYMENT_ALLOCATION provenance. No synthesized payment relation is introduced; multiplicity and all supporting path IDs remain preservable.

## M. GL source-transaction policy

GL traversal is restricted to the three frozen typed `GL_SOURCE_*` families and requires exact `source_transaction_id`, frozen transaction-type mapping, source/target type agreement, endpoint eligibility, edge provenance, and cutoff compliance. No fuzzy source matching, GL similarity, account bridge, or synthetic journal is permitted.

## N. GL fan-out governance

The maximum proposed direction remains `TR_INVOICE__GL_SOURCE_INVOICE__REVERSE__GL_ENTRY` with mean 4.168037, median 4, p95 6, p99 7, and maximum 8. Research policy is **enumerate all exact eligible deterministic edges with no arbitrary transition-local cap**. Cap status remains `NOT_FROZEN / NO_RESEARCH_TRUNCATION`; production drift/cap governance remains unresolved.

## O. Vendor/Employee hub controls

Both orientations of seven restricted Vendor/Employee relation families remain excluded: 14 directions, zero promotions. The equivalent topology run observed 1,694 prohibited frontier incidences and accepted **zero Vendor/Employee entries**. `AUDIT_EVENT_FOR_VENDOR` remains excluded even though locally bounded because frozen Vendor policy is authoritative.

## P. Bank settlement relation gap

`PAYMENT ↔ BANK_TRANSACTION` remains disabled. `BANK_SETTLEMENT_LINKAGE_STATUS = RELATION_GAP / SEPARATE FUTURE TIER_B RESEARCH`. Amount, currency, date, account, reference, text, embedding, and heuristic-window matching are prohibited.

## Q. BankStatement relation gap

No frozen BankStatement-to-transaction membership/reconciliation relation exists. `BANK_STATEMENT` retains an explicit empty transition set. No relationship is introduced during freeze; this remains an excluded/unresolved future capability not required by v1.1.

## R. Forbidden traversal registry

The immutable registry preserves all 21 draft prohibitions and 14 excluded frozen directions. It is default-deny: an existing graph edge is not traversable without an exact grammar row.

- `FT_ALLOCATION_BYPASS` — Invented Invoice <-> Payment edge without a PAYMENT_ALLOCATION provenance record
- `FT_AMBIGUOUS_OR_INFERRED_JOIN` — Fuzzy ID, cross-type fallback, nearest neighbor, collision winner, or inferred relation
- `FT_ATTRIBUTE_BRIDGE` — Traversal through department, cost_center, source_system, status, or any other non-node dimension
- `FT_CONTEXT_BRIDGE` — Continue from APPROVAL_EVENT or AUDIT_EVENT reached after hop 0
- `FT_DEFAULT_DENY_BFS` — Any graph edge without an exact current-type/relation/direction/next-type grammar row
- `FT_DEPTH_GT_3` — Any fourth or later graph edge
- `FT_EMPLOYEE_BRIDGE` — Any * -> EMPLOYEE -> * path, including actor/approver coercion
- `FT_GL_TYPE_MISMATCH` — GL traversal without exact source_transaction_id and frozen transaction_type target mapping
- `FT_MULTIPLICITY_COLLAPSE` — Silently select one neighbor or treat M:N/N:1 as 1:1
- `FT_PAYMENT_BANK` — PAYMENT <-> BANK_TRANSACTION
- `FT_POST_CUTOFF` — Traverse when source, target, edge, or provenance-effective availability exceeds cutoff
- `FT_PROVENANCE_MISSING` — Traverse an edge without retainable source fields, target fields, edge ID, and provenance record
- `FT_REACHED_GL_CONTINUATION` — Continue from GL_ENTRY reached from BANK_TRANSACTION, INVOICE, or PAYMENT
- `FT_REPEATED_RECORD` — Any candidate path in which a record_id repeats
- `FT_SAME_ACCOUNT` — Traversal based only on bank_account_id or gl_account
- `FT_SAME_AMOUNT` — Traversal based only on equal amount
- `FT_SAME_CURRENCY` — Traversal based only on equal currency
- `FT_SAME_DATE` — Traversal based only on equal date or a date window
- `FT_SEMANTIC_SIMILARITY` — Embedding, text similarity, semantic neighbor, failure-class, or RCA-concept expansion
- `FT_SYNTHETIC_GL_JOURNAL` — GL_JOURNAL node, journal_id bridge/group traversal, or AUDIT_EVENT -> GL_JOURNAL
- `FT_VENDOR_BRIDGE` — Any * -> VENDOR -> * cross-transaction path

## S. Depth and cycle policies

`MAX_PATH_DEPTH = 3`; depth 1, 2, and 3 remain separately identifiable. Paths are record-ID-simple. The equivalent run rejected 4,018 repeated-record expansions and stopped 4,415 terminal event/GL returns earlier, reconciling to 8,433. No additional cycle behavior is introduced.

## T. Multiplicity behavior

Every exact eligible neighbor is enumerated deterministically; one-to-many and many-to-many facts are not collapsed. No arbitrary transition cap exists. The future `MAX_RAW_SOURCE_RECORDS = 40` selection budget applies after traversal and does not limit candidate paths or alter relation cardinality.

## U. Provenance guarantees

Every transition retains transition ID/class, relation ID/direction, current and next node types, stored/current/next operational fields, edge ID, provenance record ID/type/fields, anchor and node sequence, temporal result, path depth, and path-class sequence. All 30 provenance validations pass.

## V. Temporal guarantees

The authoritative cutoff remains **2026-06-30**. Every hop requires cutoff eligibility for both endpoints, the persisted edge, and provenance-effective availability. A grammar row cannot override temporal eligibility; the equivalence run recorded zero type/provenance/temporal violations.

## W. Structural sequence coverage

STRUCTURAL_SEQUENCE_COVERAGE remains **76/76 = 100.0%**: depth 1 is 14/14, depth 2 is 21/21, and depth 3 is 41/41. This is typed-sequence representability, not required-document recall, evidence precision, full-evidence coverage, RCA accuracy, or LLM performance.

## X. Topology-equivalence validation

The final frozen specification reproduces the proposal topology exactly: 416 route cases, 430 roots, 13,371 accepted prefixes, and depth counts 3,332/4,477/5,562. Paths per case are p50 31, p75 44, p90 62, p95 68, p99 78, max 91. Unique records including anchors are p50 20, p95 38, p99 43, max 50. Candidate path digest: `89d7f799f60149a8e6665bf59a484131f450ec2ab435e9a891e1eec3efbb2944`.

No retrieval metric or gold evidence was calculated.

## Y. Eight validation-unused transitions

**Absence from the validation routing mix is not evidence that an operationally valid transition should be removed.** The eight rows below have zero accepted-path usage in that routing mix but pass all frozen-relation, type, direction, provenance, temporal, fan-out, hub, label-independence, and no-new-fact checks.

| Transition ID | Relation | Source/current | Target/next | Direction | Class | Route usage | Global support | Fan-out | Operational justification | Reason retained/excluded | Gold used? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TR_APPROVAL_EVENT__APPROVAL_FOR_INVOICE__FORWARD__INVOICE | APPROVAL_FOR_INVOICE | APPROVAL_EVENT | INVOICE | FORWARD | CONTEXT | 0 | 17429 exact edges | mean 1.000000; med 1; p95 1; p99 1; max 1 | An approval event records local approval context for exactly one invoice through invoice_id. | RETAINED — exact frozen relation; validation frequency is not correctness | false |
| TR_AUDIT_EVENT__AUDIT_EVENT_FOR_BANK_TRANSACTION__FORWARD__BANK_TRANSACTION | AUDIT_EVENT_FOR_BANK_TRANSACTION | AUDIT_EVENT | BANK_TRANSACTION | FORWARD | CONTEXT | 0 | 247 exact edges | mean 0.008812; med 0; p95 0; p99 0; max 1 | A typed audit event's entity_id exactly identifies one bank transaction. | RETAINED — exact frozen relation; validation frequency is not correctness | false |
| TR_AUDIT_EVENT__AUDIT_EVENT_FOR_INVOICE__FORWARD__INVOICE | AUDIT_EVENT_FOR_INVOICE | AUDIT_EVENT | INVOICE | FORWARD | CONTEXT | 0 | 16147 exact edges | mean 0.576082; med 1; p95 1; p99 1; max 1 | A typed audit event's entity_id exactly identifies one invoice. | RETAINED — exact frozen relation; validation frequency is not correctness | false |
| TR_AUDIT_EVENT__AUDIT_EVENT_FOR_PAYMENT__FORWARD__PAYMENT | AUDIT_EVENT_FOR_PAYMENT | AUDIT_EVENT | PAYMENT | FORWARD | CONTEXT | 0 | 6500 exact edges | mean 0.231903; med 0; p95 1; p99 1; max 1 | A typed audit event's entity_id exactly identifies one payment. | RETAINED — exact frozen relation; validation frequency is not correctness | false |
| TR_AUDIT_EVENT__AUDIT_EVENT_FOR_PURCHASE_ORDER__FORWARD__PURCHASE_ORDER | AUDIT_EVENT_FOR_PURCHASE_ORDER | AUDIT_EVENT | PURCHASE_ORDER | FORWARD | CONTEXT | 0 | 5000 exact edges | mean 0.178387; med 0; p95 1; p99 1; max 1 | A typed audit event's entity_id exactly identifies one purchase order. | RETAINED — exact frozen relation; validation frequency is not correctness | false |
| TR_GL_ENTRY__GL_SOURCE_BANK_TRANSACTION__FORWARD__BANK_TRANSACTION | GL_SOURCE_BANK_TRANSACTION | GL_ENTRY | BANK_TRANSACTION | FORWARD | BACKBONE | 0 | 314 exact edges | mean 0.006716; med 0; p95 0; p99 0; max 1 | A GL entry's typed source_transaction_id exactly identifies a bank transaction for approved transaction types. | RETAINED — exact frozen relation; validation frequency is not correctness | false |
| TR_GL_ENTRY__GL_SOURCE_INVOICE__FORWARD__INVOICE | GL_SOURCE_INVOICE | GL_ENTRY | INVOICE | FORWARD | BACKBONE | 0 | 33957 exact edges | mean 0.726275; med 1; p95 1; p99 1; max 1 | A GL entry's typed source_transaction_id exactly identifies an invoice for approved transaction types. | RETAINED — exact frozen relation; validation frequency is not correctness | false |
| TR_INVOICE_LINE__LINE_OF_INVOICE__FORWARD__INVOICE | LINE_OF_INVOICE | INVOICE_LINE | INVOICE | FORWARD | BACKBONE | 0 | 18299 exact edges | mean 1.000000; med 1; p95 1; p99 1; max 1 | An invoice line is an exact component of its invoice through invoice_id. | RETAINED — exact frozen relation; validation frequency is not correctness | false |

All eight are retained with `VALIDATION_ROUTE_USAGE = 0` and `STRUCTURALLY_JUSTIFIED = true` in the frozen grammar metadata.

## Z. Risk register

| ID | Risk | Inherent | Residual | Frozen mitigation |
| --- | --- | --- | --- | --- |
| R01 | Graph explosion | MEDIUM | LOW | Explicit whitelist, depth 3, record-ID-simple paths, hub bans, full fanout enumeration, and a topology regression gate; an unexplained material increase is NEEDS_REVIEW, not a reason for metric-tuned pruning. |
| R02 | Hub leakage | HIGH | LOW | No Vendor/Employee transition is executable; context nodes are terminal when reached and default-deny is enforced. |
| R03 | Cycles | HIGH | LOW | Reject a neighbor before enqueue when its record_id already appears in the path; depth remains three. |
| R04 | Temporal leakage | MEDIUM | LOW | Require source, target, persisted edge, and provenance-effective availability eligibility on every hop. |
| R05 | Semantic leakage | LOW | LOW | Every transition is justified only by frozen operational fields and topology; semantic fallback is explicitly prohibited. |
| R06 | Validation overfitting | HIGH | LOW | Transition selection used registry semantics and label-independent topology only; structural coverage is reported after selection and never used as gold optimization. |
| R07 | Ambiguity collapse | MEDIUM | LOW | Enumerate all exact neighbors in deterministic order and retain every provenance record; do not use a cap as semantic cardinality. |
| R08 | Provenance loss | MEDIUM | LOW | Persist transition, edge, relation/direction, provenance record/fields, cutoff outcome, node sequence, and path class for every hop. |
| R09 | Production interpretability | MEDIUM | LOW | Human-readable transition justifications plus one deduped evidence record and all supporting path ledgers. |
| R10 | Context bridge leakage | HIGH | LOW | Terminal-on-entry state; exact event anchors get one owner exit only; actor/Employee and Vendor exits are absent. |
| R11 | GL source-type confusion | MEDIUM | LOW | Require exact source_transaction_id plus the frozen transaction_type mapping and matching typed transition. |
| R12 | Fanout/data drift | MEDIUM | MEDIUM | Classify as BOUNDED_FANOUT, mark CAP_NOT_YET_FROZEN, apply no arbitrary truncation, and require freeze-time distribution regression. |
| R13 | Parallel payment representation | MEDIUM | LOW | Retain allocation provenance and multiple path IDs, globally deduplicate records, and label the explicit allocation bridge as the fuller lifecycle route. |
| R14 | Bank settlement limitation | MEDIUM | MEDIUM | Record RELATION_GAP and do not compensate with amount/date/account/currency heuristics; study Tier B separately. |
| R15 | Registry drift | LOW | LOW | Pin and verify raw-byte SHA-256 for all authoritative parents before any design run. |

No HIGH residual risk exists. The two retained review items are GL fan-out drift/production cap governance and absent deterministic bank-settlement linkage. Research traversal enumerates all exact eligible GL edges without a cap; bank settlement remains disabled for a separate Tier-B study.

## AA. Scientific-integrity review

Scientific integrity is **PASS**. Every prohibited activity flag is false: no parent modification, new relation/node, gold or held-out access, previous prediction use, payment-bank/BankStatement relation, Tier B, semantic fallback, LLM/API call, embedding, retriever implementation, retrieval evaluation, or Phase 6B work. Only topology-only structural verification was performed.

## AB. Determinism and hashing

Two independent builds reused the canonical timestamp `2026-08-15T17:54:51Z` and produced identical semantic content and raw bytes for all 14 core artifacts. Manifest and report construction were also regenerated from those identical payloads. Deterministic regeneration result: **PASS**.

Serialization is UTF-8 JSON, lexicographically sorted keys, two-space indentation, `ensure_ascii=false`, LF newlines, and one trailing newline. Transition arrays are ordered by transition ID. No filesystem/hash-map/concurrency ordering is used.

The manifest hashes core frozen artifacts but excludes itself, this report, and the hash inventory. The final hash inventory hashes every other final artifact and omits only its own digest, avoiding circularity; its external raw digest is reported at handoff.

## AC. Known limitations

- GL fan-out production drift/cap governance remains unresolved; no research truncation is frozen.
- Payment-bank settlement linkage remains a deterministic relation gap and separate future Tier-B question.
- BankStatement membership remains an unresolved, excluded capability.
- The exact Phase 6B LLM token cap remains `NOT_YET_FROZEN`.
- Candidate traversal may exceed the later 40-record comparison budget; evidence selection is not implemented here.

This freeze establishes that Graph v1.1 is structurally defined, registry-driven, deterministic, provenance-preserving, temporally bounded, hub-restricted, and scientifically frozen before gold retrieval evaluation.

It does **not** establish that Graph v1.1 beats Relational-RAG, achieves 77.239% retrieval recall, improves full evidence coverage, improves RCA accuracy, or improves LLM performance. Those claims require subsequent experiments.

The serious future comparator remains Relational-RAG. Historical Phase 6A context is micro required-document Recall@40 66.716% and full evidence coverage 15.144%; neither was rerun or optimized here. The future question is: *Does bounded typed multi-hop financial traversal add evidence recovery beyond exact one-hop relational expansion?*

## AD. Implementation readiness decision

Final counts: 30 transitions (18 BACKBONE, 2 SUPPORTING, 5 CONTEXT, 5 TERMINAL_CONTEXT), 15 frozen relation types used, 14 node types available, 14 forbidden directions, maximum depth 3, 76/76 structural sequence coverage, zero semantic draft-to-final transition changes, eight unused-but-retained transitions, and two unresolved production policies.

All implementation-review prerequisites in this freeze prompt pass. This is an internal recommendation only; implementation requires a separate explicit prompt.

RECOMMEND GO FOR GRAPH v1.1 TYPED GRAMMAR IMPLEMENTATION REVIEW
