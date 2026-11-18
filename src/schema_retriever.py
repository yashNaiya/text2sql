"""Step 3: authorized schema retrieval.

Returns only the tables/columns a role may see, rendered as CREATE TABLE text
with short comments (small models read this better than JSON).
"""
import json
import re
from pathlib import Path

from db_setup import get_full_schema
from rbac import get_permissions

ROOT = Path(__file__).resolve().parent.parent
DOCS_PATH = ROOT / "data" / "schema_docs.json"


def _docs() -> dict:
    with open(DOCS_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_authorized_schema(role: str, question: str | None = None,
                          max_tables: int | None = None) -> dict:
    """{table: [(column, type), ...]} limited to what `role` may see.

    Optional keyword filter: if `max_tables` is set, keep the tables whose
    names/descriptions/columns best match the question. With 9 tables this is
    off by default; the hook is here so it scales to larger databases.
    """
    full = get_full_schema()
    perms = get_permissions(role, {t: [c for c, _ in cols] for t, cols in full.items()})
    schema = {t: [(c, ty) for c, ty in full[t] if c in perms[t]] for t in perms}

    if max_tables and question and len(schema) > max_tables:
        words = set(re.findall(r"[a-z]+", question.lower()))
        docs = _docs()

        def score(t):
            text = t + " " + docs.get(t, {}).get("description", "") + " " + " ".join(c for c, _ in schema[t])
            return len(words & set(re.findall(r"[a-z]+", text.lower())))

        keep = sorted(schema, key=score, reverse=True)[:max_tables]
        schema = {t: schema[t] for t in schema if t in keep}
    return schema


def format_schema(schema: dict, with_docs: bool = True) -> str:
    docs = _docs() if with_docs else {}
    blocks = []
    for table, cols in schema.items():
        tdoc = docs.get(table, {})
        lines = []
        if tdoc.get("description"):
            lines.append(f"-- {tdoc['description']}")
        lines.append(f"CREATE TABLE {table} (")
        for i, (col, ty) in enumerate(cols):
            comma = "," if i < len(cols) - 1 else ""
            note = tdoc.get("columns", {}).get(col)
            comment = f"  -- {note}" if note else ""
            lines.append(f"  {col} {ty}{comma}{comment}")
        lines.append(");")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


if __name__ == "__main__":
    import sys
    from rbac import get_role
    user = sys.argv[1] if len(sys.argv) > 1 else "bob"
    print(format_schema(get_authorized_schema(get_role(user))))
