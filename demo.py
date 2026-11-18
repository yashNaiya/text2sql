"""Milestone 1 demo: print the authorized schema, retrieved examples and final prompt.

    python demo.py --user bob --question "Show total sales by month in 2017"
    python demo.py --user alice --question "Which payment type is most popular?"
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from example_retriever import ExampleRetriever, make_embedder  # noqa: E402
from pipeline import Pipeline  # noqa: E402
from prompt_builder import render_prompt  # noqa: E402
from rbac import get_role  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--user", required=True, help="alice (Admin) or bob (Analyst)")
ap.add_argument("--question", required=True)
ap.add_argument("--k", type=int, default=3)
ap.add_argument("--embedder", default="auto", choices=["auto", "st", "tfidf"])
a = ap.parse_args()

role = get_role(a.user)
pipe = Pipeline(client=None, retriever=ExampleRetriever(make_embedder(a.embedder)), k=a.k)
prep = pipe.prepare(a.question, role, "schema_rag")

bar = "=" * 72
print(f"{bar}\nUSER: {a.user}   ROLE: {role}\nQUESTION: {a.question}\n{bar}")
print("\n[Step 3] AUTHORIZED SCHEMA\n")
print(prep["schema_text"])
print(f"\n{bar}\n[Step 4] RETRIEVED EXAMPLES (role-filtered)\n")
for e in prep["examples"]:
    print(f"  ({e['score']:.2f}) {e['id']}  {e['question']}\n         {e['sql']}\n")
print(f"{bar}\n[Step 5] FINAL PROMPT  (~{prep['prompt_chars'] // 4} tokens)\n{bar}\n")
print(render_prompt(prep["messages"]))
