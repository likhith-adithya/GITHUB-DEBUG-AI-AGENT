from unittest.mock import AsyncMock, MagicMock

import pytest

from src.tools.github import GITHUB_TOOLS, GitHubClient, ToolDefinition


def test_github_client_requires_token(monkeypatch):
    """Client must raise ValueError when GitHub token is missing."""
    monkeypatch.delenv("GITHUB_PERSONAL_ACCESS_TOKEN", raising=False)
    with pytest.raises(ValueError, match="GITHUB_PERSONAL_ACCESS_TOKEN"):
        GitHubClient()


def test_github_client_init(monkeypatch):
    """Client should initialize correctly with a valid token."""
    monkeypatch.setenv("GITHUB_PERSONAL_ACCESS_TOKEN", "fake_token")
    client = GitHubClient()
    assert client.github_token == "fake_token"
    assert client._client is not None


def test_get_available_tools(monkeypatch):
    """get_available_tools should return the full list of tools."""
    monkeypatch.setenv("GITHUB_PERSONAL_ACCESS_TOKEN", "fake_token")
    client = GitHubClient()
    tools = client.get_available_tools()
    assert isinstance(tools, list)
    assert len(tools) == len(GITHUB_TOOLS)
    for tool in tools:
        assert isinstance(tool, ToolDefinition)
        assert tool.name
        assert tool.description
        assert "type" in tool.parameters


def test_tool_names(monkeypatch):
    """All expected tools should be registered."""
    monkeypatch.setenv("GITHUB_PERSONAL_ACCESS_TOKEN", "fake_token")
    client = GitHubClient()
    tool_names = [t.name for t in client.get_available_tools()]
    expected = [
        "search_repositories",
        "get_file_contents",
        "list_repository_files",
        "search_code",
        "list_issues",
        "get_issue",
        "list_commits",
        "get_repository_info",
    ]
    for name in expected:
        assert name in tool_names, f"Missing tool: {name}"


@pytest.mark.asyncio
async def test_call_tool_unknown(monkeypatch):
    """Calling an unknown tool should return an error message, not crash."""
    monkeypatch.setenv("GITHUB_PERSONAL_ACCESS_TOKEN", "fake_token")
    client = GitHubClient()
    result = await client.call_tool("nonexistent_tool", {})
    assert "Unknown tool" in result


@pytest.mark.asyncio
async def test_call_tool_dispatches(monkeypatch):
    """call_tool should dispatch to the correct handler method."""
    monkeypatch.setenv("GITHUB_PERSONAL_ACCESS_TOKEN", "fake_token")
    client = GitHubClient()

    # Mock the internal handler
    client._tool_search_repositories = AsyncMock(return_value="mocked result")

    result = await client.call_tool("search_repositories", {"query": "test"})
    assert result == "mocked result"
    client._tool_search_repositories.assert_called_once_with(query="test")


@pytest.mark.asyncio
async def test_connect_success(monkeypatch):
    """connect() should verify token by calling /user."""
    monkeypatch.setenv("GITHUB_PERSONAL_ACCESS_TOKEN", "fake_token")
    client = GitHubClient()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"login": "testuser"}

    client._client.get = AsyncMock(return_value=mock_response)
    await client.connect()
    client._client.get.assert_called_once_with("/user")


@pytest.mark.asyncio
async def test_connect_invalid_token(monkeypatch):
    """connect() should raise on invalid token."""
    monkeypatch.setenv("GITHUB_PERSONAL_ACCESS_TOKEN", "bad_token")
    client = GitHubClient()

    mock_response = MagicMock()
    mock_response.status_code = 401

    client._client.get = AsyncMock(return_value=mock_response)
    with pytest.raises(ValueError, match="invalid or expired"):
        await client.connect()


@pytest.mark.asyncio
async def test_disconnect(monkeypatch):
    """disconnect() should close the HTTP client."""
    monkeypatch.setenv("GITHUB_PERSONAL_ACCESS_TOKEN", "fake_token")
    client = GitHubClient()
    client._client.aclose = AsyncMock()
    await client.disconnect()
    client._client.aclose.assert_called_once()
