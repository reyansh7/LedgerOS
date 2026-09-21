# Fixed Motifs vs Typed Financial Traversal Grammar

Status: **PROPOSAL_ONLY**. No grammar, motif, relation, or production traversal change was created.

## Option A — fixed path motifs

Fixed motifs are maximally explicit, reproducible, and easy to audit path by path. Their cost is brittle coverage: each anchor orientation and lifecycle continuation must be enumerated separately, while endpoint types listed as permitted anchors do not make a one-direction motif executable from both endpoints. Maintenance grows with relation-sequence combinations, and the current registry contains seven one-hop motifs, one two-hop motif, and no three-hop motif.

In the safe-reverse diagnostic topology, fixed motifs represent 5/76 distinct direction-aware typed sequences (6.579%). This is a structural coverage result, not a retrieval redesign result.

## Option B — typed financial traversal grammar

A typed grammar can express an approved next edge from the current node type in either stored or explicitly approved reverse orientation. It remains deterministic and explainable if every transition is tied to one frozen exact edge, preserves provenance and cutoff eligibility, excludes Vendor/Employee and attribute hubs, enforces a depth limit, and rejects repeated record IDs.

The diagnostic bound is favorable: at depth 1–3 the maximum was 91 paths for one route anchor (p95 68; p99 78). This does not prove a grammar is safe under different data distributions; degree ceilings and regression tests would still require an independent freeze.

## Comparative assessment

| Criterion | Fixed motifs | Typed grammar |
|---|---|---|
| Interpretability | Highest for each enumerated sequence | High if transition rules and exclusions are explicit |
| Reproducibility | High | High with deterministic ordering/depth/simple-path rules |
| Coverage | Low unless motifs are exhaustively maintained | Higher across valid financial lifecycle continuations |
| Explosion risk | Low by construction | Requires degree, depth, hub, and cycle controls |
| Maintenance | Combinatorial sequence registry | Transition registry plus constraint policy |
| Overfitting risk | High if motifs are chosen from validation evidence | High if grammar transitions are chosen from validation evidence |
| Scientific explanation | Simple but incomplete | More abstract; still auditable from typed transitions |

## Structural conclusion

The topology supports considering a typed grammar because many exact entity-local sequences exist while observed expansion remains bounded under the stated constraints. This conclusion is based on edge semantics and topology only. It does not select a v1.1 design and does not authorize implementation.
