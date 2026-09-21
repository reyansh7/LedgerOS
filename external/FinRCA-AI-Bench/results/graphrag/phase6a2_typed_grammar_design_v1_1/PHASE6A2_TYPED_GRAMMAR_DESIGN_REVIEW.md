# Phase 6A.2 — GraphRAG v1.1 Typed Financial Traversal Grammar Design Review

`status = PROPOSAL_ONLY`

This package is a design and label-independent structural review. It is not a frozen registry, retriever implementation, retrieval evaluation, or Phase 6B authorization.

## A. Executive recommendation

Recommend independent registry-freeze review of a default-deny grammar with **30 typed directional transitions** over **15 already-frozen relation types**. It represents **76/76 (100.000%)** Phase 6A.1 safe typed sequences while reproducing the bounded 416-route topology profile: 13,371 paths and maximum 91 paths per route case.

The recommendation is only readiness for independent freeze review. It does not freeze or implement Graph v1.1 and makes no claim about retrieval accuracy.

## B. Parent hash verification

The pre-design gate passed **26/26** raw-byte checks over **25 distinct paths**. The Phase 6A.1 report is intentionally checked twice: once against the prompt-pinned digest and again through its inventory. The gate includes the Phase 6A.1 hash inventory, every artifact and analysis script named by it, all five frozen v1 registries, persisted nodes and edges, anchor resolutions, and validation routes.

| Authoritative input | Expected SHA-256 | Observed SHA-256 | Result |
| --- | --- | --- | --- |
| results/graphrag/phase6a1_motif_diagnostic_v1/PHASE6A1_MOTIF_DIAGNOSTIC_REVIEW.md | 4b32dee5614982ffab50d458e9ee876b98f8a4fa70de25b8d8e76aab4233fec6 | 4b32dee5614982ffab50d458e9ee876b98f8a4fa70de25b8d8e76aab4233fec6 | PASS |
| results/graphrag/phase6a1_motif_diagnostic_v1/phase6a1_artifact_hashes.json | d2c70d76e72fbe16a9210f191facbf8eeaecdd97bbd39c009b036cc4d332d7b5 | d2c70d76e72fbe16a9210f191facbf8eeaecdd97bbd39c009b036cc4d332d7b5 | PASS |
| results/graphrag/phase6a_graph_retrieval_v1_0/graph/edges.jsonl | ee364fa677abeda3b25119d5c3c2f1aea5bc8902a28e7f7ecefcddd38a77d9ed | ee364fa677abeda3b25119d5c3c2f1aea5bc8902a28e7f7ecefcddd38a77d9ed | PASS |
| results/graphrag/phase6a_graph_retrieval_v1_0/graph/nodes.jsonl | 87f80fa5e91675b192dd051598a9197c0703650f4daf09c2a7619c031295a167 | 87f80fa5e91675b192dd051598a9197c0703650f4daf09c2a7619c031295a167 | PASS |
| results/graphrag/phase6a_graph_retrieval_v1_0/retrieval/anchor_resolutions.jsonl | b7cfffccc5660b8c50a365b8a72dc656857e4feab8dccb8049634494c6c9f9e2 | b7cfffccc5660b8c50a365b8a72dc656857e4feab8dccb8049634494c6c9f9e2 | PASS |
| results/graphrag/registry_freeze_v1/graph_freeze_manifest_v1.json | 8097eb64accec2c076d07ed9ae4604d2202d1ca83578cf8557b40f034b7cad76 | 8097eb64accec2c076d07ed9ae4604d2202d1ca83578cf8557b40f034b7cad76 | PASS |
| results/graphrag/registry_freeze_v1/graph_node_registry_v1.json | 4c17ff5c863ed446418fbc2b3b407704519862feddc5f0c81546c210f8e91d10 | 4c17ff5c863ed446418fbc2b3b407704519862feddc5f0c81546c210f8e91d10 | PASS |
| results/graphrag/registry_freeze_v1/graph_path_motifs_v1.json | 36dd0b0d491dd6ef5f46c1dcd38cfe5e9e2ab61c632038b89cdc6ed9e0ec58ef | 36dd0b0d491dd6ef5f46c1dcd38cfe5e9e2ab61c632038b89cdc6ed9e0ec58ef | PASS |
| results/graphrag/registry_freeze_v1/graph_ranking_policy_v1.json | 85a167767f6147c2a51db9cdab47d7157731bb2126ca2cf2c452f4e9bde602f0 | 85a167767f6147c2a51db9cdab47d7157731bb2126ca2cf2c452f4e9bde602f0 | PASS |
| results/graphrag/registry_freeze_v1/graph_relation_registry_v1.json | f8c61e2117c09921d001c4d476ef80d138f362c2ac084850544fc56077a7b0c3 | f8c61e2117c09921d001c4d476ef80d138f362c2ac084850544fc56077a7b0c3 | PASS |
| results/rag/phase5_rag_validation_routes_v1_0_20260812T040938Z/validation_routes.jsonl | 08ceeaf3a7c569ca94a87b0c0830d0fb90784daac66dd959de3fee1561b94b44 | 08ceeaf3a7c569ca94a87b0c0830d0fb90784daac66dd959de3fee1561b94b44 | PASS |

No parent artifact was reconstructed or altered.

## C. Why fixed motifs were insufficient

Graph v1.0 froze eight complete motifs: seven one-hop, one two-hop, and no three-hop motif. Phase 6A.1 found 76 safe direction-aware typed sequences, but only five were represented (6.579%). Its sole two-hop motif failed every eligible Invoice-origin attempt because the first reverse edge expected a Purchase Order current node. The graph contained the needed exact relations; the complete-path motif contract could not compose them from the actual current type.

The earlier recall figures are motivation only. They were not rerun, inspected at record level, or used to select a transition.

## D. Typed grammar design principles

The proposed lookup key is `(current node type, frozen relation, direction, next node type, depth, path state)`. Missing rows are denied. Every accepted hop must correspond to one persisted exact edge, preserve its operational provenance, pass temporal eligibility, respect the depth-three/simple-path rules, and obey terminal/hub state controls. Independently valid rows can compose; no complete motif and no unrestricted BFS is required.

The transition inventory was frozen in-memory from registry semantics and Phase 6A.1 safety classes before structural coverage was calculated. Gold outcomes, failure labels, evidence contracts, and retrieval metrics were not design inputs.

## E. Frozen relation reuse

The operational graph remains unchanged at 22 frozen executable relations. The grammar uses 15 relations with traversal and reverse traversal already frozen true. Seven relations remain present for provenance but supply no grammar row: six Vendor/Employee hub relations plus `AUDIT_EVENT_FOR_VENDOR`, where the explicit Vendor policy overrides its bounded degree.

| Frozen relation | Stored types | Grammar disposition | Directional rows |
| --- | --- | --- | --- |
| ALLOCATION_OF_PAYMENT | PAYMENT_ALLOCATION → PAYMENT | USED_BY_EXPLICIT_TYPED_TRANSITIONS | 2 |
| ALLOCATION_TO_INVOICE | PAYMENT_ALLOCATION → INVOICE | USED_BY_EXPLICIT_TYPED_TRANSITIONS | 2 |
| APPROVAL_FOR_INVOICE | APPROVAL_EVENT → INVOICE | USED_BY_EXPLICIT_TYPED_TRANSITIONS | 2 |
| AUDIT_EVENT_FOR_BANK_TRANSACTION | AUDIT_EVENT → BANK_TRANSACTION | USED_BY_EXPLICIT_TYPED_TRANSITIONS | 2 |
| AUDIT_EVENT_FOR_INVOICE | AUDIT_EVENT → INVOICE | USED_BY_EXPLICIT_TYPED_TRANSITIONS | 2 |
| AUDIT_EVENT_FOR_PAYMENT | AUDIT_EVENT → PAYMENT | USED_BY_EXPLICIT_TYPED_TRANSITIONS | 2 |
| AUDIT_EVENT_FOR_PURCHASE_ORDER | AUDIT_EVENT → PURCHASE_ORDER | USED_BY_EXPLICIT_TYPED_TRANSITIONS | 2 |
| AUDIT_EVENT_FOR_VENDOR | AUDIT_EVENT → VENDOR | EXCLUDED_BY_HUB_POLICY | 0 |
| GL_SOURCE_BANK_TRANSACTION | GL_ENTRY → BANK_TRANSACTION | USED_BY_EXPLICIT_TYPED_TRANSITIONS | 2 |
| GL_SOURCE_INVOICE | GL_ENTRY → INVOICE | USED_BY_EXPLICIT_TYPED_TRANSITIONS | 2 |
| GL_SOURCE_PAYMENT | GL_ENTRY → PAYMENT | USED_BY_EXPLICIT_TYPED_TRANSITIONS | 2 |
| INVOICE_FOR_VENDOR | INVOICE → VENDOR | EXCLUDED_BY_HUB_POLICY | 0 |
| INVOICE_LINE_REFERENCES_PO_LINE | INVOICE_LINE → PO_LINE | USED_BY_EXPLICIT_TYPED_TRANSITIONS | 2 |
| INVOICE_REFERENCES_PO | INVOICE → PURCHASE_ORDER | USED_BY_EXPLICIT_TYPED_TRANSITIONS | 2 |
| LINE_OF_INVOICE | INVOICE_LINE → INVOICE | USED_BY_EXPLICIT_TYPED_TRANSITIONS | 2 |
| LINE_OF_PO | PO_LINE → PURCHASE_ORDER | USED_BY_EXPLICIT_TYPED_TRANSITIONS | 2 |
| PAYMENT_ALLOCATED_TO_INVOICE | PAYMENT → INVOICE | USED_BY_EXPLICIT_TYPED_TRANSITIONS | 2 |
| PAYMENT_FOR_VENDOR | PAYMENT → VENDOR | EXCLUDED_BY_HUB_POLICY | 0 |
| PO_FOR_VENDOR | PURCHASE_ORDER → VENDOR | EXCLUDED_BY_HUB_POLICY | 0 |
| PURCHASE_ORDER_CREATED_BY_EMPLOYEE | PURCHASE_ORDER → EMPLOYEE | EXCLUDED_BY_HUB_POLICY | 0 |
| VENDOR_CHANGE_CHANGED_BY_EMPLOYEE | VENDOR_CHANGE → EMPLOYEE | EXCLUDED_BY_HUB_POLICY | 0 |
| VENDOR_CHANGE_FOR_VENDOR | VENDOR_CHANGE → VENDOR | EXCLUDED_BY_HUB_POLICY | 0 |

## F. Proposed transition inventory

| Transition class | Proposed/excluded count | Frozen relations used | Max observed fan-out | Continue allowed? |
| --- | --- | --- | --- | --- |
| Backbone | 18 | 9 | 8 | TRANSITION_SPECIFIC |
| Supporting | 2 | 1 | 3 | YES |
| Context | 5 | 5 | 1 | ANCHOR_EXIT_ONLY_THEN_CONTINUE |
| Terminal context | 5 | 5 | 4 | NO |
| Restricted/excluded | 14 | 7 | 592 | NO |

The 30 executable proposal rows are:

| Transition ID | Class | Multiplicity | Max | Continue |
| --- | --- | --- | --- | --- |
| TR_APPROVAL_EVENT__APPROVAL_FOR_INVOICE__FORWARD__INVOICE | CONTEXT | LOW_FANOUT | 1 | Yes |
| TR_AUDIT_EVENT__AUDIT_EVENT_FOR_BANK_TRANSACTION__FORWARD__BANK_TRANSACTION | CONTEXT | LOW_FANOUT | 1 | Yes |
| TR_AUDIT_EVENT__AUDIT_EVENT_FOR_INVOICE__FORWARD__INVOICE | CONTEXT | LOW_FANOUT | 1 | Yes |
| TR_AUDIT_EVENT__AUDIT_EVENT_FOR_PAYMENT__FORWARD__PAYMENT | CONTEXT | LOW_FANOUT | 1 | Yes |
| TR_AUDIT_EVENT__AUDIT_EVENT_FOR_PURCHASE_ORDER__FORWARD__PURCHASE_ORDER | CONTEXT | LOW_FANOUT | 1 | Yes |
| TR_BANK_TRANSACTION__AUDIT_EVENT_FOR_BANK_TRANSACTION__REVERSE__AUDIT_EVENT | TERMINAL_CONTEXT | TERMINAL_CONTEXT_ONLY | 1 | No |
| TR_BANK_TRANSACTION__GL_SOURCE_BANK_TRANSACTION__REVERSE__GL_ENTRY | BACKBONE | LOW_FANOUT | 2 | No |
| TR_GL_ENTRY__GL_SOURCE_BANK_TRANSACTION__FORWARD__BANK_TRANSACTION | BACKBONE | LOW_FANOUT | 1 | Yes |
| TR_GL_ENTRY__GL_SOURCE_INVOICE__FORWARD__INVOICE | BACKBONE | LOW_FANOUT | 1 | Yes |
| TR_GL_ENTRY__GL_SOURCE_PAYMENT__FORWARD__PAYMENT | BACKBONE | LOW_FANOUT | 1 | Yes |
| TR_INVOICE_LINE__INVOICE_LINE_REFERENCES_PO_LINE__FORWARD__PO_LINE | BACKBONE | LOW_FANOUT | 1 | Yes |
| TR_INVOICE_LINE__LINE_OF_INVOICE__FORWARD__INVOICE | BACKBONE | LOW_FANOUT | 1 | Yes |
| TR_INVOICE__ALLOCATION_TO_INVOICE__REVERSE__PAYMENT_ALLOCATION | BACKBONE | LOW_FANOUT | 3 | Yes |
| TR_INVOICE__APPROVAL_FOR_INVOICE__REVERSE__APPROVAL_EVENT | TERMINAL_CONTEXT | TERMINAL_CONTEXT_ONLY | 4 | No |
| TR_INVOICE__AUDIT_EVENT_FOR_INVOICE__REVERSE__AUDIT_EVENT | TERMINAL_CONTEXT | TERMINAL_CONTEXT_ONLY | 3 | No |
| TR_INVOICE__GL_SOURCE_INVOICE__REVERSE__GL_ENTRY | BACKBONE | BOUNDED_FANOUT | 8 | No |
| TR_INVOICE__INVOICE_REFERENCES_PO__FORWARD__PURCHASE_ORDER | BACKBONE | LOW_FANOUT | 1 | Yes |
| TR_INVOICE__LINE_OF_INVOICE__REVERSE__INVOICE_LINE | BACKBONE | LOW_FANOUT | 4 | Yes |
| TR_INVOICE__PAYMENT_ALLOCATED_TO_INVOICE__REVERSE__PAYMENT | SUPPORTING | LOW_FANOUT | 3 | Yes |
| TR_PAYMENT_ALLOCATION__ALLOCATION_OF_PAYMENT__FORWARD__PAYMENT | BACKBONE | LOW_FANOUT | 1 | Yes |
| TR_PAYMENT_ALLOCATION__ALLOCATION_TO_INVOICE__FORWARD__INVOICE | BACKBONE | LOW_FANOUT | 1 | Yes |
| TR_PAYMENT__ALLOCATION_OF_PAYMENT__REVERSE__PAYMENT_ALLOCATION | BACKBONE | LOW_FANOUT | 2 | Yes |
| TR_PAYMENT__AUDIT_EVENT_FOR_PAYMENT__REVERSE__AUDIT_EVENT | TERMINAL_CONTEXT | TERMINAL_CONTEXT_ONLY | 2 | No |
| TR_PAYMENT__GL_SOURCE_PAYMENT__REVERSE__GL_ENTRY | BACKBONE | LOW_FANOUT | 4 | No |
| TR_PAYMENT__PAYMENT_ALLOCATED_TO_INVOICE__FORWARD__INVOICE | SUPPORTING | LOW_FANOUT | 2 | Yes |
| TR_PO_LINE__INVOICE_LINE_REFERENCES_PO_LINE__REVERSE__INVOICE_LINE | BACKBONE | LOW_FANOUT | 2 | Yes |
| TR_PO_LINE__LINE_OF_PO__FORWARD__PURCHASE_ORDER | BACKBONE | LOW_FANOUT | 1 | Yes |
| TR_PURCHASE_ORDER__AUDIT_EVENT_FOR_PURCHASE_ORDER__REVERSE__AUDIT_EVENT | TERMINAL_CONTEXT | TERMINAL_CONTEXT_ONLY | 1 | No |
| TR_PURCHASE_ORDER__INVOICE_REFERENCES_PO__REVERSE__INVOICE | BACKBONE | LOW_FANOUT | 2 | Yes |
| TR_PURCHASE_ORDER__LINE_OF_PO__REVERSE__PO_LINE | BACKBONE | LOW_FANOUT | 4 | Yes |

## G. Transition classes

`BACKBONE` connects the purchase, invoice, allocation, payment, and typed accounting lifecycle. `SUPPORTING` is the exact Payment↔Invoice projection whose edge retains a specific allocation record. `CONTEXT` is a stored-direction event-anchor exit allowed only at hop 1. `TERMINAL_CONTEXT` gathers a local event from its owning entity and stops. `RESTRICTED` records a frozen relation direction that the executable grammar does not expose.

### Node-level grammar summary

#### APPROVAL_EVENT

Allowed:
- `APPROVAL_FOR_INVOICE:forward` → `INVOICE` (CONTEXT; may continue).

Terminal/context:
- Exact-anchor hop-1 exit only: `TR_APPROVAL_EVENT__APPROVAL_FOR_INVOICE__FORWARD__INVOICE`.
- `TERMINAL_IF_REACHED_AFTER_HOP_0`.

Prohibited:
- `FT_CONTEXT_BRIDGE`, `FT_EMPLOYEE_BRIDGE`.

Maximum reachable depth from an exact anchor: **3**.

Reasoning: An exact approval anchor may exit to its owning Invoice; approval events reached from an Invoice are local evidence and cannot route onward.

#### AUDIT_EVENT

Allowed:
- `AUDIT_EVENT_FOR_BANK_TRANSACTION:forward` → `BANK_TRANSACTION` (CONTEXT; may continue).
- `AUDIT_EVENT_FOR_INVOICE:forward` → `INVOICE` (CONTEXT; may continue).
- `AUDIT_EVENT_FOR_PAYMENT:forward` → `PAYMENT` (CONTEXT; may continue).
- `AUDIT_EVENT_FOR_PURCHASE_ORDER:forward` → `PURCHASE_ORDER` (CONTEXT; may continue).

Terminal/context:
- Exact-anchor hop-1 exit only: `TR_AUDIT_EVENT__AUDIT_EVENT_FOR_BANK_TRANSACTION__FORWARD__BANK_TRANSACTION`, `TR_AUDIT_EVENT__AUDIT_EVENT_FOR_INVOICE__FORWARD__INVOICE`, `TR_AUDIT_EVENT__AUDIT_EVENT_FOR_PAYMENT__FORWARD__PAYMENT`, `TR_AUDIT_EVENT__AUDIT_EVENT_FOR_PURCHASE_ORDER__FORWARD__PURCHASE_ORDER`.
- `TERMINAL_IF_REACHED_AFTER_HOP_0`.

Prohibited:
- `FT_CONTEXT_BRIDGE`, `FT_EMPLOYEE_BRIDGE`, `FT_VENDOR_BRIDGE`, `FT_SYNTHETIC_GL_JOURNAL`.

Maximum reachable depth from an exact anchor: **3**.

Reasoning: An exact audit anchor may exit to its typed owning entity; audit events reached from an entity are local evidence and actor/Vendor routing stays prohibited.

#### BANK_STATEMENT

Allowed:
- None; the transition set is explicitly empty.

Terminal/context:
- No node-level terminal override; individual transition rules still apply.

Prohibited:
- `FT_DEFAULT_DENY_BFS`, `FT_PAYMENT_BANK`, `FT_SAME_ACCOUNT`, `FT_SAME_DATE`.

Maximum reachable depth from an exact anchor: **0**.

Reasoning: No frozen statement-membership relation exists, so the grammar declares an empty transition set instead of synthesizing account/date links.

#### BANK_TRANSACTION

Allowed:
- `AUDIT_EVENT_FOR_BANK_TRANSACTION:reverse` → `AUDIT_EVENT` (TERMINAL_CONTEXT; terminal).
- `GL_SOURCE_BANK_TRANSACTION:reverse` → `GL_ENTRY` (BACKBONE; terminal).

Terminal/context:
- Terminal context: `TR_BANK_TRANSACTION__AUDIT_EVENT_FOR_BANK_TRANSACTION__REVERSE__AUDIT_EVENT`.
- Terminal accounting consequence: `TR_BANK_TRANSACTION__GL_SOURCE_BANK_TRANSACTION__REVERSE__GL_ENTRY`.

Prohibited:
- `FT_PAYMENT_BANK`, `FT_SAME_AMOUNT`, `FT_SAME_ACCOUNT`.

Maximum reachable depth from an exact anchor: **1**.

Reasoning: Only exact typed GL consequences and local audit context are available; payment settlement linkage remains a relation gap.

#### EMPLOYEE

Allowed:
- None; the transition set is explicitly empty.

Terminal/context:
- No node-level terminal override; individual transition rules still apply.

Prohibited:
- `FT_EMPLOYEE_BRIDGE`, `FT_DEFAULT_DENY_BFS`.

Maximum reachable depth from an exact anchor: **0**.

Reasoning: Employee is identity context and a prohibited shared hub, with no outgoing grammar transition.

#### GL_ENTRY

Allowed:
- `GL_SOURCE_BANK_TRANSACTION:forward` → `BANK_TRANSACTION` (BACKBONE; may continue).
- `GL_SOURCE_INVOICE:forward` → `INVOICE` (BACKBONE; may continue).
- `GL_SOURCE_PAYMENT:forward` → `PAYMENT` (BACKBONE; may continue).

Terminal/context:
- Exact-anchor hop-1 exit only: `TR_GL_ENTRY__GL_SOURCE_BANK_TRANSACTION__FORWARD__BANK_TRANSACTION`, `TR_GL_ENTRY__GL_SOURCE_INVOICE__FORWARD__INVOICE`, `TR_GL_ENTRY__GL_SOURCE_PAYMENT__FORWARD__PAYMENT`.
- `TERMINAL_IF_REACHED_AFTER_HOP_0`.

Prohibited:
- `FT_SYNTHETIC_GL_JOURNAL`, `FT_GL_TYPE_MISMATCH`, `FT_REACHED_GL_CONTINUATION`.

Maximum reachable depth from an exact anchor: **3**.

Reasoning: An exact GL anchor may exit through one typed source relation; a GL entry reached from its source transaction is a terminal accounting consequence.

#### INVOICE

Allowed:
- `ALLOCATION_TO_INVOICE:reverse` → `PAYMENT_ALLOCATION` (BACKBONE; may continue).
- `APPROVAL_FOR_INVOICE:reverse` → `APPROVAL_EVENT` (TERMINAL_CONTEXT; terminal).
- `AUDIT_EVENT_FOR_INVOICE:reverse` → `AUDIT_EVENT` (TERMINAL_CONTEXT; terminal).
- `GL_SOURCE_INVOICE:reverse` → `GL_ENTRY` (BACKBONE; terminal).
- `INVOICE_REFERENCES_PO:forward` → `PURCHASE_ORDER` (BACKBONE; may continue).
- `LINE_OF_INVOICE:reverse` → `INVOICE_LINE` (BACKBONE; may continue).
- `PAYMENT_ALLOCATED_TO_INVOICE:reverse` → `PAYMENT` (SUPPORTING; may continue).

Terminal/context:
- Terminal context: `TR_INVOICE__APPROVAL_FOR_INVOICE__REVERSE__APPROVAL_EVENT`, `TR_INVOICE__AUDIT_EVENT_FOR_INVOICE__REVERSE__AUDIT_EVENT`.
- Terminal accounting consequence: `TR_INVOICE__GL_SOURCE_INVOICE__REVERSE__GL_ENTRY`.

Prohibited:
- `FT_VENDOR_BRIDGE`, `FT_PAYMENT_BANK`, `FT_ALLOCATION_BYPASS`.

Maximum reachable depth from an exact anchor: **3**.

Reasoning: Invoice is a lifecycle hub only through exact PO, line, allocation, payment-projection, GL, approval, and audit relations.

#### INVOICE_LINE

Allowed:
- `INVOICE_LINE_REFERENCES_PO_LINE:forward` → `PO_LINE` (BACKBONE; may continue).
- `LINE_OF_INVOICE:forward` → `INVOICE` (BACKBONE; may continue).

Terminal/context:
- No node-level terminal override; individual transition rules still apply.

Prohibited:
- `FT_DEFAULT_DENY_BFS`.

Maximum reachable depth from an exact anchor: **3**.

Reasoning: Invoice lines compose only through their exact owning Invoice and referenced PO line.

#### PAYMENT

Allowed:
- `ALLOCATION_OF_PAYMENT:reverse` → `PAYMENT_ALLOCATION` (BACKBONE; may continue).
- `AUDIT_EVENT_FOR_PAYMENT:reverse` → `AUDIT_EVENT` (TERMINAL_CONTEXT; terminal).
- `GL_SOURCE_PAYMENT:reverse` → `GL_ENTRY` (BACKBONE; terminal).
- `PAYMENT_ALLOCATED_TO_INVOICE:forward` → `INVOICE` (SUPPORTING; may continue).

Terminal/context:
- Terminal context: `TR_PAYMENT__AUDIT_EVENT_FOR_PAYMENT__REVERSE__AUDIT_EVENT`.
- Terminal accounting consequence: `TR_PAYMENT__GL_SOURCE_PAYMENT__REVERSE__GL_ENTRY`.

Prohibited:
- `FT_PAYMENT_BANK`, `FT_VENDOR_BRIDGE`, `FT_ALLOCATION_BYPASS`.

Maximum reachable depth from an exact anchor: **3**.

Reasoning: Payment composes through exact allocation/projection relations and may expose typed GL consequences or local audit context; bank matching is disabled.

#### PAYMENT_ALLOCATION

Allowed:
- `ALLOCATION_OF_PAYMENT:forward` → `PAYMENT` (BACKBONE; may continue).
- `ALLOCATION_TO_INVOICE:forward` → `INVOICE` (BACKBONE; may continue).

Terminal/context:
- No node-level terminal override; individual transition rules still apply.

Prohibited:
- `FT_MULTIPLICITY_COLLAPSE`.

Maximum reachable depth from an exact anchor: **3**.

Reasoning: The allocation record is the provenance-complete bridge between an exact Invoice and Payment and remains composable.

#### PO_LINE

Allowed:
- `INVOICE_LINE_REFERENCES_PO_LINE:reverse` → `INVOICE_LINE` (BACKBONE; may continue).
- `LINE_OF_PO:forward` → `PURCHASE_ORDER` (BACKBONE; may continue).

Terminal/context:
- No node-level terminal override; individual transition rules still apply.

Prohibited:
- `FT_DEFAULT_DENY_BFS`.

Maximum reachable depth from an exact anchor: **3**.

Reasoning: PO lines compose through their exact PO header and exact referencing invoice lines.

#### PURCHASE_ORDER

Allowed:
- `AUDIT_EVENT_FOR_PURCHASE_ORDER:reverse` → `AUDIT_EVENT` (TERMINAL_CONTEXT; terminal).
- `INVOICE_REFERENCES_PO:reverse` → `INVOICE` (BACKBONE; may continue).
- `LINE_OF_PO:reverse` → `PO_LINE` (BACKBONE; may continue).

Terminal/context:
- Terminal context: `TR_PURCHASE_ORDER__AUDIT_EVENT_FOR_PURCHASE_ORDER__REVERSE__AUDIT_EVENT`.

Prohibited:
- `FT_VENDOR_BRIDGE`, `FT_EMPLOYEE_BRIDGE`.

Maximum reachable depth from an exact anchor: **3**.

Reasoning: Purchase orders compose to exact lines and referencing invoices and may expose local audit context; Vendor/Employee bridges are disabled.

#### VENDOR

Allowed:
- None; the transition set is explicitly empty.

Terminal/context:
- No node-level terminal override; individual transition rules still apply.

Prohibited:
- `FT_VENDOR_BRIDGE`, `FT_DEFAULT_DENY_BFS`.

Maximum reachable depth from an exact anchor: **0**.

Reasoning: Vendor is restricted identity/filter context and cannot be a cross-transaction bridge, including through audit events.

#### VENDOR_CHANGE

Allowed:
- None; the transition set is explicitly empty.

Terminal/context:
- No node-level terminal override; individual transition rules still apply.

Prohibited:
- `FT_VENDOR_BRIDGE`, `FT_EMPLOYEE_BRIDGE`, `FT_DEFAULT_DENY_BFS`.

Maximum reachable depth from an exact anchor: **0**.

Reasoning: Vendor changes remain standalone context because their Vendor and Employee relations are frozen traversal-disabled.

## H. Backbone financial lifecycle grammar

The 18 BACKBONE rows are both orientations of nine exact relations: PO header/line, Invoice/PO, InvoiceLine/POLine, Invoice/InvoiceLine, PaymentAllocation/Payment, PaymentAllocation/Invoice, and three typed GL source relations. These rows permit legitimate components to compose without authoring every complete path. A reached GL_ENTRY is the deliberate exception to ordinary backbone continuation.

## I. Payment-allocation design

`PAYMENT_ALLOCATION` remains the provenance-complete bridge: `INVOICE ↔ PAYMENT_ALLOCATION ↔ PAYMENT`. Both allocation edges retain `payment_id`, `invoice_id`, edge ID, and allocation record. The already-frozen `PAYMENT_ALLOCATED_TO_INVOICE` projection is not invented; its two SUPPORTING rows require the same PAYMENT_ALLOCATION provenance. Candidate records are globally deduplicated while every supporting path stays visible. Whether that projection should remain executable is an explicit freeze-review question, not an outcome-tuned choice.

## J. GL source-transaction design

Three typed relation pairs connect GL_ENTRY only to BANK_TRANSACTION, INVOICE, or PAYMENT. Every hop requires exact `(transaction_type, source_transaction_id)`, the frozen type mapping, type agreement, provenance, and cutoff eligibility. A GL_ENTRY anchor may use one stored-direction source row at hop 1 and continue from the source. A GL_ENTRY reached from a transaction is terminal. `GL_JOURNAL`, journal grouping, fuzzy source IDs, and account-based expansion remain prohibited.

## K. Purchase-order / invoice design

Exact PO, PO line, Invoice, and Invoice line relationships can compose in either safely frozen direction. This naturally represents PO→Invoice→Payment and line-level chains when the constituent edges exist; it does not assume or synthesize any missing relation. Vendor and creator-Employee joins are not available to the grammar.

## L. Approval-event policy

Invoice→ApprovalEvent is TERMINAL_CONTEXT and enumerates all exact local events (observed maximum four). An exact ApprovalEvent anchor may take one stored-direction hop to its owning Invoice, then normal lifecycle rules apply. No approver-to-Employee path exists.

## M. Audit-event policy

Operational entity→AuditEvent rows are TERMINAL_CONTEXT for Bank Transaction, Invoice, Payment, and Purchase Order. An exact AuditEvent anchor may take one typed stored-direction owner hop before entering the lifecycle. Actor identity, Vendor audit traversal, and `gl_journal` remain prohibited, so audit evidence cannot bridge subjects.

## N. Vendor and Employee hub policy

All 14 orientations of seven Vendor/Employee relations are excluded. The strongest observed excluded maxima are Vendor→Invoice 592, Vendor→PO 362, Vendor→Payment 217, Employee→VendorChange 146, and Employee→PO 63. `AUDIT_EVENT_FOR_VENDOR` remains excluded despite maximum Vendor→AuditEvent degree one because an exception would change the frozen Vendor policy. Vendor, Employee, and VendorChange have explicit empty outgoing sets.

## O. Bank-transaction limitation

**KNOWN STRUCTURAL LIMITATION — BANK SETTLEMENT LINKAGE EXCLUDED.** Bank Transaction anchors have only exact GL consequences and local Audit Events and therefore remain shallow. No PAYMENT↔BANK_TRANSACTION relation is frozen. The proposal does not compensate with amount, date, currency, account, text, embedding, or nearest-match heuristics; a future Tier-B experiment would require separate authorization and audit.

A second, non-required relation gap is recorded for BANK_STATEMENT→BANK_TRANSACTION membership/reconciliation. Because no such frozen relation exists, BANK_STATEMENT has an explicit empty set; v1.1 neither requires nor synthesizes this navigation.

## P. Cycle prevention

Every path is record-ID-simple and rejects a repeat before enqueue. The simulator rejected 4,018 allowed-transition repeat attempts (depth_2=1,243, depth_3=2,775). Terminal-state checks avoided another 4,415 one-edge returns before adjacency lookup: 2,110 event returns and 2,305 reached-GL returns. Together these controls account for 8,433, matching Phase 6A.1's 8,433 repeated-record candidates despite the different stop-order counter definition.

## Q. Depth policy

`MAX_PATH_DEPTH = 3`. Every accepted prefix is retained by exact depth so later research can separate direct, depth-two, and depth-three evidence. No fourth edge is proposed. Whether depth three's incremental evidence value justifies its complexity is reserved for a future independently authorized retrieval evaluation.

## R. Multiplicity and fan-out

Every proposed direction reports degree over all records of its current type, including zeros, with mean, median, nearest-rank p95/p99, and maximum. All proposed maxima are at most eight. `TR_INVOICE__GL_SOURCE_INVOICE__REVERSE__GL_ENTRY` is the only BOUNDED_FANOUT row: mean 4.168037, median 4, p95 6, p99 7, max 8. It is `CAP_NOT_YET_FROZEN`; this draft applies no arbitrary truncation. Multiplicity remains semantic cardinality, not a ranking device.

The future 40-record selection budget is distinct from traversal. This simulation selects no evidence and permits candidate sets above 40.

## S. Forbidden transitions

- `FT_DEFAULT_DENY_BFS` — Any graph edge without an exact current-type/relation/direction/next-type grammar row. The typed grammar is a whitelist, never generic BFS.
- `FT_VENDOR_BRIDGE` — Any * -> VENDOR -> * cross-transaction path. Vendor is restricted identity/filter context and cannot route between transactions.
- `FT_EMPLOYEE_BRIDGE` — Any * -> EMPLOYEE -> * path, including actor/approver coercion. Employee identity may be shared/system context and cannot route between transactions.
- `FT_PAYMENT_BANK` — PAYMENT <-> BANK_TRANSACTION. The deterministic payment-bank relation is not frozen; amount/date/currency/account heuristics remain Tier B and disabled.
- `FT_SYNTHETIC_GL_JOURNAL` — GL_JOURNAL node, journal_id bridge/group traversal, or AUDIT_EVENT -> GL_JOURNAL. No canonical journal-header source record exists; gl_journal route labels resolve only to GL_ENTRY anchors.
- `FT_SEMANTIC_SIMILARITY` — Embedding, text similarity, semantic neighbor, failure-class, or RCA-concept expansion. Traversal correctness must arise from frozen operational relations, never label or semantic similarity.
- `FT_SAME_CURRENCY` — Traversal based only on equal currency. Equality of a non-node attribute does not establish an operational fact.
- `FT_SAME_AMOUNT` — Traversal based only on equal amount. Equality of a non-node attribute does not establish an operational fact.
- `FT_SAME_DATE` — Traversal based only on equal date or a date window. Date proximity does not establish an operational fact.
- `FT_SAME_ACCOUNT` — Traversal based only on bank_account_id or gl_account. Account values remain context/filter attributes and are not graph nodes or joins.
- `FT_ATTRIBUTE_BRIDGE` — Traversal through department, cost_center, source_system, status, or any other non-node dimension. Attributes cannot be promoted to bridge nodes or inferred edges in this phase.
- `FT_REPEATED_RECORD` — Any candidate path in which a record_id repeats. A record-ID-simple path prohibits A -> B -> A and longer cycles.
- `FT_DEPTH_GT_3` — Any fourth or later graph edge. MAX_PATH_DEPTH is fixed at three for this proposal.
- `FT_CONTEXT_BRIDGE` — Continue from APPROVAL_EVENT or AUDIT_EVENT reached after hop 0. Events enrich local evidence but cannot route to unrelated neighborhoods; an exact event anchor may take one typed owner exit at hop 1.
- `FT_GL_TYPE_MISMATCH` — GL traversal without exact source_transaction_id and frozen transaction_type target mapping. Typed GL provenance must select exactly BANK_TRANSACTION, INVOICE, or PAYMENT.
- `FT_PROVENANCE_MISSING` — Traverse an edge without retainable source fields, target fields, edge ID, and provenance record. Every path step must remain operationally reconstructible.
- `FT_POST_CUTOFF` — Traverse when source, target, edge, or provenance-effective availability exceeds cutoff. Every path participant must be cutoff eligible; edge effective availability is the latest participant availability.
- `FT_AMBIGUOUS_OR_INFERRED_JOIN` — Fuzzy ID, cross-type fallback, nearest neighbor, collision winner, or inferred relation. Only persisted exact frozen edges may be followed.
- `FT_ALLOCATION_BYPASS` — Invented Invoice <-> Payment edge without a PAYMENT_ALLOCATION provenance record. The frozen projection is allowed only with its exact PAYMENT_ALLOCATION provenance; the allocation-node route is the fuller lifecycle representation.
- `FT_MULTIPLICITY_COLLAPSE` — Silently select one neighbor or treat M:N/N:1 as 1:1. Enumerate exact neighbors deterministically; a future cap may stop expansion but cannot rewrite cardinality.
- `FT_REACHED_GL_CONTINUATION` — Continue from GL_ENTRY reached from BANK_TRANSACTION, INVOICE, or PAYMENT. A reached GL entry is a terminal accounting consequence; only an exact GL_ENTRY anchor may exit to one typed source at hop 1.

## T. Structural sequence coverage

Overall STRUCTURAL_SEQUENCE_COVERAGE is **76/76 (100.000%)**, compared with the immutable v1 motif context of 5/76 (6.579%). A sequence counts only when its exact typed/directional transition sequence passes the draft state rules and is emitted at least once in the 416-route topology simulation. It is counted once, not weighted by cases or path instances.

| Exact depth | Represented | Safe denominator | Coverage |
| --- | --- | --- | --- |
| 1 | 14 | 14 | 100.000% |
| 2 | 21 | 21 | 100.000% |
| 3 | 41 | 41 | 100.000% |

By Phase 6A.1 route anchor type:

| Anchor type | Represented | Safe denominator | Coverage |
| --- | --- | --- | --- |
| bank_transaction | 2 | 2 | 100.000% |
| gl_journal | 13 | 13 | 100.000% |
| invoice | 35 | 35 | 100.000% |
| payment | 26 | 26 | 100.000% |

`gl_journal` in this table is the immutable route-label category whose exact resolutions are GL_ENTRY records; it is not a graph node type and does not authorize `GL_JOURNAL`.

Excluded safe sequence count: **0**. No legitimate observed safe sequence is omitted; this result follows from the pre-justified transition inventory and is not a target optimized against gold.

## U. Topology-simulation boundedness

The label-independent simulation used 416 frozen route cases and 430 exact resolved graph roots. It emitted 13,371 accepted path prefixes: depth 1 = 3,332, depth 2 = 4,477, depth 3 = 5,562. Per route case: mean 32.142, p50 31, p75 44, p90 62, p95 68, p99 78, max 91. This exactly matches the Phase 6A.1 safe path counts and has no unexplained expansion.

Unique records including anchors per route case: mean 20.118, p50 20, p75 26, p90 35, p95 38, p99 43, max 50. 9 cases exceed the future 40-record selection reference, which is allowed because no selection is performed here.

The maximum-degree responsible transition is `TR_INVOICE__GL_SOURCE_INVOICE__REVERSE__GL_ENTRY` at 8. The absent hub rows prevented 1,694 prohibited path-state edge incidences across the reachable frontier; no Vendor or Employee node was entered. The candidate path-set digest is `89d7f799f60149a8e6665bf59a484131f450ec2ab435e9a891e1eec3efbb2944`.

Accepted emitted paths contain **22/30** proposed row IDs. The other 8 IDs are the five event-anchor exits plus three exact directions that do not survive into accepted paths for this route set. A missing ID may still have been considered at a frontier and rejected by the simple-path or another later rule. Those rows remain justified by frozen semantics, Phase 6A.1 directionality safety, and graph-global fan-out; 76/76 sequence coverage must not be read as accepted-path exercise of every proposed row.

## V. Mapping from v1 motifs to v1.1 grammar

The eight frozen v1 motifs remain immutable. The mapping is compatibility documentation, not deletion or migration. Exact typed rows fully represent the seven one-hop motifs; the GL wildcard decomposes into three typed rows; and PO_INVOICE_LINES becomes ordinary composition whose direction is selected from the current type. The two already-excluded payment-bank motifs remain intentionally unrepresentable.

| v1 motif | Registry group | v1.1 representability | Direction/status |
| --- | --- | --- | --- |
| PO_WITH_INVOICES | FROZEN | FULLY_REPRESENTABLE | EXACT_TYPED_REVERSE |
| PO_WITH_LINES | FROZEN | FULLY_REPRESENTABLE | EXACT_TYPED_REVERSE |
| PO_INVOICE_LINES | FROZEN | FULLY_REPRESENTABLE | DIRECTION_CORRECTED_NATURALLY_BY_GRAMMAR |
| INVOICE_PAYMENTS | FROZEN | FULLY_REPRESENTABLE | EXACT_TYPED_REVERSE_WITH_MANDATORY_ALLOCATION_PROVENANCE |
| INVOICE_APPROVALS | FROZEN | FULLY_REPRESENTABLE | TERMINAL_CONTEXT |
| INVOICE_AUDIT_EVENTS | FROZEN | FULLY_REPRESENTABLE | TERMINAL_CONTEXT |
| PAYMENT_GL_ENTRIES | FROZEN | FULLY_REPRESENTABLE | TERMINAL_ACCOUNTING_CONSEQUENCE |
| GL_ENTRY_SOURCE_TRANSACTION | FROZEN | FULLY_REPRESENTABLE_BY_TYPED_DECOMPOSITION | WILDCARD_REMOVED |
| INVOICE_PAYMENT_BANK | EXCLUDED | INTENTIONALLY_NOT_REPRESENTABLE | RELATION_GAP |
| GL_PAYMENT_BANK | EXCLUDED | INTENTIONALLY_NOT_REPRESENTABLE | RELATION_GAP |

## W. Risk register

| ID | Risk | Inherent | Residual | Mitigation |
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

No HIGH residual risk remains. Two MEDIUM residual questions are deliberately carried into freeze review: drift/cap governance for Invoice→GL_ENTRY and the known absence of deterministic bank-settlement linkage.

## X. Scientific-integrity audit

Integrity status is **PASS**. No Phase 5, registry v1, Graph v1, Phase 6A, or Phase 6A.1 artifact was modified. No relation or node type was created. Payment-bank, Tier B, semantic fallback, and synthetic GL_JOURNAL remain disabled. No held-out labels, held-out gold, oracle sources, validation gold, retrieval recall, LLM, API, or new embedding was used. Graph v1.1 was neither implemented nor evaluated.

Determinism status is **PASS**: two independent in-process structural runs produced identical transition sets and IDs, structural coverage, path-set digest, fanout statistics, cycle outcomes, and prohibition outcomes.

## Y. Differences from Graph v1.0

Graph v1.0 executes immutable complete motifs and cannot compose arbitrary approved steps. This v1.1 draft proposes a separate state-transition architecture whose rows are typed, directional, provenance-aware, cutoff-aware, default-deny, depth-bounded, and simple-path constrained. It preserves all v1 graph and motif artifacts, adds no operational fact, implements no ranking or record selection, and retains complete path explanations for future deduplication.

The future primary empirical question—outside this phase—is: **Does bounded typed multi-hop traversal add evidence recovery beyond exact one-hop relational expansion?** Relational-RAG remains the benchmark; this design does not recalculate or compare retrieval performance.

## Z. Recommendation for freeze

### Research questions

- **Q1 — More complete than 6.579% motif coverage? YES.** The draft structurally represents 76/76 safe sequences (100.000%) versus 5/76.
- **Q2 — Without generic BFS? YES.** Exactly 30 typed rows are whitelisted; every absent edge/type/direction combination is denied.
- **Q3 — Bounded at depth three with simple paths? YES.** The 416-route simulation remains 13,371 paths with p99 78 and max 91.
- **Q4 — Transactional backbone?** PO header/line, Invoice/PO, InvoiceLine/POLine, Invoice/InvoiceLine, allocation/Payment, allocation/Invoice, and the three typed GL-source relation pairs.
- **Q5 — Terminal context?** ApprovalEvent and AuditEvent are terminal when reached; a reached GL_ENTRY is a terminal accounting consequence. Vendor, Employee, BankStatement, and VendorChange have no outgoing rows.
- **Q6 — Necessary reverse traversals?** Reverse component/header, PO/Invoice, line, allocation, Payment projection, transaction→GL consequence, and entity→local event directions. Each is already frozen reverse-permitted and exact.
- **Q7 — Unsupported executable transition? NO.** Every proposed row uses an already-frozen deterministic relation.
- **Q8 — Deterministic traversal separated from Tier B matching? YES.** Payment-bank and all heuristic matching remain disabled relation gaps.
- **Q9 — Every path operationally explainable? YES.** The path contract retains exact nodes, edges, directions, transition IDs, provenance fields/records, temporal outcomes, depth, and class.
- **Q10 — Ready for independent freeze review without gold evaluation? YES.** All eight readiness gates pass; no retrieval implementation or gold performance evaluation occurred.

### Eight readiness gates

| Gate | Result | Evidence |
| --- | --- | --- |
| GATE_1_LINEAGE_AND_INTEGRITY | GO | 26 parent raw-byte checks over 25 distinct paths passed; every mandated scientific-integrity flag is false. |
| GATE_2_UNIVERSE_AND_RELATION_REUSE | GO | Exactly the 14 frozen node types and 15 of 22 frozen relations are used; no unsupported transition, graph edge, relation type, or node type is introduced. |
| GATE_3_TYPED_DIRECTION_SAFETY | GO | Thirty unique typed rows are frozen-permitted and Phase 6A.1-safe; all 14 Vendor/Employee directions remain excluded, including AUDIT_EVENT_FOR_VENDOR. |
| GATE_4_STATE_AND_HUB_SAFETY | GO | Default deny, depth 3, simple paths, terminal event/GL states, explicit hub/payment-bank/GL_JOURNAL prohibitions, and four empty hub/gap node sets are machine-checked; no Vendor/Employee node is entered. |
| GATE_5_PROVENANCE_TEMPORAL_CARDINALITY | GO | Every row requires an exact typed edge, explicit stored/current/next field provenance, cutoff eligibility, and deterministic full-neighbor enumeration; the persisted simulation has zero provenance/type/temporal violations. |
| GATE_6_BOUNDEDNESS_AND_DETERMINISM | GO | Two canonical simulations agree on every fingerprint; totals and depth counts exactly match Phase 6A.1, p50/p95/p99/max remain 31/68/78/91, and cycle controls reconcile to 8,433. |
| GATE_7_EXPRESSIVENESS_AND_INDEPENDENCE | GO | Structural sequence coverage is exactly 76/76 overall, complete at every depth and anchor type, with zero exclusions and no gold evidence or retrieval metric. |
| GATE_8_PACKAGE_AND_RESIDUAL_RISK | GO | Transition, 14-node, forbidden, 8+2 motif, 30-justification, and risk design objects are complete, and no HIGH residual risk remains. |

Freeze review should specifically decide whether the frozen direct Payment↔Invoice projection remains executable SUPPORTING evidence and whether a later drift study justifies a deterministic cap for Invoice→GL_ENTRY. Neither question blocks this structural proposal, and neither is decided from retrieval outcomes.

RECOMMEND 8/8 GO FOR GRAPH v1.1 TYPED GRAMMAR REGISTRY FREEZE REVIEW
