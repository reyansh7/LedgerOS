# Standard RAG Pre-Live-Run Audit — Version 1.0

## Frozen configuration

- Specification SHA-256: `390a23c63989a1b7593d336bd96b51f171180729f1e66284688032a01243d715`
- Corpus text-manifest SHA-256: `8842865bd6e688f824a0b16450301fb547c62c4ba495099d605753ebaf2ff00d`
- Embedding-matrix SHA-256: `128e3cd5c4215e9e1f6cdc664b838c1c3aef72b8eb0bc1191d19bf7bf763043a`
- Index-manifest SHA-256: `527b5980f1544dda5eab4581f8cb9c498e2a8e7633e4c061dd232b8cff05e3a6`
- Selected K: `40`
- Selection SHA-256: `07365557a3d4bf04cbfcb4e1e834fad637ad04ab17585aba8cda156ece79c670`
- Query version: `standard_rag_query_v1.0`
- Query-builder SHA-256: `947818f336668feb2e1ef26a45e062954dbf68f82cd4fb714d9678cc1627cffb`
- Prompt SHA-256: `bca6d6d8366c6f95b07f83fc068ead359fc329793987b946a7f491f0ffd4d302`
- Model ID: `gpt-5.6-sol`
- Expected held-out cases: `439`

## Audits

- Context size: PASS
- No graph: PASS
- Runtime leakage: PASS
- Held-out label isolation: PASS
- Secrets: PASS
- Phase 5 tests: PASS
- API mocks: PASS
- Terminal ineligible-anchor technical failures: 2 (`["RCA_000902", "RCA_000955"]`)
- Protocol deviations: NONE
- Generation API calls made before this audit: NO

## Unresolved issues

- None

## Decision

**PHASE 5B READY FOR HELD-OUT RAG RUN**
