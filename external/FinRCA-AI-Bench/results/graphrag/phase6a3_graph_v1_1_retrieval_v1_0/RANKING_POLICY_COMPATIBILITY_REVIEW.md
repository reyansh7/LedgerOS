# Graph v1.1 Ranking-Policy Compatibility Review

## Decision

The frozen v1 ranking registry is not sufficiently specific to convert Graph v1.1 typed candidate paths into at most 40 unique records without a new scientific design decision. Candidate traversal is authorized and has been frozen; Top-40 selection and validation-gold evaluation are not authorized.

## Frozen policy sources

- `graph_ranking_policy_v1.json`: `85a167767f6147c2a51db9cdab47d7157731bb2126ca2cf2c452f4e9bde602f0`
- `graph_traversal_grammar_v1_1.json`: frozen candidate traversal only; source-record selection is explicitly unimplemented.
- Graph v1.1 proposed structural ordering is labeled metadata for future independent review, and `shorter_path_automatically_preferred` is false.

## Requirement-by-requirement findings

| Requirement | Status | Finding |
|---|---|---|
| exact anchor priority | SPECIFIED | Frozen v1 priority 1 is exact anchor. |
| record budget | SPECIFIED | Frozen v1 maximum_raw_source_records is 40 and applies after traversal. |
| record deduplication and path provenance | SPECIFIED | Graph v1.1 freezes case_id+record_id deduplication and preservation of sorted supporting path IDs. |
| disabled future methods | SPECIFIED | Tier B, semantic fallback, embeddings, learned ranking, and generic BFS remain disabled. |
| BACKBONE priority | AMBIGUOUS | The v1 policy distinguishes direct Tier A from complete Tier A multi-hop, but it does not map Graph v1.1 BACKBONE prefixes and complete lifecycle paths to those classes. |
| SUPPORTING handling | AMBIGUOUS | The frozen v1 policy has no SUPPORTING transition class and does not decide whether the direct Payment↔Invoice projection ranks as direct Tier A or below a provenance-complete allocation path. |
| CONTEXT and TERMINAL_CONTEXT handling | AMBIGUOUS | Approved event/audit context is priority 5, but mixed context-anchor-exit plus lifecycle paths and terminal-context prefixes have no frozen class-assignment rule. |
| complete multi-hop path admission | AMBIGUOUS | The policy does not define which emitted prefixes constitute a complete path or whether selecting a path requires admitting every record on that path. |
| tie breaking over typed paths | AMBIGUOUS | Fewer hops, relation order, and canonical record_id are listed, but no frozen rule defines canonical-record ordering for multiple roots, multi-record paths, or equal-priority paths sharing endpoints. |
| more-than-40 path/record competition | AMBIGUOUS | The registry forbids silent truncation but does not freeze whole-path admission, partial-path admission, or skip/fill behavior when the next ranked path exceeds the remaining record budget. |
| v1.1 selection authorization | AMBIGUOUS | Graph v1.1 does not contain an affirmative executable-selection freeze. |

## Why existing Phase 6A code is not sufficient authority

The prior executable `FrozenPathRanker` and `select_paths_and_records` implementation are not frozen policy artifacts. Reusing their whole-path skip behavior or their v1 event classification would silently choose semantics that the Graph v1.1 freeze did not authorize.

## Candidate freeze completed

Registry-driven traversal emitted 13,371 paths and 8,369 case-record rows. 9 cases exceed 40 candidates. No candidate expansion was truncated and no record was ranked, selected, or dropped.

## Decisions requiring a separate freeze

1. Map BACKBONE, SUPPORTING, CONTEXT, and TERMINAL_CONTEXT path combinations to executable priority classes.
2. Define when an emitted prefix is a complete path for path-first selection.
3. Define canonical tie-breaking across multiple roots and multi-record paths.
4. Define whole-path versus partial-path behavior when fewer than all records on the next path fit the remaining 40-record budget.
5. Define whether the direct supporting Payment↔Invoice projection ranks before or after its provenance-complete allocation route.

BLOCKED — GRAPH v1.1 EVIDENCE-SELECTION POLICY REQUIRES SEPARATE FREEZE
