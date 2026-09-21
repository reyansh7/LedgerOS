# Graph v1.1 Evidence-Selection Policy Design Rationale

## Stage A scientific boundary

This rationale and `evidence_selection_policy_v1_1_draft.json` were authored before case-level inspection of the nine overloaded candidate pools. Inputs were limited to the frozen Graph v1.1 grammar, transition classes and justifications, the frozen v1 ranking lineage, and the aggregate counts already reported by Phase 6A.3. Validation and held-out gold were not opened. No candidate record identity, record text, RCA label, expected answer, or per-case overloaded path was used to choose a rule.

## Mandatory exact anchors

All exact roots are selected first because they establish the identity of the routed financial object. This follows the frozen exact-anchor contract and resolves the prior ambiguity about whether an `EXACT_MULTI` group may be collapsed: it may not. Roots consume ordinary record slots and are ordered by canonical `record_id`; if roots alone exceed 40, the selector fails closed rather than violating either identity or budget. This rule affects the budget but is label-independent and contains no RCA outcome information.

## Context-anchor owner bridge

The frozen grammar allows an `APPROVAL_EVENT` or `AUDIT_EVENT` root exactly one stored-direction CONTEXT hop to its owning operational record. Selection role `ANCHOR_OWNER_BRIDGE` makes that owner a mandatory continuation of anchor identity without changing the transition's frozen CONTEXT class. It resolves the risk that a context-rooted case could retain only the event while losing the transaction it describes. The bridge consumes only its newly introduced owner record and uses no text, actor, status, or failure signal.

## Maximal-prefix canonicalization

Traversal persists every valid prefix, so allowing all prefixes to compete would duplicate one structural route and make serialization density influence budget use. A nonterminal strict prefix is therefore suppressed only when a longer path from the same exact root preserves the same record, transition, relation-direction, and edge prefix **and belongs to the same preselection semantic family**: backbone, supporting, terminal context, or other context. A backbone prefix is not suppressed merely because it extends to a lower-priority terminal-context path; otherwise event context could accidentally demote the lifecycle structure it decorates. Terminal context, reached GL consequences, maximum-depth stops, mandatory anchor-owner bridges, and prefixes whose extensions change semantic family remain independently meaningful. Suppressed path IDs and their extensions remain in the ledger, preserving provenance. The rule is derived from frozen path state and affects path competition, not graph reachability or gold relevance.

## Semantic priority lattice

The lattice implements the frozen hierarchy of identity, backbone lifecycle, supporting projection, then local context. Classification is ordered and total: recognize the event-root owner bridge first; strip only that leading class for longer-path classification; recognize a final `TERMINAL_CONTEXT` before suffix classes; then recognize pure-backbone GL terminal, pure-backbone maximal lifecycle, and finally any backbone/supporting mixture containing `SUPPORTING`. A residual class combination fails validation rather than entering a fabricated catch-all tier:

1. `MANDATORY_ANCHOR`.
2. `ANCHOR_OWNER_BRIDGE`.
3. `COMPLETE_BACKBONE_ACCOUNTING_PATH` for pure-backbone paths ending in a frozen reached-GL accounting consequence.
4. `MAXIMAL_BACKBONE_LIFECYCLE_PATH` for other canonical pure-backbone lifecycle paths.
5. `BACKBONE_PLUS_SUPPORTING_PATH` for paths containing the frozen supporting Payment↔Invoice projection.
6. `LOCAL_TERMINAL_CONTEXT_PATH` for exact terminal Approval/Audit context.

This resolves how the v1 direct/multi-hop concepts map to typed v1.1 paths. GL receives accounting priority because the frozen transition role is `ACCOUNTING_CONSEQUENCE`, not because of observed gold frequency. Supporting projections follow provenance-complete backbone paths because the frozen grammar explicitly distinguishes those roles. Context follows lifecycle structure so local event multiplicity cannot crowd out core transactions. No numeric relevance weights exist.

## Leading context classification

For a context anchor, one leading `ANCHOR_OWNER_BRIDGE` class is removed only while classifying the remaining suffix. The complete path and its records remain atomic. This lets the owner's lifecycle paths receive their proper backbone/supporting semantics while still selecting the mandatory bridge first. It is global, works beyond the present validation routing mix, and has no case-specific condition.

## Complete-path atomic admission

For each canonical path in frozen order, `PATH_NEW_RECORD_COST` is the count of distinct path records not already selected. A path is admitted only when the full cost fits the remaining budget. All new records are then introduced in path order; otherwise none are. Zero-cost paths are admitted to retain additional provenance. A nonfitting path does not terminate the scan: later structurally ordered paths may still fit, but all backbone and supporting tiers are exhausted before context tiers. This resolves whole-path versus partial-path behavior and prevents an endpoint from being admitted without its unselected structural intermediates. The maximum is 40, never a target.

## Global deduplication and provenance

The record key is `(case_id, record_id)`. One record consumes one slot even when many paths support it. Every selected record retains all frozen supporting path IDs, all transition paths, minimum reachable depth, path classes, node type, root associations, first introduction path, selection tier, and reason. Deduplication reduces cost through objective overlap; it is not a relevance or diversity bonus.

## Multi-root merge

All roots and required context-owner records form one mandatory-set preflight. If their distinct union exceeds 40, the selector fails before emitting a partial selection. Otherwise all roots enter one global budget. Paths from all roots are sorted by semantic keys before root and path fallbacks. There is no root quota and no root-by-root exhaustion phase. This gives equal structural rules to every root without inventing a round-robin whose necessity is not established by frozen semantics.

## Tie breaking and depth

Ties resolve lexicographically by semantic tier, terminal/completeness state, transition-class sequence, descending depth within that same semantic tier, frozen relation-registry ordinal sequence, direction/transition IDs, record sequence, canonical root, root index, edge sequence, and path ID. Depth never overrides semantic tier: a depth-3 backbone accounting path remains ahead of one-hop context. Descending depth within a tier favors the more complete canonical path without a learned weight. Every fallback is serialized explicitly, so filesystem, insertion, random, and concurrency order cannot affect selection.

The Graph v1.1 lattice is an expressly preregistered refinement of the v1 policy's generic direct-before-multihop and fewer-hops-first order. That older ordering cannot express the typed distinction between a complete allocation/accounting lifecycle, a direct supporting projection, and local terminal context. The refinement retains v1's anchor-first, context-below-lifecycle, 40-record maximum, and no-learned-ranking controls; it does not claim unchanged inheritance.

## Context multiplicity

Context paths use frozen semantic tier and canonical transition/record/path ordering. Availability timestamps are not introduced as a selection signal because the frozen candidate contract already provides a complete canonical fallback. No event is ranked by text, actor, status, suspiciousness, or expected failure relevance. Context can use remaining budget only after backbone and supporting paths have been considered.

## Evidence ordering

Membership and order are both frozen. Exact roots come first. New records then appear in the order they are first introduced by admitted paths, and within a path follow its record sequence. Already-ranked records never move. This preserves path coherence while giving a total deterministic order. Prompt layout, model choice, reasoning instructions, and token cap remain outside this freeze.

## Forbidden signals and fail-closed behavior

The selector receives a whitelisted structural projection only: IDs, node types, root association, transition/relation/direction/class metadata, depth and terminal state, and provenance IDs. Record text, gold, labels, token length, embeddings, and model scores are never projected into the selection object. Vendor/Employee bridging, Payment-Bank matching, BankStatement membership, GL_JOURNAL, Tier B, and semantic fallback cannot be introduced because selection never creates candidates. Any unknown class, impossible tie, noncandidate record, partial admission, hash mismatch, mandatory-policy violation, or budget violation is a structural failure requiring a later revision—not an in-run policy patch.

## Relational-RAG comparability

This selector is path-first because Graph v1.1 produces typed paths; Relational-RAG remains unchanged. Scientific comparability later comes from the same 40-record maximum, cases, and scoring definitions, not identical internal selection machinery. No retrieval metric is computed in Phase 6A.3a.
