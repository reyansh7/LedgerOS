# Graph v1.1 Evidence-Selection Freeze Review

## A. Executive decision

The preregistered, label-blind path-first selector passed unchanged and is frozen for a separately authorized Phase 6A.3 resume. This decision does not authorize gold evaluation, retrieval metrics, an LLM, or Phase 6B.

## B. Parent artifact verification

All 151 raw-byte checks over 86 distinct authoritative paths passed. The Phase 6A.3 candidate pool, its nested pre-gold freeze, Graph v1.1 registry freeze, run-manifest lineage, and all nine prompt-pinned hashes reconcile.

## C. Why Phase 6A.3 stopped

Candidate generation succeeded, but ranking correctly stopped because v1 did not fully define how typed paths become at most 40 evidence records. No gold was opened at that stop or during this freeze.

## D. Scientific requirements for the selector

Selection is global, deterministic, path-first, bounded at 40 unique source records, label-blind, provenance-preserving, and restricted to frozen candidates. It cannot create nodes, relations, or traversal.

## E. Policy preregistration procedure

Stage A used only registry semantics and reported aggregate topology. The draft was serialized and hashed as `db509ca1442b832b0c8b4bc401b8902cfec8f4fbd337a00f4ec12a62bf8cfcf8` before overloaded-case contents were inspected. Its raw bytes remained unchanged throughout Stage B.

## F. Selector architecture

The implementation projects only structural fields, canonicalizes same-family redundant prefixes, classifies canonical paths into frozen semantic tiers, applies one total lexicographic order, admits paths atomically, and deduplicates records globally per case.

## G. Mandatory anchor policy

All 430 resolved roots were preloaded at Tier 0. No mandatory anchor was dropped.

## H. EXACT_MULTI policy

There were 14 EXACT_MULTI cases with two roots each. Every root is mandatory; all roots are ordered first by record ID, then all root paths enter one global semantic order. There is no root-by-root exhaustion or round-robin quota. More than 40 mandatory roots fails closed.

## I. Path canonicalization

Exactly 2,767 same-root, same-family, nonterminal strict prefixes were marked `REDUNDANT_PREFIX`; provenance and extension IDs remain in the ledger. Terminal context, reached-GL, max-depth, owner-bridge, and different-family paths remain independent. Suppressed prefixes are not resurrected after a later atomic nonfit.

## J. Semantic path-priority lattice

- Tier 0: `MANDATORY_ANCHOR`
- Tier 1: `ANCHOR_OWNER_BRIDGE`
- Tier 2: `COMPLETE_BACKBONE_ACCOUNTING_PATH`
- Tier 3: `MAXIMAL_BACKBONE_LIFECYCLE_PATH`
- Tier 4: `BACKBONE_PLUS_SUPPORTING_PATH`
- Tier 5: `LOCAL_TERMINAL_CONTEXT_PATH`

Classification checks terminal context before suffix backbone/supporting classes. A supporting-containing path ending in GL remains Tier 4, not Tier 2.

## K. Backbone treatment

Backbone accounting consequences and maximal lifecycle paths precede supporting projections and context. All 2,385 canonical complete-backbone accounting paths were selected; none was budget-dropped.

## L. Supporting treatment

Supporting payment/invoice projections remain eligible after complete/maximal backbone paths. Shared records cost zero, and all supporting explanations remain attached after record deduplication.

## M. Context / terminal-context treatment

An event-root hop-1 owner bridge is mandatory. Current routing contains no event roots, so that branch is covered synthetically. Local terminal context is considered last: 3,528 of 3,574 canonical context paths were admitted and 46 were budget-rejected.

## N. GL terminal policy

Frozen reached-GL accounting consequences are meaningful Tier-2 evidence and remain terminal. Supporting-containing GL paths remain Tier 4. No GL_JOURNAL node or grouping relation exists.

## O. Atomic path admission

At encounter time, cost is the distinct unselected records on the path. A fitting path introduces all missing records in traversal order; a nonfitting path introduces none and scanning continues. Earlier rejects are never reconsidered. Zero-cost paths are admitted for provenance. No partial admission occurred.

## P. Global record deduplication

The key is `(case_id, record_id)`. The selector produced 8,336 unique selected rows and retained every supporting path ID, transition path, minimum depth, path class, root association, first-introduction tier, and frozen rank.

## Q. Tie-breaking

The total order is tier; terminal/completeness rank; transition-class rank sequence; descending depth within tier; frozen relation-registry ordinal sequence; direction/transition sequence; record sequence; root ID; root index; edge sequence; path ID. Relation ordinals are zero-based positions in `graph_relation_registry_v1.json:frozen_relations` (SHA-256 `f8c61e2117c09921d001c4d476ef80d138f362c2ac084850544fc56077a7b0c3`); the grammar `relation_reuse` audit projection is not the ordinal source.

## R. 40-record budget semantics

Forty is a maximum, not a target. Nine cases required truncation and 13 cases ended at exactly 40; coherent selections below 40 were not padded.

## S. Token-policy separation

No token length or prompt budget affects membership or order. Prompt composition and the exact token cap remain Phase 6B concerns.

## T. Structural simulation

The frozen pool contains 416 cases, 13,371 paths, and 8,369 case-records. Canonicalization left 10,604 competing paths; 10,558 were admitted and 46 were atomically rejected for budget. The selector returned 8,336 records and dropped 33.

## U. Nine over-budget cases

| Case | Candidate records | Selected | Dropped | Candidate paths | Selected paths | Dropped paths |
|---|---:|---:|---:|---:|---:|---:|
| RCA_000747 | 41 | 40 | 1 | 74 | 59 | 15 |
| RCA_000873 | 47 | 40 | 7 | 87 | 61 | 26 |
| RCA_001322 | 42 | 40 | 2 | 76 | 61 | 15 |
| RCA_001346 | 43 | 40 | 3 | 78 | 62 | 16 |
| RCA_001451 | 45 | 40 | 5 | 83 | 61 | 22 |
| RCA_001902 | 41 | 40 | 1 | 75 | 60 | 15 |
| RCA_002014 | 43 | 40 | 3 | 79 | 62 | 17 |
| RCA_002121 | 41 | 40 | 1 | 73 | 59 | 14 |
| RCA_002233 | 50 | 40 | 10 | 91 | 58 | 33 |

All nine retained every anchor, stayed at 40, admitted no partial path, and dropped only Tier-5 local context records: 30 audit events and three approval events. This is a structural statement, not a claim about correctness or gold retention.

## V. Path completeness

Complete backbone paths: 2,385/2,385 selected; budget drops 0. Terminal-context paths: 3,528/3,574 selected; budget drops 46.

## W. Selection pressure by semantic tier

Selected-record first-introduction counts were Tier 0=430, Tier 1=0, Tier 2=3029, Tier 3=1705, Tier 4=715, Tier 5=2457. All 33 dropped records had best available Tier 5. Candidate mean=20.117788, selected mean=20.038462, and dropped mean=0.079327 records per case.

## X. Stress tests

Synthetic fixtures covered anchor-only, 40, 41, 50, and 121 records; EXACT_MULTI; overlap; multiple GL paths; backbone/supporting overlap; 60 context records; a one-new-slot overlap; an atomic three-new/two-left nonfit; all-fit; and mandatory overflow. All 23 tests passed.

## Y. Negative tests

Tests demonstrate mandatory anchors cannot be silently dropped, the cap cannot be exceeded, out-of-pool records and unregistered/forbidden transitions fail closed, atomic paths cannot split, EXACT_MULTI cannot collapse, and gold/model/embedding/token fields cannot affect selection because they are not projected.

## Z. Determinism

Two same-input runs and a reversed-input-order run had identical selected paths, records, ordering, tiers, reasons, drop ledgers, and supporting provenance. All five component hashes match. The implementation is serial-only, so parallel equivalence is not applicable.

## AA. Scientific integrity

Graph, grammar, and candidate artifacts were unchanged. Validation and held-out gold remained unopened. No LLM/API/embedding, relevance weights, retrieval metric, RCA accuracy, graph retraversal, Relational-RAG comparison, or Phase 6B work occurred.

## AB. Draft-to-final semantic diff

`SEMANTIC_POLICY_DIFF_COUNT = 0`. Only status/version/freeze filename, timestamp, parent-draft reference, and validation metadata differ. The preregistered draft hash remains `db509ca1442b832b0c8b4bc401b8902cfec8f4fbd337a00f4ec12a62bf8cfcf8`.

## AC. Frozen artifact hashes

| Artifact | SHA-256 | Bytes |
|---|---|---:|
| `EVIDENCE_SELECTION_POLICY_DESIGN_RATIONALE.md` | `8123b92e49f59824fd36438e9599290242657aef8523c19168c75f743c5e2868` | 9475 |
| `evidence_selection_freeze_manifest_v1_1.json` | `9f89654a5b7e80b7df1eabc4e506ef188dfe8b9b2a75471195a634bcb17b24f7` | 5147 |
| `evidence_selection_policy_v1_1.json` | `cad5f2298d9dad62599cfe592304c08cf8808441586fb865d1f4824b3054ea1b` | 15374 |
| `evidence_selection_policy_v1_1_draft.json` | `db509ca1442b832b0c8b4bc401b8902cfec8f4fbd337a00f4ec12a62bf8cfcf8` | 15772 |
| `over_budget_case_diagnostics.json` | `eaa8fdb02a8484cf525ee17ba29418ddd20f91a669f2ebd0003082a40e1cb872` | 11349 |
| `policy_preregistration_manifest.json` | `8271c15c39c6d2a85f25aacb306a3d31e14898fee368615b402ee01ffa3bdb61` | 2479 |
| `scientific_integrity_selection_freeze.json` | `ea1164338d0464d236ec0993777f8b997844618f529cb7f7b76faf0421e858d8` | 1586 |
| `selection/drop_ledger_pre_gold.jsonl` | `c367f2436a8b52b59ef394e84845b2b26408f16ef72e78b30cf8cd57d1aad3e9` | 1534349 |
| `selection/selected_paths_pre_gold.jsonl` | `7c50a3569920124286ad1866af28155d6ba25d7e77d6480aaf0627f7c8cd0561` | 19458898 |
| `selection/selected_records_pre_gold.jsonl` | `e8335a880b0cf57820f58c233f4558b9f4df111f6739f8c13ca7bc04eb994cbd` | 41745675 |
| `selection/selection_results_pre_gold.jsonl` | `e9ed35885fc76f55d2b431039cf94b97bbff7740bd3fdcbac125244ca5a6c5e7` | 1074429 |
| `selection_determinism_validation.json` | `d454152f0c91060777f43bbb6b0f4230c7b7d25a17046f5fa189d02eb82823dd` | 2044 |
| `selection_policy_semantic_diff.json` | `4a3526fc49f9518ae8c718943addb86ecef50f1ecd52e8b1cf181b2e3ac715bb` | 807 |
| `selection_pressure_diagnostics.json` | `cec9840641af0e8b256171ee5481fdcaf7ea2dabd14bf15bc0177f333bf4973f` | 2390 |
| `selection_structural_validation.json` | `bc24a068b1a2c73a7a25baa88c9cd36ace8ec599fb9b872ae2055962fe5ef918` | 70436 |
| `selector_test_results.json` | `c125e4a7081522c3f1d0126540716915352363865ea183b90143c5657ff7e2a3` | 841 |

The report and hash-inventory digests are necessarily closed by the noncircular final hash inventory and external handoff digest.

## AD. Known limitations

This phase establishes selection semantics, not evidence quality. Payment↔bank settlement and BankStatement membership remain absent relation gaps; GL fan-out governance remains separate; token/prompt policy remains unfrozen; and the current 416-case routing does not dynamically exercise event-root owner bridges. Synthetic tests cover selector behavior beyond the current topology.

## AE. Phase 6A.3 resume readiness

Every freeze condition passed unchanged. The freeze does not itself authorize resumption, gold evaluation, LLM inference, or Phase 6B; those require a separate explicit instruction.

RECOMMEND GO FOR PHASE 6A.3 RESUME — PRE-GOLD SELECTION POLICY FROZEN
