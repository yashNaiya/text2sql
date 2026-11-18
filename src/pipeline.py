"""Glue: question + role -> authorized schema -> examples -> prompt -> LLM -> guard -> result.

Configs (ablation):
  llm_only    question only, no schema, no examples
  schema      + authorized schema
  schema_rag  + role-filtered retrieved examples
The SQL guard is always on: security is not something we ablate.
"""
import time

from db_setup import get_full_schema
from prompt_builder import build_messages
from rbac import get_permissions
from schema_retriever import format_schema, get_authorized_schema
from sql_guard import check, extract_sql, is_refusal, run_readonly

CONFIGS = ("llm_only", "schema", "schema_rag")

# outcome values
OK, REFUSED, BLOCKED, INVALID, EXEC_ERROR = "ok", "refused", "blocked", "invalid", "exec_error"


class Pipeline:
    def __init__(self, client, retriever=None, k: int = 3):
        self.client, self.retriever, self.k = client, retriever, k
        self._full = {t: [c for c, _ in cols] for t, cols in get_full_schema().items()}
        self._perms = {}

    def perms(self, role):
        if role not in self._perms:
            self._perms[role] = get_permissions(role, self._full)
        return self._perms[role]

    def prepare(self, question: str, role: str, config: str) -> dict:
        if config not in CONFIGS:
            raise ValueError(f"unknown config {config!r}")
        schema_text, examples = None, []
        if config in ("schema", "schema_rag"):
            schema_text = format_schema(get_authorized_schema(role))
        if config == "schema_rag":
            if self.retriever is None:
                raise ValueError("schema_rag needs a retriever")
            examples = self.retriever.retrieve(question, role, self.k)
        messages = build_messages(question, schema_text, examples)
        return dict(schema_text=schema_text, examples=examples, messages=messages,
                    prompt_chars=sum(len(m["content"]) for m in messages))

    def answer(self, question: str, role: str, config: str, execute: bool = True) -> dict:
        prep = self.prepare(question, role, config)
        t0 = time.time()
        raw = self.client.chat(prep["messages"])
        rec = dict(question=question, role=role, config=config, raw=raw, sql=None, rows=None,
                   truncated=False, reason="", examples_used=[e["id"] for e in prep["examples"]],
                   prompt_chars=prep["prompt_chars"], ms=0)
        sql = extract_sql(raw)
        rec["sql"] = sql
        if is_refusal(sql):
            rec["outcome"] = REFUSED
        else:
            v = check(sql, self.perms(role), self._full)
            rec["outcome"], rec["reason"] = {"ok": OK, "invalid": INVALID, "blocked": BLOCKED}[v.status], v.reason
            if v.ok and execute:
                try:
                    rec["rows"], rec["truncated"] = run_readonly(sql)
                except Exception as e:  # noqa: BLE001
                    rec["outcome"], rec["reason"] = EXEC_ERROR, f"{type(e).__name__}: {e}"[:200]
        rec["ms"] = int((time.time() - t0) * 1000)
        return rec
