#!/usr/bin/env python3
"""Test FastAPI MCP endpoint."""

import json
import os

import httpx

BASE_URL = os.getenv("MCP_BASE_URL", "http://127.0.0.1:8001")
API_KEY = os.getenv("MCP_API_KEY", "your-test-api-key-here")


def test_health():
    """Test health endpoint."""
    r = httpx.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    print("✓ Health check passed")


def mcp_call(method: str, params: dict = None):
    """Make MCP call."""
    payload = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params:
        payload["params"] = params

    r = httpx.post(
        f"{BASE_URL}/mcp/v1/",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json=payload,
    )
    return r.json()


def test_tools_list():
    """Test tools/list."""
    result = mcp_call("tools/list")
    assert "result" in result
    tools = result["result"]["tools"]
    assert len(tools) > 0
    print(f"✓ tools/list returned {len(tools)} tools")


def test_get_context():
    """Test get_context tool."""
    result = mcp_call("tools/call", {"name": "get_context", "arguments": {}})
    assert "result" in result
    content = result["result"]["content"][0]["text"]
    data = json.loads(content)
    assert "account_id" in data
    print(f"✓ get_context - account_id: {data['account_id']}")


def test_workspace_list():
    """Test workspace_list tool."""
    result = mcp_call("tools/call", {"name": "workspace_list", "arguments": {}})
    assert "result" in result
    content = result["result"]["content"][0]["text"]
    data = json.loads(content)
    assert "workspaces" in data
    print(f"✓ workspace_list - {data['count']} workspaces")


def test_account_get():
    """Test account_get tool."""
    result = mcp_call("tools/call", {"name": "account_get", "arguments": {}})
    assert "result" in result
    content = result["result"]["content"][0]["text"]
    data = json.loads(content)
    assert "account_id" in data
    print(f"✓ account_get - {data['name']} (id: {data['account_id']})")


def test_workspace_create():
    """Test workspace_create tool (idempotent)."""
    result = mcp_call(
        "tools/call",
        {"name": "workspace_create", "arguments": {"external_id": "test-fastapi-ws", "name": "Test FastAPI Workspace"}},
    )
    assert "result" in result
    content = result["result"]["content"][0]["text"]
    data = json.loads(content)
    assert "workspace_id" in data
    print(f"✓ workspace_create - created: {data.get('created', 'N/A')}")


def test_invalid_tool():
    """Test calling invalid tool."""
    result = mcp_call("tools/call", {"name": "nonexistent_tool", "arguments": {}})
    assert "error" in result
    print("✓ invalid_tool - error correctly returned")


def test_invalid_api_key():
    """Test invalid API key."""
    r = httpx.post(
        f"{BASE_URL}/mcp/v1/",
        headers={"Authorization": "Bearer invalid_key", "Content-Type": "application/json"},
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
    )
    assert r.status_code == 401
    print("✓ invalid_api_key - rejected with 401")


def main():
    print("=== FastAPI MCP Tests ===\n")

    test_health()
    test_tools_list()
    test_get_context()
    test_workspace_list()
    test_account_get()
    test_workspace_create()
    test_invalid_tool()
    test_invalid_api_key()

    print("\n=== All tests passed! ===")


if __name__ == "__main__":
    main()
