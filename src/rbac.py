"""Step 2: mock authentication + role-based access control.

Deny by default: unknown users, unknown roles and unlisted tables/columns are
never allowed.
"""
import json
from pathlib import Path

from db_setup import get_full_schema

ROOT = Path(__file__).resolve().parent.parent
ROLES_PATH = ROOT / "data" / "roles.json"


class AccessError(Exception):
    pass


def _load() -> dict:
    with open(ROLES_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_role(user: str) -> str:
    users = _load().get("users", {})
    if user not in users:
        raise AccessError(f"Unknown user: {user!r}")
    return users[user]


def get_permissions(role: str, full_schema: dict | None = None) -> dict:
    """Resolve a role into {table: [allowed columns]} against the real schema."""
    cfg = _load()
    if role not in cfg or role == "users":
        raise AccessError(f"Unknown role: {role!r}")
    rc = cfg[role]
    full_schema = full_schema or {t: [c for c, _ in cols]
                                  for t, cols in get_full_schema().items()}
    cols_of = lambda t: [c for c, _ in full_schema[t]] if isinstance(full_schema[t][0], tuple) else full_schema[t]

    tables = list(full_schema) if rc["allowed_tables"] == "*" else rc["allowed_tables"]
    result = {}
    for t in tables:
        if t not in full_schema:
            raise AccessError(f"roles.json lists table {t!r} that does not exist")
        spec = "*" if rc["allowed_columns"] == "*" else rc["allowed_columns"].get(t)
        if spec is None:
            continue  # table allowed but no column rule -> deny
        all_cols = cols_of(t)
        if spec == "*":
            result[t] = all_cols
        else:
            bad = [c for c in spec if c not in all_cols]
            if bad:
                raise AccessError(f"roles.json lists missing columns {bad} for {t}")
            result[t] = [c for c in all_cols if c in spec]  # keep DB column order
    return result
