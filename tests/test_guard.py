"""Unit tests for the SQL guard. Run:  python tests/test_guard.py  (or pytest)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from db_setup import get_full_schema  # noqa: E402
from rbac import get_permissions  # noqa: E402
from sql_guard import check, extract_sql, is_refusal, run_readonly  # noqa: E402

FULL = {t: [c for c, _ in cols] for t, cols in get_full_schema().items()}
ANALYST = get_permissions("Analyst", FULL)
ADMIN = get_permissions("Admin", FULL)


def st(sql, perms=ANALYST):
    return check(sql, perms, FULL).status


# ---- allowed
def test_simple_select_ok():
    assert st("SELECT COUNT(*) FROM orders") == "ok"

def test_join_with_aliases_ok():
    assert st("SELECT c.customer_state, COUNT(*) FROM orders o JOIN customers c "
              "ON o.customer_id = c.customer_id GROUP BY c.customer_state") == "ok"

def test_cte_and_window_ok():
    assert st("WITH m AS (SELECT strftime('%Y-%m', order_purchase_timestamp) AS month, COUNT(*) AS n "
              "FROM orders GROUP BY month) SELECT month, n - LAG(n) OVER (ORDER BY month) AS d FROM m") == "ok"

def test_order_by_alias_ok():
    assert st("SELECT seller_id, SUM(price) AS revenue FROM order_items GROUP BY seller_id ORDER BY revenue DESC") == "ok"

def test_select_star_ok_when_table_fully_allowed():
    assert st("SELECT * FROM orders LIMIT 3") == "ok"

# ---- blocked (security)
def test_forbidden_table():
    assert st("SELECT SUM(payment_value) FROM order_payments") == "blocked"

def test_forbidden_table_via_join():
    assert st("SELECT o.order_id FROM orders o JOIN order_payments p ON o.order_id = p.order_id") == "blocked"

def test_forbidden_column():
    assert st("SELECT customer_unique_id FROM customers") == "blocked"

def test_forbidden_column_qualified():
    assert st("SELECT c.customer_zip_code_prefix FROM customers c") == "blocked"

def test_forbidden_column_hidden_in_alias():
    assert st("SELECT customer_unique_id AS x FROM customers") == "blocked"

def test_forbidden_column_in_where():
    assert st("SELECT COUNT(*) FROM customers WHERE customer_unique_id = 'abc'") == "blocked"

def test_star_on_restricted_table():
    assert st("SELECT * FROM customers") == "blocked"

def test_qualified_star_on_restricted_table():
    assert st("SELECT c.* FROM customers c") == "blocked"

def test_review_text_blocked():
    assert st("SELECT review_comment_message FROM order_reviews") == "blocked"

def test_geolocation_blocked():
    assert st("SELECT geolocation_lat FROM geolocation") == "blocked"

def test_admin_can_see_everything():
    assert st("SELECT customer_unique_id FROM customers", ADMIN) == "ok"
    assert st("SELECT SUM(payment_value) FROM order_payments", ADMIN) == "ok"

# ---- invalid (not security)
def test_unknown_table():
    assert st("SELECT * FROM nonexistent") == "invalid"

def test_unknown_column():
    assert st("SELECT order_date FROM orders") == "invalid"

def test_syntax_error():
    assert st("SELEC COUNT(*) FROM orders") == "invalid"

def test_multiple_statements():
    assert st("SELECT 1; DROP TABLE orders") == "invalid"

def test_write_statements_rejected():
    for s in ("DROP TABLE orders", "DELETE FROM orders", "UPDATE orders SET order_status='x'",
              "INSERT INTO orders VALUES (1)", "PRAGMA table_info(orders)"):
        assert st(s, ADMIN) == "invalid", s

# ---- helpers
def test_extract_sql_from_fence():
    assert extract_sql("Here you go:\n```sql\nSELECT 1;\n```\nDone") == "SELECT 1;"

def test_refusal_detection():
    assert is_refusal("-- UNAUTHORIZED") and is_refusal("  -- unauthorized: payments")
    assert not is_refusal("SELECT 1")

def test_readonly_connection_cannot_write():
    try:
        run_readonly("DELETE FROM orders")
    except Exception:
        return
    raise AssertionError("write succeeded on read-only connection")

def test_row_limit():
    rows, truncated = run_readonly("SELECT * FROM order_items", row_limit=10)
    assert len(rows) == 10 and truncated


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
