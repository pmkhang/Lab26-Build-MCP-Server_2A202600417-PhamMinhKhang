.PHONY: install run run-sse run-sse-auth test inspect clean

install:
	uv sync --extra dev

run:
	uv run mcp-server

run-sse:
	uv run python -m mcp_server.server --transport sse --port 8000

run-sse-auth:
	MCP_API_KEY=secret123 uv run python -m mcp_server.server --transport sse --port 8000 --auth

test:
	uv run pytest tests/ -v

inspect:
	npx @modelcontextprotocol/inspector uv run mcp-server

clean:
	rm -f data/lab26.db
	rm -rf .venv __pycache__ .pytest_cache src/**/__pycache__ tests/**/__pycache__
