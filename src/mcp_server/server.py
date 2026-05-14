from __future__ import annotations

import argparse
import os
from typing import Literal

from fastmcp import FastMCP
from starlette.middleware import Middleware

from .auth import APIKeyAuthMiddleware
from .database import aggregate_products, get_schema, init_db, insert_product, search_products

mcp = FastMCP("Lab26 Products DB")
DB_PATH = os.environ.get("LAB26_DB_PATH", "data/lab26.db")


@mcp.tool(name="search", description="Search products by keyword and optional category")
def search_tool(query: str, category: str | None = None, limit: int = 10) -> list[dict]:
    return search_products(query=query, category=category, limit=limit, db_path=DB_PATH)


@mcp.tool(name="insert", description="Insert a new product into the database")
def insert_tool(name: str, category: str, price: float, stock: int) -> dict:
    product_id = insert_product(name=name, category=category, price=price, stock=stock, db_path=DB_PATH)
    return {"id": product_id, "message": "Product inserted successfully"}


@mcp.tool(name="aggregate", description="Aggregate products by category with selected metric")
def aggregate_tool(
    group_by: Literal["category"] = "category",
    metric: Literal["count", "total_stock", "avg_price"] = "count",
) -> list[dict]:
    return aggregate_products(group_by=group_by, metric=metric, db_path=DB_PATH)


@mcp.resource("db://schema")
def get_db_schema() -> str:
    """Returns the database schema for context."""
    return get_schema()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lab26 MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--auth", action="store_true", help="Enable API key auth for SSE")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    init_db(DB_PATH)

    if args.transport == "sse":
        run_kwargs: dict = {"transport": "sse", "host": args.host, "port": args.port}
        if args.auth:
            api_key = os.environ.get("MCP_API_KEY")
            if not api_key:
                raise ValueError("MCP_API_KEY is required when --auth is enabled")
            run_kwargs["middleware"] = [Middleware(APIKeyAuthMiddleware, expected_api_key=api_key)]
        mcp.run(**run_kwargs)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
