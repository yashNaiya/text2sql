# Execution accuracy - stub-oracle - role Admin

`{"model": "stub-oracle", "role": "Admin", "embedder": "tfidf-DRYRUN", "k": 3, "configs": ["llm_only", "schema", "schema_rag"], "date": "20261004_221010", "dry_run": true}`

> DRY RUN: stub model or TF-IDF embedder. Numbers are for harness testing only.

### llm_only (N=30)

| difficulty | n | valid SQL | executes | exec. accuracy | refused | blocked |
|---|---|---|---|---|---|---|
| easy | 10 | 100.0% | 100.0% | **100.0%** | 0 | 0 |
| medium | 10 | 100.0% | 100.0% | **100.0%** | 0 | 0 |
| hard | 10 | 100.0% | 100.0% | **100.0%** | 0 | 0 |
| overall | 30 | 100.0% | 100.0% | **100.0%** | 0 | 0 |

avg latency 398 ms, avg prompt ~75 tokens

### schema (N=30)

| difficulty | n | valid SQL | executes | exec. accuracy | refused | blocked |
|---|---|---|---|---|---|---|
| easy | 10 | 100.0% | 100.0% | **100.0%** | 0 | 0 |
| medium | 10 | 100.0% | 100.0% | **100.0%** | 0 | 0 |
| hard | 10 | 100.0% | 100.0% | **100.0%** | 0 | 0 |
| overall | 30 | 100.0% | 100.0% | **100.0%** | 0 | 0 |

avg latency 419 ms, avg prompt ~1343 tokens

### schema_rag (N=30)

| difficulty | n | valid SQL | executes | exec. accuracy | refused | blocked |
|---|---|---|---|---|---|---|
| easy | 10 | 100.0% | 100.0% | **100.0%** | 0 | 0 |
| medium | 10 | 100.0% | 100.0% | **100.0%** | 0 | 0 |
| hard | 10 | 100.0% | 100.0% | **100.0%** | 0 | 0 |
| overall | 30 | 100.0% | 100.0% | **100.0%** | 0 | 0 |

avg latency 424 ms, avg prompt ~1523 tokens

## Failures

### llm_only: 0 failed


### schema: 0 failed


### schema_rag: 0 failed

