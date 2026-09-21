# Graph v1.1 Held-Out LLM Experiment — Pre-Inference Readiness

## Decision

GO. The frozen Graph v1.1 graph, 30-transition grammar, and evidence selector have been applied label-blind to the canonical 439-case test routes. There are 437 exactly resolved model contexts and the same two deterministic unresolved GL-journal anchors as Standard RAG.

## Fairness and lineage

- Standard RAG comparator: `results/rag/phase5_rag_prelive_v1_0_20260812T043901Z`
- Test routes SHA-256: `efccfa96f231d72fe153f77bcb0a7b8df73cf765706d78589cf12ba8ed307ca7`
- Prompt reused byte-for-byte: `bca6d6d8366c6f95b07f83fc068ead359fc329793987b946a7f491f0ffd4d302`
- Model/config: `gpt-5.6-sol`, reasoning effort `medium`, max output `1000`, verbosity `low`
- Graph adapter validation equivalence: PASS on all 416 validation cases and `13,371` paths
- Held-out labels, expected answers, failure manifests, and oracle packages opened before inference: NO
- Paid API calls made: NO

## Current blocker

`OPENAI_API_KEY` is not available in the current environment. All retrieval, serialization, parser, checkpoint, resume, and evaluation infrastructure is frozen and tested. The exact resume command is emitted by the preparation command after the external pre-inference inventory hash is known.
