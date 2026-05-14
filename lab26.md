# Lab 26 Report — Build MCP Server

## 1) Build MCP Server
- Framework: FastMCP + Python + uv
- Implemented tools:
  - `search(query, category=None, limit=10)`
  - `insert(name, category, price, stock)`
  - `aggregate(group_by="category", metric="count|total_stock|avg_price")`
- Source: `src/mcp_server/server.py`, `src/mcp_server/database.py`

## 2) Add Resource
- Implemented resource: `db://schema`
- Returns SQL schema + column notes from `get_schema()`.

## 3) Test with MCP Inspector
- Verified in Inspector:
  - Tool list and schemas
  - `search` success
  - `insert` success
  - `insert` error (`price=-1`) returns MCP error, server does not crash
  - `aggregate(metric="avg_price")` success
  - Resource `db://schema` readable
- Evidence screenshots:
  - `screenshots/01-tool-list.png`
  - `screenshots/02-search-schema-result.png`
  - `screenshots/03-insert-success.png`
  - `screenshots/04-insert-error.png`
  - `screenshots/05-aggregate-result.png`
  - `screenshots/06-resource-schema.png`

## 4) Claude Desktop
- Skipped per latest requirement (no Claude Desktop E2E for this submission).

## Bonus) SSE Auth
- Added API key middleware for SSE mode:
  - command: `MCP_API_KEY=secret123 make run-sse-auth`
  - missing/invalid bearer token -> `401`
  - valid token -> `200` + SSE stream

## Additional Artifacts
- `README.md`: setup, tools table, screenshots, Claude config, bonus auth
- `PLAN.md`: original implementation plan
