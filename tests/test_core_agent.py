import pytest
from unittest.mock import MagicMock, AsyncMock
from src.core.agent import AIEngineerAgent, MAX_TOOL_RESULT_CHARS
from src.tools.base import ToolDefinition


def test_ai_engineer_agent_init():
    mock_llm = MagicMock()
    mock_github = MagicMock()
    agent = AIEngineerAgent(llm_client=mock_llm, tools_clients=[mock_github])
    assert agent.llm is not None
    assert agent.tools_clients is not None
    assert len(agent.tools_clients) == 1


def test_build_tools_list():
    """_build_tools_list should convert ToolDefinitions to OpenAI format."""
    mock_llm = MagicMock()
    mock_github = MagicMock()
    agent = AIEngineerAgent(llm_client=mock_llm, tools_clients=[mock_github])
    
    mock_github.get_available_tools.return_value = [
        ToolDefinition(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {"arg": {"type": "string"}}, "required": ["arg"]}
        )
    ]
    
    tools = agent._build_tools_list()
    assert len(tools) == 1
    assert tools[0]["type"] == "function"
    assert tools[0]["function"]["name"] == "test_tool"
    assert tools[0]["function"]["description"] == "A test tool"
    assert tools[0]["function"]["parameters"]["type"] == "object"
    assert "arg" in tools[0]["function"]["parameters"]["properties"]
    assert "arg" in tools[0]["function"]["parameters"]["required"]


def test_build_tools_list_empty():
    """Empty tool list should return empty list."""
    mock_llm = MagicMock()
    mock_github = MagicMock()
    agent = AIEngineerAgent(llm_client=mock_llm, tools_clients=[mock_github])
    mock_github.get_available_tools.return_value = []
    assert agent._build_tools_list() == []


def test_truncate_result_short():
    """Short results should not be truncated."""
    mock_llm = MagicMock()
    mock_github = MagicMock()
    agent = AIEngineerAgent(llm_client=mock_llm, tools_clients=[mock_github])
    text = "short text"
    assert agent._truncate_result(text) == text


def test_truncate_result_long():
    """Long results should be truncated with a message."""
    mock_llm = MagicMock()
    mock_github = MagicMock()
    agent = AIEngineerAgent(llm_client=mock_llm, tools_clients=[mock_github])
    text = "x" * (MAX_TOOL_RESULT_CHARS + 1000)
    result = agent._truncate_result(text)
    assert len(result) < len(text)
    assert "TRUNCATED" in result
    assert "1000 characters" in result


def test_response_to_dict_no_tool_calls():
    """Response without tool calls should only have role and content."""
    mock_llm = MagicMock()
    mock_github = MagicMock()
    agent = AIEngineerAgent(llm_client=mock_llm, tools_clients=[mock_github])
    response = MagicMock()
    response.content = "Hello world"
    response.tool_calls = None
    
    result = agent._response_to_dict(response)
    assert result == {"role": "assistant", "content": "Hello world"}
    assert "tool_calls" not in result


def test_response_to_dict_with_tool_calls():
    """Response with tool calls should be properly serialized."""
    mock_llm = MagicMock()
    mock_github = MagicMock()
    agent = AIEngineerAgent(llm_client=mock_llm, tools_clients=[mock_github])
    
    mock_tc = MagicMock()
    mock_tc.id = "call_123"
    mock_tc.function.name = "search"
    mock_tc.function.arguments = '{"query": "test"}'
    
    response = MagicMock()
    response.content = None
    response.tool_calls = [mock_tc]
    
    result = agent._response_to_dict(response)
    assert result["role"] == "assistant"
    assert result["content"] == ""  # None should become ""
    assert len(result["tool_calls"]) == 1
    assert result["tool_calls"][0]["id"] == "call_123"
    assert result["tool_calls"][0]["type"] == "function"
    assert result["tool_calls"][0]["function"]["name"] == "search"
    assert result["tool_calls"][0]["function"]["arguments"] == '{"query": "test"}'
