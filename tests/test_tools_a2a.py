import pytest

from src.tools.a2a import A2ADebugToolClient


@pytest.mark.asyncio
async def test_a2a_client_get_tools():
    client = A2ADebugToolClient()
    tools = client.get_available_tools()
    assert len(tools) == 1
    assert tools[0].name == "invoke_debug_agent"
    assert "task_description" in tools[0].parameters["required"]


@pytest.mark.asyncio
async def test_a2a_client_call_tool():
    client = A2ADebugToolClient()
    result = await client.call_tool("invoke_debug_agent", {"task_description": "Fix memory leak"})
    assert "DEBUG AGENT REPORT" in result
    assert "Fix memory leak" in result


@pytest.mark.asyncio
async def test_a2a_client_unknown_tool():
    client = A2ADebugToolClient()
    with pytest.raises(ValueError, match="Unknown tool"):
        await client.call_tool("unknown", {})
