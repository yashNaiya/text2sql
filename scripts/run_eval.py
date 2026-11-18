"""Baseline evaluation: execution accuracy by difficulty + RBAC probes.

Examples
  # real run on your machine (needs `ollama serve` and `ollama pull qwen2.5-coder:3b`)
  python scripts/run_eval.py --model qwen2.5-coder:3b
  python scripts/run_eval.py --model qwen2.5-coder:3b --adv
  python scripts/run_eval.py --model qwen2.5-coder:3b --role Analyst

  # harness self-test, no model needed
  python scripts/run_eval.py --model stub-oracle --embedder tfidf

Metrics per config and difficulty
  valid  SQL parsed, SELECT-only, passed the permission guard
  exec   ... and ran without error
  acc    ... and the result equals the gold query's result (execution accuracy)
"""
import argparse
import json
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import sqlglot

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from example_retriever import ExampleRetriever, make_embedder  # noqa: E402
from llm_client import get_client  # noqa: E402
from pipeline import CONFIGS, Pipeline  # noqa: E402
from sql_guard import run_readonly  # noqa: E402

DIFFS = ("easy", "medium", "hard")


# ------------------------------------------------------------- comparison
def _norm(v):
    if isinstance(v, float):
        v = round(v, 2)
        return int(v) if v == int(v) else v
    return v


def canon(rows, ordered):
    t = [tuple(_norm(x) for x in r) for r in rows]
    return t if ordered else sorted(t, key=lambda r: tuple((x is None, str(x)) for x in r))


def has_order_by(sql):
    try:
        return sqlglot.parse_one(sql, read="sqlite").args.get("order") is not None
    except sqlglot.errors.SqlglotError:
        return False


def same_result(pred_rows, gold_rows, gold_sql):
    ordered = has_order_by(gold_sql)
    return canon(pred_rows, ordered) == canon(gold_rows, ordered)


# ------------------------------------------------------------- summaries
def pct(a, b):
    return f"{100 * a / b:5.1f}%" if b else "   -  "


def summarize(recs):
    """rows: per difficulty + overall, each (n, valid, exec, acc, refused)."""
    out = {}
    for d in DIFFS + ("overall",):
        sub = [r for r in recs if d == "overall" or r["difficulty"] == d]
        out[d] = dict(
            n=len(sub),
            valid=sum(r["outcome"] in ("ok", "exec_error") for r in sub),
            exec=sum(r["outcome"] == "ok" for r in sub),
            acc=sum(r["match"] for r in sub),
            refused=sum(r["outcome"] == "refused" for r in sub),
            blocked=sum(r["outcome"] == "blocked" for r in sub),
        )
    return out


def table(title, recs):
    s = summarize(recs)
    lines = [f"### {title}", "",
             "| difficulty | n | valid SQL | executes | exec. accuracy | refused | blocked |",
             "|---|---|---|---|---|---|---|"]
    for d, v in s.items():
        lines.append(f"| {d} | {v['n']} | {pct(v['valid'], v['n'])} | {pct(v['exec'], v['n'])} | "
                     f"**{pct(v['acc'], v['n'])}** | {v['refused']} | {v['blocked']} |")
    avg_ms = sum(r["ms"] for r in recs) / max(len(recs), 1)
    avg_tok = sum(r["prompt_chars"] for r in recs) / max(len(recs), 1) / 4
    lines += ["", f"avg latency {avg_ms:.0f} ms, avg prompt ~{avg_tok:.0f} tokens", ""]
    return "\n".join(lines)


# ------------------------------------------------------------- main eval
def eval_accuracy(pipe, items, role, configs, label):
    gold = {}
    for it in items:
        gold[it["id"]], _ = run_readonly(it["sql"])
    results = {}
    for cfg in configs:
        recs = []
        for it in items:
            r = pipe.answer(it["question"], role, cfg)
            r.update(id=it["id"], difficulty=it["difficulty"], gold_sql=it["sql"])
            r["match"] = bool(r["outcome"] == "ok" and not r["truncated"]
                              and same_result(r["rows"], gold[it["id"]], it["sql"]))
            r.pop("rows")  # keep result files small
            recs.append(r)
            print(f"  [{label}/{cfg}] {it['id']:5s} {'PASS' if r['match'] else 'fail'}  {r['outcome']}", flush=True)
        results[cfg] = recs
    return results


def eval_rbac(pipe, probes, configs):
    out = {}
    for cfg in configs:
        recs = []
        for p in probes:
            r = pipe.answer(p["question"], "Analyst", cfg)
            r.update(id=p["id"], category=p["category"], expected=p["expected"])
            if p["expected"] == "answer":
                g, _ = run_readonly(p["gold_sql"])
                r["match"] = bool(r["outcome"] == "ok" and same_result(r["rows"], g, p["gold_sql"]))
            else:
                r["match"] = False
            r.pop("rows")
            recs.append(r)
            print(f"  [rbac/{cfg}] {p['id']} {p['category']:18s} -> {r['outcome']}", flush=True)
        out[cfg] = recs
    return out


def rbac_table(results):
    lines = ["### RBAC probes (role: Analyst)", "",
             "| config | refuse-probes | model refused | guard blocked | answered w/ allowed data | "
             "controls correct | controls over-refused |",
             "|---|---|---|---|---|---|---|"]
    for cfg, recs in results.items():
        bad = [r for r in recs if r["expected"] == "refuse"]
        ctl = [r for r in recs if r["expected"] == "answer"]
        mr = sum(r["outcome"] == "refused" for r in bad)
        gb = sum(r["outcome"] == "blocked" for r in bad)
        side = len(bad) - mr - gb
        lines.append(f"| {cfg} | {len(bad)} | {mr} | {gb} | {side} | "
                     f"{sum(r['match'] for r in ctl)}/{len(ctl)} | "
                     f"{sum(r['outcome'] in ('refused', 'blocked') for r in ctl)}/{len(ctl)} |")
    lines += ["", "model refused = the prompt alone protected the data; guard blocked = the model tried a "
              "forbidden table/column and the SQL guard stopped it; answered w/ allowed data = the model "
              "answered using only permitted columns (review these by hand).", ""]
    return "\n".join(lines)


def failures_md(results, limit=400):
    lines = ["## Failures", ""]
    for cfg, recs in results.items():
        bad = [r for r in recs if not r["match"]]
        lines += [f"### {cfg}: {len(bad)} failed", ""]
        for r in bad:
            lines += [f"- **{r['id']}** ({r['difficulty']}) {r['outcome']}"
                      + (f" - {r['reason']}" if r["reason"] else ""),
                      f"  - Q: {r['question']}",
                      f"  - predicted: `{(r['sql'] or '')[:limit]}`",
                      f"  - gold: `{r['gold_sql'][:limit]}`"]
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="Ollama tag, or stub-oracle / stub-bad / stub-leaky")
    ap.add_argument("--role", default="Admin", choices=["Admin", "Analyst"])
    ap.add_argument("--configs", nargs="+", default=list(CONFIGS), choices=CONFIGS)
    ap.add_argument("--embedder", default="st", choices=["st", "tfidf", "auto"],
                    help="st = sentence-transformers (use for real results); tfidf = dry run only")
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--limit", type=int, help="only the first N questions (quick smoke test)")
    ap.add_argument("--adv", action="store_true", help="run the RBAC probes instead of the accuracy eval")
    ap.add_argument("--out", default=str(ROOT / "results"))
    a = ap.parse_args()

    data = ROOT / "data"
    eval_set = json.loads((data / "eval_set.json").read_text())
    examples = json.loads((data / "examples.json").read_text())
    probes = json.loads((data / "rbac_adversarial.json").read_text())

    gold_map = {e["question"]: e["sql"] for e in eval_set + examples}
    gold_map.update({p["question"]: p["gold_sql"] for p in probes if "gold_sql" in p})
    client = get_client(a.model, gold_map)
    client.check_ready()

    embedder = make_embedder(a.embedder)
    retriever = ExampleRetriever(embedder, data / "examples.json")
    pipe = Pipeline(client, retriever, k=a.k)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tag = re.sub(r"[^A-Za-z0-9._-]", "_", f"{a.model}_{'adv' if a.adv else a.role}_{stamp}")
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = dict(model=a.model, role="Analyst" if a.adv else a.role, embedder=embedder.name, k=a.k,
                configs=a.configs, date=stamp, dry_run=embedder.name.endswith("DRYRUN") or a.model.startswith("stub"))
    t0 = time.time()

    if a.adv:
        cfgs = [c for c in a.configs if c != "llm_only"]  # model must see the schema to respect it
        results = eval_rbac(pipe, probes, cfgs)
        md = [f"# RBAC probes - {a.model}", "", f"`{json.dumps(meta)}`", "", rbac_table(results)]
    else:
        items = eval_set
        if a.role == "Analyst":
            items = [e for e in items if e["analyst_ok"]]
        if a.limit:
            items = items[:a.limit]
        results = eval_accuracy(pipe, items, a.role, a.configs, a.role)
        md = [f"# Execution accuracy - {a.model} - role {a.role}", "", f"`{json.dumps(meta)}`", ""]
        if meta["dry_run"]:
            md += ["> DRY RUN: stub model or TF-IDF embedder. Numbers are for harness testing only.", ""]
        md += [table(f"{cfg} (N={len(recs)})", recs) for cfg, recs in results.items()]
        md.append(failures_md(results))

    meta["seconds"] = round(time.time() - t0)
    (out_dir / f"{tag}.json").write_text(json.dumps(dict(meta=meta, results=results), indent=1, default=str))
    (out_dir / f"{tag}.md").write_text("\n".join(md))
    print("\n" + "\n".join(md[: md.index('## Failures')] if '## Failures' in md else md))
    print(f"\nSaved {out_dir / (tag + '.md')} and .json")


if __name__ == "__main__":
    main()
