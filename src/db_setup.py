"""Step 1: load the Olist CSVs into a SQLite database.

Usage:  python src/db_setup.py
Reads   data/raw/*.csv
Writes  data/olist.db
"""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "olist.db"

# table name -> (csv file, columns forced to TEXT so leading zeros survive)
TABLES = {
    "customers": ("olist_customers_dataset.csv", ["customer_zip_code_prefix"]),
    "sellers": ("olist_sellers_dataset.csv", ["seller_zip_code_prefix"]),
    "geolocation": ("olist_geolocation_dataset.csv", ["geolocation_zip_code_prefix"]),
    "orders": ("olist_orders_dataset.csv", []),
    "order_items": ("olist_order_items_dataset.csv", []),
    "order_payments": ("olist_order_payments_dataset.csv", []),
    "order_reviews": ("olist_order_reviews_dataset.csv", []),
    "products": ("olist_products_dataset.csv", []),
    "product_category_name_translation": ("product_category_name_translation.csv", []),
}

INDEXES = [
    "CREATE INDEX idx_orders_customer ON orders(customer_id)",
    "CREATE INDEX idx_orders_purchase ON orders(order_purchase_timestamp)",
    "CREATE INDEX idx_items_order ON order_items(order_id)",
    "CREATE INDEX idx_items_product ON order_items(product_id)",
    "CREATE INDEX idx_items_seller ON order_items(seller_id)",
    "CREATE INDEX idx_pay_order ON order_payments(order_id)",
    "CREATE INDEX idx_rev_order ON order_reviews(order_id)",
    "CREATE INDEX idx_prod_cat ON products(product_category_name)",
    "CREATE INDEX idx_cust_state ON customers(customer_state)",
    "CREATE INDEX idx_geo_zip ON geolocation(geolocation_zip_code_prefix)",
]


def load_all() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = sqlite3.connect(DB_PATH)
    for table, (csv_name, text_cols) in TABLES.items():
        path = RAW / csv_name
        if not path.exists():
            raise FileNotFoundError(f"Missing {path}")
        dtype = {c: str for c in text_cols}
        # utf-8-sig strips the BOM present in the category translation file
        df = pd.read_csv(path, dtype=dtype, encoding="utf-8-sig")
        df.columns = [c.strip().lstrip("﻿") for c in df.columns]
        df.to_sql(table, con, index=False, if_exists="replace")
        print(f"{table:40s} {len(df):>9,d} rows")
    for stmt in INDEXES:
        con.execute(stmt)
    con.commit()
    con.close()
    print(f"\nWrote {DB_PATH}")


def get_full_schema(db_path: Path = DB_PATH) -> dict:
    """Return {table: [(column, type), ...]} via PRAGMA table_info."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    schema = {t: [(r[1], r[2]) for r in con.execute(f"PRAGMA table_info({t})")]
              for t in tables}
    con.close()
    return schema


if __name__ == "__main__":
    load_all()
