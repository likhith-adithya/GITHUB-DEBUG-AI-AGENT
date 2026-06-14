"""Unit tests for the A2A (Agent-to-Agent) Debug Tool Client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tools.a2a import A2ADebugToolClient


@pytest.mark.asyncio
async def test_a2a_client_get_tools():
    """Verify that get_available_tools returns correct tool definitions."""
    client = A2ADebugToolClient()
    tools = client.get_available_tools()
    assert len(tools) == 1
    assert tools[0].name == "invoke_debug_agent"
    assert "owner" in tools[0].parameters["required"]
    assert "repo" in tools[0].parameters["required"]
    assert "task_description" in tools[0].parameters["required"]


@pytest.mark.asyncio
async def test_a2a_client_unknown_tool():
    """Verify that calling an unknown tool raises ValueError."""
    client = A2ADebugToolClient()
    with pytest.raises(ValueError, match="Unknown tool"):
        await client.call_tool("unknown", {})


@pytest.mark.asyncio
async def test_a2a_client_call_tool_success():
    """Verify that call_tool successfully executes and handles git cloning/worker loops."""
    client = A2ADebugToolClient()

    # Mock subprocess to simulate successful git clone
    mock_proc = AsyncMock()
    mock_proc.returncode = 0
    mock_proc.communicate.return_value = (b"", b"")

    # Mock LLM response to simulate the worker agent generating a report
    mock_response = MagicMock()
    mock_response.tool_calls = []
    mock_response.content = "Solved the bug in main.py"

    # Mock LLMClient.generate_response
    with (
        patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_clone,
        patch("src.tools.a2a.LLMClient") as mock_llm_class,
        patch("os.makedirs"),
        patch("shutil.rmtree"),
        patch("os.path.exists", return_value=True),
    ):
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate_response = AsyncMock(return_value=mock_response)
        mock_llm_class.return_value = mock_llm_instance

        result = await client.call_tool(
            "invoke_debug_agent",
            {"owner": "octocat", "repo": "hello-world", "task_description": "Fix memory leak"},
        )

        # Verify result contains the expected diagnostic report from sub-agent
        assert "DEBUG AGENT REPORT" in result
        assert "Solved the bug in main.py" in result

        # Verify clone was called with correct parameters
        mock_clone.assert_called_once()
        args, _ = mock_clone.call_args
        assert args[0] == "git"
        assert args[1] == "clone"
        assert "github.com/octocat/hello-world.git" in args[4]
