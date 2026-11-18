# Text-to-SQL on Olist with RBAC + RAG (Milestone 1 + baseline)

Pipeline: question + user -> role -> **authorized schema** -> **role-filtered RAG examples** -> prompt -> local LLM
(Qwen2.5-Coder 3B via Ollama) -> **SQL guard** (sqlglot) -> read-only SQLite.

## Setup (once)

```bash
pip install -r requirements.txt

# 1. data: put the 9 Olist CSVs in data/raw/
#    You already have 8. The geolocation file (61 MB) can be fetched with:
curl -L -o data/raw/olist_geolocation_dataset.csv \
  https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets/olist_geolocation_dataset.csv

# 2. build the SQLite database (data/olist.db)
python src/db_setup.py

# 3. local model
ollama pull qwen2.5-coder:3b       # Ollama must be running: `ollama serve`
```

The first real run also downloads `all-MiniLM-L6-v2` (the embedding model) from Hugging Face.

## Check everything works

```bash
python tests/test_guard.py                       # 25 guard tests, no model needed
python scripts/run_eval.py --model stub-oracle --embedder tfidf   # harness self-test: expect 100%
python demo.py --user bob --question "How many orders were placed per month in 2018?"
```

## Baseline run (what to send back)

```bash
python scripts/run_eval.py --model qwen2.5-coder:3b            # accuracy: Admin, 3 configs x 30 questions
python scripts/run_eval.py --model qwen2.5-coder:3b --adv      # RBAC probes: 15 forbidden + 5 controls
python scripts/run_eval.py --model qwen2.5-coder:3b --role Analyst   # optional: Analyst-answerable subset
```

Each run writes `results/<model>_<role>_<time>.md` (tables + every failure with predicted vs gold SQL)
and `.json` (raw outputs). Send me the `.md` and `.json` files.

Configs (ablation): `llm_only` (question only) -> `schema` (+ authorized schema) -> `schema_rag` (+ examples).

## Metrics

| metric | meaning |
|---|---|
| valid SQL | parses, SELECT-only, passes the permission guard |
| executes | valid and runs without error |
| exec. accuracy | result equals the gold query's result (floats rounded to 2 dp; row order checked only if gold has ORDER BY; column order and count must match) |

## Layout

```
data/roles.json           RBAC: Admin (alice), Analyst (bob)
data/schema_docs.json     column descriptions + Olist gotchas shown to the model
data/examples.json        30 verified NL-SQL pairs  -> vector DB
data/eval_set.json        30 held-out pairs (10 easy / 10 medium / 10 hard) - never indexed
data/rbac_adversarial.json  15 forbidden probes + 5 allowed controls
src/db_setup.py           CSV -> SQLite
src/rbac.py               roles -> permitted tables/columns (deny by default)
src/schema_retriever.py   authorized schema as CREATE TABLE text
src/example_retriever.py  FAISS over question embeddings, filtered by role
src/prompt_builder.py     system + schema + examples + question
src/sql_guard.py          parse / authorize / read-only execute
src/llm_client.py         Ollama client + test stubs
src/pipeline.py           ties it together
scripts/build_examples.py regenerates the datasets; runs every gold query first
scripts/run_eval.py       baseline evaluation
```

## Notes

* Eval questions are *siblings* of retrieval questions (same SQL pattern, different entities), so scores
  measure generalisation to similar patterns, not to completely novel ones.
* `--embedder tfidf` is a word-matching stand-in for dry runs only. Real results use the default (`st`).
* Olist data covers 2016-09 to 2018-10; there is no 2024 data.
