# Phase 6A.3 Graph v1.1 One-Shot Evaluation Metric Specification

## 1. Purpose

This document preregisters the offline validation evaluation for the clean
Phase 6A.3 Graph v1.1 retrieval run.

The evaluation compares the already-frozen Graph v1.1 candidate pool and
selected evidence against the already-frozen Relational-RAG baseline.

No retrieval, graph traversal, evidence selection, ranking, policy tuning,
embedding generation, LLM inference, or API call is permitted during this
evaluation.

The evaluator may open validation gold only after:

1. this metric specification is frozen,
2. evaluator source is frozen,
3. evaluator synthetic tests pass,
4. evaluator source and test hashes are recorded,
5. the clean pre-gold retrieval gate remains unchanged.

Held-out/test gold is prohibited.

---

## 2. Clean Graph v1.1 run

Run ID:

`phase6a3_graph_v1_1_retrieval_v1_2_20260816T034800Z`

Clean pre-gold manifest SHA-256:

`0c4ec3125a9af91a1ec2e9ee1b7b71bf6105e712a49c1e1413a137a40421fa6f`

Clean pre-gold hash-inventory SHA-256:

`fdba4cab1ca00d83ca42bb2b3e3962aebc31b185a89e952b0fc9a6ea17b415d8`

Graph v1.1 selected paths SHA-256:

`7c50a3569920124286ad1866af28155d6ba25d7e77d6480aaf0627f7c8cd0561`

Graph v1.1 selected records SHA-256:

`e8335a880b0cf57820f58c233f4558b9f4df111f6739f8c13ca7bc04eb994cbd`

Candidate paths SHA-256:

`eab6e5524334001cbb285dbe1cb5367daa70fe008836a9df5ac99fedef695c03`

Candidate records SHA-256:

`4c960019afebaa179f6ef213bd9771c36c82f652dc60b0b1ac1f20f24eff955c`

Graph v1.1 grammar SHA-256:

`2222def5dc3fd18628731949697087c6c96d7cdf1bb6c4cf2d16a1a58da6c8dc`

Evidence-selection policy SHA-256:

`cad5f2298d9dad62599cfe592304c08cf8808441586fb865d1f4824b3054ea1b`

Maximum selected records per case:

`40`

Validation case count:

`416`

---

## 3. Frozen Relational-RAG baseline

Artifact:

`results/graphrag/phase6a_graph_retrieval_v1_0/ablations/relational_rag_results.jsonl`

SHA-256:

`3921c2bbc17373b3dc237dafb8f6f17327e655842acf0ecbbcbc6c23966c58f5`

Expected cases:

`416`

Expected unique case IDs:

`416`

Expected terminal status:

`SUCCESS` for all 416 cases.

Observed frozen retrieval-set range:

`2` to `21` records per case.

Relational-RAG must not be rerun or padded. The comparison uses the frozen
retrieval output as produced. The shared contract is a maximum evidence budget
of 40 records, not a requirement that every system emit exactly 40 records.

---

## 4. Frozen corpus and route lineage

Corpus:

`results/rag/phase5_rag_index_v1_0_20260810T000000Z/corpus`

Expected document count:

`155391`

Corpus documents SHA-256:

`43fe8841d3cbfc64c403349c2336c631c9f6ca9dc35f3e86af1c4ae993441b8c`

Corpus metadata SHA-256:

`e30183ea1e17af182ad24a3177e776a869ed55718872ba6cc1a169506b4f96fb`

Corpus record IDs SHA-256:

`1850249832dbb9c75ddddfa8e82615dd1db138cdd83cb2dc455029035e1b0058`

Validation routes:

`results/rag/phase5_rag_validation_routes_v1_0_20260812T040938Z/validation_routes.jsonl`

Validation route SHA-256:

`08ceeaf3a7c569ca94a87b0c0830d0fb90784daac66dd959de3fee1561b94b44`

---

## 5. Authorized validation-gold projection

Validation evidence may be opened only by the offline evaluator after the
evaluator freeze gate.

Authorized source:

`data/benchmark/validation/rca_ground_truth.jsonl`

The evaluator must project only:

- `case_id`
- `evidence_ids`
- `evidence_required`

No RCA/failure label, expected answer, question text, generated answer,
classification target, or other semantic gold field may be used.

Evidence resolution must reuse the existing frozen evidence-resolution
semantics from `src.rag.evidence.resolve_evidence`.

Retrieval scoring must reuse the existing
`src.rag.evaluation.retrieval_case_metrics` definitions where applicable.

---

## 6. Primary per-case retrieval metric

For case \(i\):

`document_recall_i = |required_record_ids_i ∩ retrieved_record_ids_i| / |required_record_ids_i|`

The existing `retrieval_case_metrics` implementation is authoritative for this
definition.

No case weighting is permitted.

---

## 7. Candidate-pool recall

For each case, use every unique frozen Graph v1.1 candidate record.

Compute per-case document recall using the definition above.

Candidate-pool macro recall is the arithmetic mean across all 416 cases.

This measures traversal/candidate-generation coverage before the 40-record
selection budget.

---

## 8. Graph Selected Recall@40

For each case, use the frozen Graph v1.1 selected-record ordering.

No more than 40 records may appear.

Compute per-case document recall.

Graph Selected Recall@40 is the arithmetic mean across all 416 cases.

No post-gold reranking, padding, filtering, or record substitution is allowed.

---

## 9. Full-evidence coverage

For a system and case:

`full_evidence_coverage = required_record_ids <= retrieved_record_ids`

Graph full-evidence coverage is the fraction of the 416 cases satisfying this
condition using frozen Graph selected records.

Relational full-evidence coverage uses the same definition on frozen
Relational-RAG records.

Candidate-pool full-evidence coverage uses the same definition on all frozen
Graph candidate records.

---

## 10. Strict full-contract coverage

Use the existing `retrieval_case_metrics` definition:

- all required records retrieved,
- annotated evidence IDs covered,
- observable evidence tables covered,
- no absence-only table prevents strict satisfaction.

Report Graph selected strict full-contract coverage.

If scientifically useful, candidate and Relational values may also be reported
using exactly the same implementation.

The definition must not change after gold access.

---

## 11. Relational-RAG Recall@40

For each case, score the frozen Relational-RAG `retrieved_record_ids` using the
same required-record recall definition.

The name Recall@40 denotes the common maximum evidence-budget contract.

Frozen Relational outputs containing fewer than 40 records are not padded.

Macro Relational-RAG Recall@40 is the arithmetic mean of the 416 per-case
recall values.

---

## 12. Absolute macro-recall difference

Compute:

`Graph_Selected_Macro_Recall - Relational_Macro_Recall`

Positive values favor Graph v1.1.

Negative values favor Relational-RAG.

---

## 13. Paired macro-recall difference

For every validation case \(i\):

`delta_i = graph_document_recall_i - relational_document_recall_i`

Report:

`mean(delta_i)`

This is the paired macro-recall difference.

Because both systems are evaluated on the same 416 cases, uncertainty must be
computed on the paired per-case differences, not by independently bootstrapping
the two system means.

---

## 14. Paired macro-recall bootstrap confidence interval

Bootstrap seed:

`20260809`

Bootstrap resamples:

`10000`

Each bootstrap resample samples 416 paired case differences with replacement.

For each resample, compute the arithmetic mean of the sampled differences.

Report the percentile 95% confidence interval:

- 2.5th percentile
- 97.5th percentile

The implementation may reuse the deterministic `_bootstrap_mean` primitive from
`src.rag.evaluation`, provided it uses the frozen seed and 10,000 resamples.

No alternative seed or adaptive resampling is permitted.

---

## 15. Better / equal / worse cases

For each case compare:

`graph_document_recall_i` versus `relational_document_recall_i`

Classify exactly one of:

- `GRAPH_BETTER`
- `EQUAL`
- `GRAPH_WORSE`

Report counts totaling 416.

No tolerance band is used; recall values are exact rational quantities derived
from integer record counts.

---

## 16. Full-evidence paired outcomes

For each case classify exactly one of:

- `GRAPH_ONLY_FULL`
- `RELATIONAL_ONLY_FULL`
- `BOTH_FULL`
- `NEITHER_FULL`

Report all four counts.

Graph-only full-evidence cases are `GRAPH_ONLY_FULL`.

Relational-only full-evidence cases are `RELATIONAL_ONLY_FULL`.

---

## 17. Full-evidence rate difference

Compute:

`Graph_full_evidence_rate - Relational_full_evidence_rate`

Positive values favor Graph v1.1.

---

## 18. McNemar exact test

Use only discordant full-evidence outcomes:

- `b = GRAPH_ONLY_FULL`
- `c = RELATIONAL_ONLY_FULL`

Run an exact two-sided McNemar test using the binomial formulation already used
in `src.rag.evaluation`:

`binomtest(min(b, c), b + c, 0.5).pvalue`

If there are zero discordant cases, define the p-value as `1.0`.

Report:

- Graph-only count
- Relational-only count
- discordant-pair count
- exact two-sided p-value

No asymptotic chi-square approximation is permitted.

---

## 19. Candidate-to-selection recall loss

For each case:

`candidate_to_selection_recall_loss_i =
candidate_pool_document_recall_i - graph_selected_document_recall_i`

Report:

- mean loss
- number of cases with positive loss
- number of cases with zero loss
- maximum loss

The aggregate candidate-to-selection recall loss is:

`candidate_pool_macro_recall - graph_selected_macro_recall`

This diagnostic isolates selection-budget loss from candidate-generation loss.

---

## 20. Required records among the 33 structurally dropped records

The frozen selector produced 33 dropped candidate records.

After authorized gold access, intersect those dropped `(case_id, record_id)`
pairs with each case's resolved required-record set.

Report:

- total structurally dropped records = 33
- dropped records that were required
- unique cases containing at least one required dropped record
- required dropped records by node type
- required dropped records by minimum reachable depth
- required dropped records by frozen structural selection tier

This is evaluation only.

The result must not be used to alter the frozen selection policy in the same
run.

---

## 21. Cases harmed by Top-40

A case is `HARMED_BY_TOP40` iff:

`candidate_pool_document_recall > graph_selected_document_recall`

Report:

- count
- case IDs
- candidate recall
- selected recall
- recall loss
- required records lost by selection

No case is considered harmed merely because non-required candidate records were
dropped.

---

## 22. Minimum required-evidence depth

For every Graph candidate `(case_id, record_id)`, derive the minimum candidate
path depth at which that record is reachable from any exact root.

Use only the already-frozen candidate paths.

No graph retraversal is allowed.

For a required record:

- depth 0 means the record itself is a resolved exact anchor,
- depth 1 means reachable on a depth-1 candidate path,
- depth 2 means the minimum non-anchor reachable depth is exactly 2,
- depth 3 means the minimum non-anchor reachable depth is exactly 3.

If a record appears at multiple depths, use the minimum.

---

## 23. Depth-2-only required evidence

A required record is `DEPTH_2_ONLY` iff:

- it is present in the frozen Graph candidate pool, and
- its minimum Graph candidate depth is exactly 2.

Report:

- required-record incidence count
- unique case count
- selected incidence count
- full list in machine-readable evaluation output

---

## 24. Depth-3-only required evidence

A required record is `DEPTH_3_ONLY` iff:

- it is present in the frozen Graph candidate pool, and
- its minimum Graph candidate depth is exactly 3.

Report:

- required-record incidence count
- unique case count
- selected incidence count
- full list in machine-readable evaluation output

---

## 25. Graph-only depth >=2 required evidence

A required record incidence is Graph-only depth >=2 iff:

1. Graph selected records contain it,
2. Relational-RAG retrieved records do not contain it,
3. its minimum frozen Graph candidate depth is at least 2.

Report:

- required-record incidence count
- unique case count
- depth-2 count
- depth-3 count

This is an observed retrieval difference, not a causal claim.

---

## 26. Multi-hop-benefit cases

Construct a diagnostic depth-1-only Graph set by taking, for each case:

- all mandatory exact anchors, and
- selected Graph records whose minimum reachable Graph depth is <= 1.

This is an evaluation diagnostic only and does not rerun ranking.

A case receives `MULTIHOP_BENEFIT = true` iff the frozen selected Graph result
contains at least one required record with minimum reachable depth >= 2 that is
absent from the diagnostic depth-1-only set.

Report the number of such cases.

---

## 27. Cases made complete by multi-hop

A case is `MADE_COMPLETE_BY_MULTIHOP` iff:

1. frozen Graph selected evidence has full-evidence coverage, and
2. the diagnostic depth-1-only Graph set does not have full-evidence coverage.

Report:

- case count
- case IDs
- required depth-2 evidence involved
- required depth-3 evidence involved

This metric does not claim that the same Top-40 ranking would result under a
counterfactual depth-1 traversal. It measures whether the actually selected
complete evidence set depends on records only reachable at depth >=2.

---

## 28. Per-anchor metrics

Use the already-frozen validation route field:

`primary_entity_type`

For every anchor type with at least one case, report:

- case count
- Graph selected macro recall
- Relational macro recall
- paired recall difference
- Graph full-evidence coverage
- Relational full-evidence coverage
- Graph better/equal/worse counts

No anchor categories may be merged or split after gold access.

---

## 29. Bank-transaction subset

For cases whose frozen route `primary_entity_type` is `BANK_TRANSACTION`,
report:

- case count
- candidate-pool macro recall
- Graph selected macro recall
- Relational macro recall
- Graph full-evidence coverage
- Relational full-evidence coverage
- required records absent from Graph candidate pool
- required records present in candidate pool but absent after Top-40

A missing required record from the candidate pool may support a
relation-coverage-gap hypothesis.

It must not be reported as proof that any specific missing relation caused the
failure unless that causal conclusion follows directly from frozen structural
evidence.

No missing relation may be added in this run.

---

## 30. Source-token distribution

Source-token diagnostics may be computed using the frozen Phase-5 corpus and
existing token-accounting implementation.

Report separately for:

- Graph selected
- Relational-RAG

No token count may affect retrieval membership or ranking.

---

## 31. Latency

Fresh comparative latency is out of scope for this one-shot evaluation because
the clean v1.2 run reuses frozen retrieval artifacts rather than executing both
retrievers under a common timing protocol.

Report latency as:

`NOT_COMPUTED_IN_CLEAN_ONE_SHOT_EVALUATION`

Existing historical timing artifacts must not be presented as if they were
measured by this clean run.

---

## 32. Evaluation determinism

The evaluator must be deterministic for identical frozen inputs.

After the first authorized gold read, the same in-memory projected gold may be
used to compute all preregistered metrics within that single evaluator
execution.

The evaluator should serialize deterministic machine-readable outputs using
stable case ordering and sorted keys where applicable.

No random procedure other than the preregistered deterministic bootstrap is
allowed.

---

## 33. One-shot execution rule

Before the first validation-gold read:

1. metric specification must be hashed,
2. evaluator source must be finalized and hashed,
3. synthetic evaluator tests must pass,
4. test source/results must be hashed,
5. clean pre-gold retrieval hashes must still match,
6. Graph selected output hashes must still match,
7. Relational-RAG baseline hash must match,
8. corpus and route hashes must match.

Only after all checks pass may the evaluator open validation gold.

The validation gold is then projected once into the authorized evidence-only
fields and all preregistered metrics are computed in the same evaluation run.

If the evaluator fails after validation gold has been opened, the run fails
closed.

No evaluator code, metric definition, Graph retrieval artifact, selector,
baseline retrieval output, or statistical procedure may be patched and rerun
within the same scientific run.

Any required correction after gold access requires a separately documented new
evaluation run and explicit scientific-integrity review.

---

## 34. Prohibited evaluation behavior

The evaluator must not:

- modify Graph retrieval outputs,
- rerun graph traversal,
- rerun evidence selection,
- rerun Relational-RAG,
- change the 40-record budget,
- inspect held-out/test gold,
- use RCA labels or expected answers,
- use question text to reinterpret required evidence,
- add relations or nodes,
- enable Payment-Bank traversal,
- enable BankStatement membership,
- add GL_JOURNAL,
- enable Tier B,
- use semantic fallback,
- create embeddings,
- call an LLM or external API,
- tune any metric or threshold from observed validation results.

---

## 35. Required final outputs

The one-shot evaluator must produce machine-readable outputs sufficient to
report:

1. Candidate-pool recall
2. Graph Selected Recall@40
3. Graph full-evidence coverage
4. Graph strict full-contract coverage
5. Relational-RAG Recall@40
6. Relational full-evidence coverage
7. Absolute macro-recall difference
8. Paired macro-recall difference and 95% CI
9. Full-evidence difference and exact McNemar test
10. Better/equal/worse case counts
11. Graph-only full-evidence cases
12. Relational-only full-evidence cases
13. Depth-2-only required evidence
14. Depth-3-only required evidence
15. Graph-only depth >=2 required evidence
16. Multi-hop-benefit cases
17. Cases made complete by multi-hop
18. Candidate-to-selection recall loss
19. Required records among the 33 drops
20. Cases harmed by Top-40
21. Per-anchor metrics
22. Bank-transaction subset diagnostics
23. Source-token distribution
24. Evaluation determinism/integrity metadata
25. All authoritative input hashes

The evaluator must not produce or interpret RCA/generation accuracy.

---

## 36. Scientific interpretation boundary

The evaluation may establish retrieval performance differences between frozen
Graph v1.1 and frozen Relational-RAG.

It may identify observed candidate-generation gaps, selection-budget losses,
and multi-hop evidence contributions.

It must not convert observational retrieval differences into unsupported causal
claims about individual graph relations.

Results must be reported whether Graph v1.1 wins, ties, or loses.

No Graph v1.2 redesign is permitted until this evaluation is finalized and
reviewed.
