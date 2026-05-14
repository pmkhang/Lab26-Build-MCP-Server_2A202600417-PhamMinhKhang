from __future__ import annotations

import os
from pathlib import Path

from mcp_server.database import aggregate_products, init_db, insert_product, search_products


def _test_db_path(tmp_path: Path) -> str:
    return str(tmp_path / "lab26_test.db")


def test_search_products(tmp_path: Path):
    db_path = _test_db_path(tmp_path)
    init_db(db_path)

    results = search_products(query="phone", db_path=db_path)
    assert isinstance(results, list)
    assert any("phone" in item["name"] for item in results)


def test_insert_product_success(tmp_path: Path):
    db_path = _test_db_path(tmp_path)
    init_db(db_path)

    new_id = insert_product(
        name="gaming mouse",
        category="electronics",
        price=59.0,
        stock=14,
        db_path=db_path,
    )
    assert isinstance(new_id, int)
    assert new_id > 0


def test_insert_product_validation_error(tmp_path: Path):
    db_path = _test_db_path(tmp_path)
    init_db(db_path)

    try:
        insert_product(
            name="bad product",
            category="electronics",
            price=-1,
            stock=0,
            db_path=db_path,
        )
    except ValueError as exc:
        assert "price" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid price")


def test_aggregate_avg_price(tmp_path: Path):
    db_path = _test_db_path(tmp_path)
    init_db(db_path)

    results = aggregate_products(group_by="category", metric="avg_price", db_path=db_path)
    assert isinstance(results, list)
    assert len(results) > 0
    assert all("group" in row and "value" in row for row in results)
