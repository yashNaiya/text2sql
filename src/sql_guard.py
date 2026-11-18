"""SQL guard: parse, authorize and safely execute model output.

This is the real security layer. Prompt filtering can be bypassed; this cannot,
because it checks the SQL that is actually about to run:
  * exactly one statement, and it must be a SELECT (or WITH ... SELECT / UNION)
  * every table must exist and be allowed for the role
  * every column must exist and be allowed for the role
  * SELECT * is rejected when it would expose restricted columns
"""
import re
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path

import sqlglot
from sqlglot import exp

UNAUTHORIZED = "-- UNAUTHORIZED"
ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "olist.db"

_QUERY_TYPES = tuple(getattr(exp, n) for n in ("Select", "SetOperation", "Union") if hasattr(exp, n))
_WRITE_NAMES = ("Insert", "Update", "Delete", "Drop", "Create", "Alter", "Command",
                "Pragma", "Merge", "Attach", "Detach", "TruncateTable")
_WRITE_TYPES = tuple(getattr(exp, n) for n in _WRITE_NAMES if hasattr(exp, n))


@dataclass
class Verdict:
    ok: bool
    status: str  # "ok" | "invalid" | "blocked"
    reason: str = ""
    tables: list = field(default_factory=list)
    columns: list = field(default_factory=list)


def extract_sql(raw: str) -> str:
    """Pull the SQL out of a model reply (handles ``` fences and chatter)."""
    text = (raw or "").strip()
    m = re.search(r"```(?:sql|sqlite)?\s*(.*?)```", text, re.S | re.I)
    if m:
        text = m.group(1).strip()
    return text


def is_refusal(text: str) -> bool:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    return bool(lines) and lines[0].upper().startswith("-- UNAUTHORIZED")


def check(sql: str, perms: dict, full_cols: dict) -> Verdict:
    """Authorize `sql` against perms={table:[cols]}; full_cols={table:[cols]}."""
    try:
        stmts = [s for s in sqlglot.parse(sql, read="sqlite") if s is not None]
    except sqlglot.errors.SqlglotError as e:
        return Verdict(False, "invalid", f"syntax error: {str(e).splitlines()[0][:120]}")
    if len(stmts) != 1:
        return Verdict(False, "invalid", f"expected 1 statement, got {len(stmts)}")
    tree = stmts[0]
    if not isinstance(tree, _QUERY_TYPES) or tree.find(*_WRITE_TYPES):
        return Verdict(False, "invalid", "only SELECT statements are allowed")

    ctes = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
    alias_to_table, real = {}, set()
    for t in tree.find_all(exp.Table):
        name = t.name.lower()
        if name in ctes:
            continue
        real.add(name)
        alias_to_table[(t.alias or t.name).lower()] = name

    known = {k.lower() for k in full_cols}
    for t in sorted(real):
        if t not in known:
            return Verdict(False, "invalid", f"unknown table: {t}", sorted(real))
    for t in sorted(real):
        if t not in perms:
            return Verdict(False, "blocked", f"unauthorized table: {t}", sorted(real))

    full = {t: {c.lower() for c in full_cols[t]} for t in real}
    allowed = {t: {c.lower() for c in perms[t]} for t in real}
    real_cols = set().union(*full.values()) if full else set()
    aliases = {a.alias.lower() for a in tree.find_all(exp.Alias) if a.alias}
    aliases |= {c.name.lower() for c in tree.find_all(exp.ColumnDef)}
    for cte in tree.find_all(exp.CTE):
        talias = cte.args.get("alias")
        for col in (talias.args.get("columns") or []) if talias else []:
            aliases.add(col.name.lower())

    # SELECT * / t.* must not expose restricted columns
    for sel in tree.find_all(exp.Select):
        for e in sel.expressions:
            star = isinstance(e, exp.Star) or (isinstance(e, exp.Column) and isinstance(e.this, exp.Star))
            if not star:
                continue
            tabs = real
            if isinstance(e, exp.Column) and e.table:
                tabs = {alias_to_table.get(e.table.lower(), e.table.lower())} & real or real
            for t in tabs:
                if allowed[t] != full[t]:
                    return Verdict(False, "blocked",
                                   f"SELECT * would expose restricted columns of {t}", sorted(real))

    used = set()
    for c in tree.find_all(exp.Column):
        if isinstance(c.this, exp.Star):
            continue
        name = c.name.lower()
        used.add(name)
        if name not in real_cols:
            if name in aliases:
                continue
            return Verdict(False, "invalid", f"unknown column: {name}", sorted(real), sorted(used))
        if c.table:
            cands = {alias_to_table.get(c.table.lower(), c.table.lower())} & real
            cands = cands or real
        else:
            cands = real
        having = [t for t in cands if name in full[t]]
        if having and not any(name in allowed[t] for t in having):
            return Verdict(False, "blocked", f"unauthorized column: {having[0]}.{name}",
                           sorted(real), sorted(used))
    return Verdict(True, "ok", "", sorted(real), sorted(used))


def run_readonly(sql: str, db_path: Path = DB_PATH, row_limit: int = 10000, timeout: float = 30.0):
    """Execute on a read-only connection with a row cap and a wall-clock timeout.
    Returns (rows, truncated)."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    t0 = time.time()
    con.set_progress_handler(lambda: 1 if time.time() - t0 > timeout else 0, 100000)
    try:
        cur = con.execute(sql)
        rows = cur.fetchmany(row_limit + 1)
    finally:
        con.close()
    return rows[:row_limit], len(rows) > row_limit
