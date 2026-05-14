from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0
);
""".strip()

SEED_PRODUCTS: list[tuple[str, str, float, int]] = [
    ("iphone 15", "electronics", 999.0, 12),
    ("galaxy s24", "electronics", 899.0, 10),
    ("macbook air", "electronics", 1199.0, 7),
    ("dell xps 13", "electronics", 1099.0, 6),
    ("office chair", "furniture", 189.0, 25),
    ("standing desk", "furniture", 399.0, 9),
    ("water bottle", "lifestyle", 19.0, 60),
    ("running shoes", "fashion", 129.0, 18),
    ("phone case", "electronics", 29.0, 40),
    ("wireless earbuds", "electronics", 149.0, 22),
]


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with _connect(db_path) as conn:
        conn.execute(SCHEMA_SQL)
        row = conn.execute("SELECT COUNT(*) AS n FROM products").fetchone()
        if row and row["n"] == 0:
            conn.executemany(
                "INSERT INTO products(name, category, price, stock) VALUES (?, ?, ?, ?)",
                SEED_PRODUCTS,
            )
        conn.commit()


def search_products(query: str, category: str | None = None, limit: int = 10, db_path: str = "data/lab26.db") -> list[dict[str, Any]]:
    if limit <= 0:
        raise ValueError("limit must be > 0")

    name_pattern = f"%{query.strip()}%"
    sql = """
    SELECT id, name, category, price, stock
    FROM products
    WHERE name LIKE ?
      AND (? IS NULL OR category = ?)
    ORDER BY id ASC
    LIMIT ?
    """

    with _connect(db_path) as conn:
        rows = conn.execute(sql, (name_pattern, category, category, limit)).fetchall()

    return [dict(row) for row in rows]


def insert_product(name: str, category: str, price: float, stock: int, db_path: str = "data/lab26.db") -> int:
    if price <= 0:
        raise ValueError("price must be > 0")
    if stock < 0:
        raise ValueError("stock must be >= 0")

    with _connect(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO products(name, category, price, stock) VALUES (?, ?, ?, ?)",
            (name.strip(), category.strip(), price, stock),
        )
        conn.commit()
        return int(cursor.lastrowid)


def aggregate_products(
    group_by: str = "category",
    metric: str = "count",
    db_path: str = "data/lab26.db",
) -> list[dict[str, Any]]:
    if group_by != "category":
        raise ValueError("group_by only supports category")

    metric_sql = {
        "count": "COUNT(*)",
        "total_stock": "SUM(stock)",
        "avg_price": "AVG(price)",
    }.get(metric)

    if metric_sql is None:
        raise ValueError("metric must be one of: count, total_stock, avg_price")

    sql = f"""
    SELECT {group_by} AS grouping_value, {metric_sql} AS metric_value
    FROM products
    GROUP BY {group_by}
    ORDER BY {group_by} ASC
    """

    with _connect(db_path) as conn:
        rows = conn.execute(sql).fetchall()

    return [{"group": row["grouping_value"], "value": row["metric_value"]} for row in rows]


def get_schema() -> str:
    return (
        SCHEMA_SQL
        + "\n\nColumns:\n"
        + "- id: INTEGER PRIMARY KEY AUTOINCREMENT\n"
        + "- name: TEXT NOT NULL\n"
        + "- category: TEXT NOT NULL\n"
        + "- price: REAL NOT NULL\n"
        + "- stock: INTEGER NOT NULL DEFAULT 0"
    )
