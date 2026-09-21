# Phase 6A.3 Graph v1.1 One-Shot Validation Review

## A. Executive finding

The retrieval bundle passed its structural pre-gold freeze, but the one-shot evaluation is blocked. A delegated mapping audit read raw bytes from five validation artifacts with `shasum` and `wc -l` before the final pre-gold gate timestamp. No semantic records or labels were exposed, but the prompt makes any pre-freeze validation-gold access a scientific-integrity failure. No metric was computed.

## B. Experimental preregistration lineage

The blocked candidate run, Graph v1.1 grammar freeze, and evidence-selection freeze all passed complete raw-byte lineage verification. The selector draft/final semantic diff remained zero.

## C. Graph v1.1 frozen grammar verification

PASS: grammar SHA-256 `2222def5dc3fd18628731949697087c6c96d7cdf1bb6c4cf2d16a1a58da6c8dc`; 30 transitions, 15 relation types, depth 3, and all prohibited traversal modes disabled. No grammar byte changed.

## D. Candidate traversal lineage verification

PASS: 416 cases, 430 roots, 13,371 candidate paths (3,332/4,477/5,562 by depth), and 8,369 candidate-record rows were copied byte-for-byte from the immutable parent.

## E. Frozen evidence-selection verification

PASS: final policy SHA-256 `cad5f2298d9dad62599cfe592304c08cf8808441586fb865d1f4824b3054ea1b`; 8,336 selected records; max 40; 430/430 roots retained; zero partial admissions; 33 Tier-5 drops; zero complete-backbone budget drops.

## F. Final pre-gold retrieval freeze

The structural bundle was written and independently verified. Manifest SHA-256: `e0139ab40956cd9fa548b6218087be990a70dda414e8f5300a52e26ce88b2661`. Pre-gold inventory SHA-256: `18994f6b4f4785b0b7532a78d2d95b010e0b483140f57455e2e4175580ec2df7`. It remains preserved as provenance, but its evaluator authorization is revoked by the subsequently discovered earlier access.

## G. Gold-isolation audit

FAIL. Before `2026-08-16T01:14:00Z`, a delegated mapping audit hashed and line-counted validation `case_ids`, `rca_ground_truth`, `case_entity_records`, `failure_manifest`, and `benchmark_questions`. Output exposed only hashes and line counts; no JSON/CSV rows, IDs, labels, evidence fields, questions, or answers were displayed or parsed. Held-out/test bytes were not read. The exact first-access timestamp was not recorded.

## H. Validation cohort

The intended cohort was the authorized 416-case validation split. Evaluation was not run.

## I. Relational-RAG baseline verification

Not opened after the incident; no baseline metric was copied or computed.

## J. Graph v1.1 candidate-pool metrics

Not computed due to the integrity block.

## K. Graph v1.1 selected Top-40 metrics

Not computed due to the integrity block.

## L. Candidate-vs-selected loss

Structural counts remain frozen (33 dropped records), but gold-dependent selection loss was not computed.

## M. Graph v1.1 vs Relational-RAG

Not computed.

## N. Paired case outcomes

Not computed.

## O. Full-evidence paired outcomes

Not computed.

## P. Statistical uncertainty

No bootstrap, confidence interval, or McNemar test was run.

## Q. Multi-hop evidence contribution

Not computed.

## R. Depth-2 incremental contribution

Not computed.

## S. Depth-3 incremental contribution

Not computed.

## T. Graph-only required evidence

Not computed.

## U. Relational-only required evidence

Not computed.

## V. Transition contribution

No gold-dependent transition contribution was computed.

## W. Path-sequence contribution

No gold-dependent path-sequence contribution was computed.

## X. Path-class contribution

No gold-dependent path-class contribution was computed.

## Y. Selector impact on 9 over-budget cases

Only the preregistered structural result is retained: nine cases were truncated and 33 Tier-5 context records were dropped. Required-gold impact was not computed.

## Z. Anchor-type results

Not computed.

## AA. Invoice cases

Not computed.

## AB. Payment cases

Not computed.

## AC. Bank-transaction cases

Not computed; no relation-gap conclusion was scored.

## AD. GL-journal-route cases

Not computed; no synthetic `GL_JOURNAL` was created.

## AE. Failure attribution

Retrieval failure attribution was not run. The run-level failure is `PRE_FREEZE_VALIDATION_BYTE_ACCESS`.

## AF. Relation gaps

Frozen relation gaps remain unchanged but were not evaluated against gold.

## AG. Record-budget efficiency

The structurally frozen selected-record distribution remains available in the selection freeze; no gold-dependent efficiency metric was computed here.

## AH. Token efficiency

Not computed.

## AI. Latency

Not computed for the resumed evaluation.

## AJ. Determinism

Pre-gold retrieval determinism passed. Evaluation determinism is not applicable because evaluation did not run.

## AK. Tests

The inherited selector suite passed 23/23 and the pre-gold cross-file gate passed. Evaluation tests were not run after the incident.

## AL. Scientific integrity

FAIL. `validation_gold_opened_before_final_pre_gold_freeze=true`; `VALIDATION_GOLD_FIRST_OPENED_AFTER_FREEZE=false`. Retrieval never received gold, no semantic content was exposed, no configuration changed, and held-out gold remained unopened, but the mandatory chronology was violated.

## AM. Known limitations

No retrieval conclusion can be drawn from this attempted one-shot run. The valid pre-gold retrieval files are preserved, but the run cannot satisfy the requested attestation.

## AN. Research interpretation

Scientific success was defined as uncontaminated execution, not as Graph winning. Because that condition failed before scoring, no comparative interpretation is permitted.

## AO. Phase 6B recommendation

Phase 6B is not authorized. A research owner must decide whether a separately governed future evaluation is scientifically permissible; this run cannot be repaired by silently redefining byte access.

RECOMMEND BLOCK — PHASE 6A.3 SCIENTIFIC INTEGRITY OR IMPLEMENTATION FAILURE
