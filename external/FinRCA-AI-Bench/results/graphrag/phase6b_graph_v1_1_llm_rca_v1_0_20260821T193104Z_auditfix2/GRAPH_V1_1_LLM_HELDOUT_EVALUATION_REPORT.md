# Graph v1.1 Retrieval + LLM Held-Out Evaluation

## Executive result

The canonical held-out population contains 439 cases. Graph v1.1 and Standard RAG use the same frozen `gpt-5.6-sol` reasoning protocol, prompt, taxonomy, output schema, and two anchor technical failures.

## Classification

| Metric | Graph v1.1 | Standard RAG | Graph minus Standard |
|---|---:|---:|---:|
| Exact 16-class accuracy | 0.724374 | 0.020501 | 0.703872 |
| Macro F1 | 0.713767 | 0.007353 | 0.706414 |
| Binary F1 | 0.834559 | 0.000000 | 0.834559 |

McNemar exact two-sided p-value: `1.9176146e-93`. Fixed-seed paired bootstrap: 10,000 resamples, seed `20260809`.

## Retrieval versus reasoning

{
  "REASONING_FAILURE_GIVEN_SUFFICIENT_RETRIEVAL": 15,
  "STRUCTURAL_RETRIEVAL_FAILURE": 95,
  "SUCCESS_DESPITE_INCOMPLETE_RETRIEVAL": 254,
  "SUCCESS_WITH_SUFFICIENT_RETRIEVAL": 64,
  "TECHNICAL_FAILURE": 9
}

The decomposition distinguishes structural retrieval failure, the frozen 40-record selector, reasoning failure despite sufficient retrieved evidence, citation outcomes, and technical failures. It does not infer that retrieval was correct merely because an LLM prediction was correct.

## Reproducibility

The run directory retains frozen inference objects, deterministic graph path metadata, exact source-record text, request payloads and hashes, raw model responses, parsed primary predictions, per-case retrieval/evidence/attribution rows, paired tests, and raw-byte inventories.
