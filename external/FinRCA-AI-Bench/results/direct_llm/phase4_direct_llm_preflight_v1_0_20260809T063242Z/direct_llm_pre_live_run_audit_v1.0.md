# Direct LLM Pre-Live-Run Audit — Version 1.0

## Frozen configuration

- Specification checksum: `fb71556291a92d96913b3a3d8b86b636a88b28569002751bcc6627ed2f487212`
- Prompt checksum: `e4fb908829f412eb0a3015a4d05f29c0603b12cac84ade166aff92b76c78278c`
- Packet-builder checksum: `7f38fd1efdf7ceb57818461b9b6a5a2fa567afa0507167f51f5f5024571a080a`
- Case-packet version: `direct_llm_case_packet_v1.0`
- Selected prompt: `direct_llm_v1.0` (single prompt locked a priori)
- Model ID: `gpt-5.6-sol`
- Provider: `OpenAI`
- Generation configuration: `{"backoff_seconds": [1.0, 2.0, 4.0], "cached_input_usd_per_million_tokens": 0.5, "concurrency": 1, "context_window_tokens": 1050000, "endpoint": "Responses API", "input_usd_per_million_tokens": 5.0, "max_attempts": 4, "max_output_tokens": 1000, "model_id": "gpt-5.6-sol", "output_usd_per_million_tokens": 30.0, "pricing_reference_date": "2026-08-08", "provider": "OpenAI", "reasoning_effort": "medium", "request_timeout_seconds": 120.0, "reserved_output_tokens": 1000, "service_tier": "default", "stability_repetitions": 3, "stability_subset_salt": "phase4-direct-llm-stability-v1.0", "stability_subset_size": 32, "store": false, "structured_output_mode": "Pydantic/JSON Schema strict", "temperature": null, "token_estimator": "ceil(Unicode characters / 3); conservative non-billing estimate", "top_p": null, "truncation": "disabled", "verbosity": "low"}`
- Retry-policy version: `direct_llm_retry_v1.0`
- Structured-output schema version: `direct_llm_output_schema_v1.0`
- Number of test cases: 439

## Audit results

- Frozen artifact checksums: PASS
- Case-packet leakage audit: PASS
- Test-label isolation: PASS
- Context-size audit: PASS
- Mock/unit/integration tests: PASS
- Secret handling: PASS
- Validation-only prompt selection: NOT APPLICABLE — SINGLE PROMPT LOCKED BEFORE API USE
- Validation-only stability analysis: NOT RUN
- Held-out API calls made: NO

## Unresolved protocol issues

- validation-only stability analysis has not been executed

## Decision

The pre-live gate is not satisfied. No held-out inference is authorized unless this document and the machine-readable manifest both state READY.

**PHASE 4 NOT READY FOR LIVE RUN**
