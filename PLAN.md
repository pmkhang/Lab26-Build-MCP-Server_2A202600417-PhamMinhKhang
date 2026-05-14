# Lab 26 — Build MCP Server: Implementation Plan

## Tổng quan

Xây dựng MCP (Model Context Protocol) Server sử dụng **FastMCP** + **Python** + **uv**, expose 3 tools (search, insert, aggregate) và 1 resource (schema) cho database. Test với MCP Inspector và tích hợp Claude Desktop.

---

## Tech Stack

| Thành phần | Lựa chọn |
|---|---|
| Package manager | `uv` |
| MCP framework | `fastmcp` |
| Database | SQLite (local, zero-config) |
| Transport | stdio (default) + SSE (bonus) |
| Test tool | MCP Inspector (`npx @modelcontextprotocol/inspector`) |
| Build automation | `Makefile` |

---

## Cấu trúc thư mục

```
Lab26-Build-MCP-Servicer_2A202600417-PhamMinhKhang/
├── Makefile
├── PLAN.md
├── README.md
├── lab26.md
├── pyproject.toml          # uv project config
├── uv.lock
├── .python-version         # pin python version
├── data/
│   └── lab26.db            # SQLite database (auto-created)
├── src/
│   └── mcp_server/
│       ├── __init__.py
│       ├── server.py       # FastMCP app + tool/resource definitions
│       ├── database.py     # DB init, connection, CRUD helpers
│       └── auth.py         # (Bonus) SSE auth middleware
├── tests/
│   └── test_tools.py       # Unit tests cho 3 tools
└── screenshots/            # Inspector screenshots cho README
```

---

## Bước 1 — Khởi tạo project với uv

### 1.1 Init project

```bash
uv init .
uv python pin 3.12
```

### 1.2 Thêm dependencies vào `pyproject.toml`

```toml
[project]
name = "lab26-mcp-server"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastmcp>=2.0",
    "aiosqlite>=0.20",
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-asyncio>=0.24"]

[project.scripts]
mcp-server = "mcp_server.server:main"
```

### 1.3 Cài dependencies

```bash
uv sync
uv sync --extra dev  # cho test
```

---

## Bước 2 — Database Layer (`src/mcp_server/database.py`)

### Schema

Dùng bảng `products` đơn giản để demo đủ 3 operations:

```sql
CREATE TABLE IF NOT EXISTS products (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT    NOT NULL,
    category TEXT   NOT NULL,
    price   REAL    NOT NULL,
    stock   INTEGER NOT NULL DEFAULT 0
);
```

### Functions cần implement

| Function | Mô tả |
|---|---|
| `init_db(db_path)` | Tạo DB + bảng nếu chưa có, seed sample data |
| `search_products(query, category, limit)` | Full-text search theo name/category |
| `insert_product(name, category, price, stock)` | Insert 1 record, trả về id |
| `aggregate_products(group_by, metric)` | GROUP BY + COUNT/SUM/AVG |
| `get_schema()` | Trả về schema string cho resource |

---

## Bước 3 — MCP Server (`src/mcp_server/server.py`)

### 3.1 Khởi tạo FastMCP app

```python
from fastmcp import FastMCP
mcp = FastMCP("Lab26 Products DB")
```

### 3.2 Tool 1: `search`

**Mục đích**: Tìm kiếm sản phẩm theo từ khóa và/hoặc category.

```
Tool name: search
Input:
  - query: str — từ khóa tìm kiếm (tên sản phẩm)
  - category: str | None — lọc theo category (optional)
  - limit: int = 10 — số kết quả tối đa
Output: list[dict] — danh sách sản phẩm khớp
```

**Logic**: `SELECT * FROM products WHERE name LIKE ? AND (category = ? OR ? IS NULL) LIMIT ?`

### 3.3 Tool 2: `insert`

**Mục đích**: Thêm sản phẩm mới vào database.

```
Tool name: insert
Input:
  - name: str
  - category: str
  - price: float (> 0)
  - stock: int (>= 0)
Output: dict — { "id": int, "message": str }
```

**Logic**: Validate input → INSERT → trả về id mới.  
**Error handling**: Raise `ValueError` nếu price <= 0 hoặc stock < 0 → FastMCP tự convert thành MCP error response.

### 3.4 Tool 3: `aggregate`

**Mục đích**: Thống kê tổng hợp theo nhóm.

```
Tool name: aggregate
Input:
  - group_by: Literal["category"] = "category"
  - metric: Literal["count", "total_stock", "avg_price"] = "count"
Output: list[dict] — [{ "group": str, "value": number }]
```

**Logic**: Dynamic SQL với GROUP BY, chọn aggregate function theo `metric`.

### 3.5 Resource: `db://schema`

**Mục đích**: Expose database schema để LLM hiểu cấu trúc dữ liệu trước khi gọi tools.

```python
@mcp.resource("db://schema")
def get_db_schema() -> str:
    """Returns the database schema for context."""
    return get_schema()
```

Output: chuỗi SQL CREATE TABLE statement + mô tả các cột.

### 3.6 Entry point

```python
def main():
    init_db("data/lab26.db")
    mcp.run()  # stdio transport mặc định

if __name__ == "__main__":
    main()
```

---

## Bước 4 — Makefile

```makefile
.PHONY: install run test inspect clean

install:
	uv sync --extra dev

run:
	uv run mcp-server

test:
	uv run pytest tests/ -v

inspect:
	npx @modelcontextprotocol/inspector uv run mcp-server

clean:
	rm -f data/lab26.db
	rm -rf .venv __pycache__ src/**/__pycache__
```

---

## Bước 5 — Test với MCP Inspector

### 5.1 Chạy Inspector

```bash
make inspect
# hoặc
npx @modelcontextprotocol/inspector uv run mcp-server
```

### 5.2 Checklist verify

- [ ] **Tool schemas**: 3 tools hiện đúng tên, description, input schema (types, required fields)
- [ ] **Resource**: `db://schema` accessible, trả về schema string
- [ ] **Test `search`**: gọi với `query="phone"` → trả về list sản phẩm
- [ ] **Test `insert`**: gọi với data hợp lệ → trả về `{"id": N, "message": "..."}`
- [ ] **Test `insert` lỗi**: `price=-1` → trả về MCP error response (không crash server)
- [ ] **Test `aggregate`**: `metric="avg_price"` → trả về list `[{group, value}]`

### 5.3 Screenshots cần chụp (cho README)

1. Tool list panel — hiển thị 3 tools
2. `search` tool schema + sample call result
3. `insert` tool — success response
4. `insert` tool — error response (validation fail)
5. `aggregate` tool result
6. Resource `db://schema` content

---

## Bước 6 — Claude Desktop Integration

### 6.1 Config file

Thêm vào `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) hoặc `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "lab26-products": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/absolute/path/to/Lab26-Build-MCP-Servicer_2A202600417-PhamMinhKhang",
        "mcp-server"
      ]
    }
  }
}
```

### 6.2 E2E Test scenarios (cho demo video 2 phút)

| Scenario | Prompt mẫu | Expected |
|---|---|---|
| Schema context | "What tables are in the database?" | Claude đọc resource `db://schema`, mô tả bảng products |
| Search | "Find all electronics products" | Claude gọi `search(category="electronics")` |
| Insert | "Add a new laptop: $999, 5 in stock" | Claude gọi `insert(name="laptop", ...)` |
| Aggregate | "Show me average price by category" | Claude gọi `aggregate(metric="avg_price")` |
| Multi-tool | "Insert a phone then show category stats" | Claude gọi `insert` rồi `aggregate` tuần tự |

### 6.3 Demo video script (2 phút)

```
0:00-0:20  Giới thiệu: mở Claude Desktop, show MCP server connected
0:20-0:45  Demo search + schema context
0:45-1:10  Demo insert (success + error case)
1:10-1:35  Demo aggregate
1:35-2:00  Demo multi-tool routing (insert → aggregate)
```

---

## Bước 7 — (Bonus) Auth cho SSE Transport

### 7.1 Thêm dependency

```toml
dependencies = [
    ...
    "starlette>=0.40",
    "python-jose[cryptography]>=3.3",
]
```

### 7.2 Cơ chế

- SSE transport expose HTTP endpoint
- Middleware kiểm tra `Authorization: Bearer <token>` header
- Token là static API key (đơn giản) hoặc JWT
- Nếu thiếu/sai token → trả về `401 Unauthorized`

### 7.3 Chạy với SSE

```bash
uv run python -m mcp_server.server --transport sse --port 8000
```

Thêm vào Makefile:

```makefile
run-sse:
	uv run python -m mcp_server.server --transport sse --port 8000

run-sse-auth:
	MCP_API_KEY=secret123 uv run python -m mcp_server.server --transport sse --port 8000 --auth
```

---

## Bước 8 — README.md

Nội dung README cần có:

1. **Mô tả project** — Lab 26, MCP server cho Products DB
2. **Setup** — `git clone` → `make install` → `make run`
3. **Tool descriptions** — bảng mô tả 3 tools + resource
4. **Inspector screenshots** — 6 ảnh từ bước 5.3
5. **Claude Desktop config** — JSON snippet
6. **Demo video** — link YouTube/Google Drive (2 phút)
7. **(Bonus)** Auth setup instructions

---

## Thứ tự implement

```
1. uv init + pyproject.toml          (5 phút)
2. database.py                        (15 phút)
3. server.py (3 tools + 1 resource)  (20 phút)
4. Makefile                           (5 phút)
5. make inspect + chụp screenshots   (15 phút)
6. Claude Desktop config + E2E test  (15 phút)
7. Quay demo video 2 phút            (10 phút)
8. README.md                          (10 phút)
9. (Bonus) auth.py + SSE             (20 phút)
```

**Tổng**: ~1.5–2 giờ (không tính bonus)

---

## Lưu ý quan trọng

- `uv run` tự activate venv → không cần `source .venv/bin/activate`
- FastMCP tự generate JSON Schema từ Python type hints → dùng đúng types
- MCP error response: raise exception trong tool → FastMCP handle, server không crash
- `db://schema` resource phải trả về string (không phải dict)
- Claude Desktop cần **absolute path** trong config JSON
- Seed ít nhất 10 sample records để demo aggregate có ý nghĩa
