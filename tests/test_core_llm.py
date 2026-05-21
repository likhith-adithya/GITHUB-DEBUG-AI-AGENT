from unittest.mock import AsyncMock, patch

import pytest

from src.core.llm import LLMClient


@pytest.fixture
def mock_openai_env(monkeypatch):
    """Set up env for OpenAI provider."""
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("API_KEY", "test_key")
    monkeypatch.setenv("MODEL_NAME", "gpt-4o")


@pytest.fixture
def mock_ollama_env(monkeypatch):
    """Set up env for Ollama provider."""
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5:7b")


@patch("src.core.llm.AsyncOpenAI")
def test_llm_client_init_openai(mock_async_openai, mock_openai_env):
    client = LLMClient()
    assert client.provider == "openai"
    assert client.model == "gpt-4o"
    mock_async_openai.assert_called_once_with(api_key="test_key", base_url=None)


@patch("src.core.llm.AsyncOpenAI")
def test_llm_client_init_vllm(mock_async_openai, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "vllm")
    monkeypatch.setenv("VLLM_API_URL", "http://test:8000/v1")
    monkeypatch.setenv("VLLM_MODEL", "meta-llama/test")

    client = LLMClient()
    assert client.provider == "vllm"
    assert client.model == "meta-llama/test"
    mock_async_openai.assert_called_once_with(api_key="EMPTY", base_url="http://test:8000/v1")


@patch("src.core.llm.AsyncOpenAI")
def test_llm_client_init_ollama(mock_async_openai, mock_ollama_env):
    client = LLMClient()
    assert client.provider == "ollama"
    assert client.model == "qwen2.5:7b"
    mock_async_openai.assert_called_once_with(
        api_key="ollama", base_url="http://localhost:11434/v1"
    )


@patch("src.core.llm.AsyncOpenAI")
def test_llm_client_init_huggingface2(mock_async_openai, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "huggingface")
    monkeypatch.setenv("HF_API_KEY", "hf_test")

    client = LLMClient()
    assert client.provider == "huggingface"
    assert client.model == "Meta-Llama-3.3-70B-Instruct"
    mock_async_openai.assert_called_once_with(
        api_key="hf_test", base_url="https://router.huggingface.co/sambanova/v1"
    )


@patch("src.core.llm.AsyncOpenAI")
def test_llm_client_init_openrouter(mock_async_openai, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")

    client = LLMClient()
    assert client.provider == "openrouter"
    assert client.model == "meta-llama/llama-3.3-70b-instruct"
    mock_async_openai.assert_called_once_with(
        api_key="sk-or-test", base_url="https://openrouter.ai/api/v1"
    )


@patch("src.core.llm.AsyncOpenAI")
def test_llm_client_init_google(mock_async_openai, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "google")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini_test_key")

    client = LLMClient()
    assert client.provider == "google"
    assert client.model == "gemini-2.0-flash"
    mock_async_openai.assert_called_once_with(
        api_key="gemini_test_key",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )


@patch("src.core.llm.AsyncOpenAI")
def test_llm_client_init_huggingface(mock_async_openai, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "huggingface")
    monkeypatch.setenv("HF_API_KEY", "hf_test")

    client = LLMClient()
    assert client.provider == "huggingface"
    assert client.model == "Meta-Llama-3.3-70B-Instruct"
    mock_async_openai.assert_called_once_with(
        api_key="hf_test", base_url="https://router.huggingface.co/sambanova/v1"
    )


def test_llm_client_openai_requires_api_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("API_KEY", raising=False)
    with pytest.raises(ValueError, match="API_KEY"):
        LLMClient()


def test_llm_client_huggingface_requires_api_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "huggingface")
    monkeypatch.delenv("HF_API_KEY", raising=False)
    monkeypatch.delenv("API_KEY", raising=False)
    with pytest.raises(ValueError, match="HF_API_KEY"):
        LLMClient()


def test_llm_client_google_requires_api_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "google")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("API_KEY", raising=False)
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        LLMClient()


@pytest.mark.asyncio
@patch("src.core.llm.AsyncOpenAI")
async def test_generate_response(mock_async_openai, mock_openai_env):
    # Setup mock
    mock_instance = mock_async_openai.return_value
    mock_choice = AsyncMock()
    mock_choice.message = "test_response"
    mock_response = AsyncMock()
    mock_response.choices = [mock_choice]

    mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)

    client = LLMClient()
    messages = [{"role": "user", "content": "hello"}]
    tools = [{"type": "function", "function": {"name": "test"}}]

    res = await client.generate_response(messages, tools=tools)

    assert res == "test_response"
    mock_instance.chat.completions.create.assert_called_once_with(
        model="gpt-4o", messages=messages, temperature=0.1, tools=tools
    )


@pytest.mark.asyncio
@patch("src.core.llm.AsyncOpenAI")
async def test_generate_response_ollama_sets_tool_choice(mock_async_openai, mock_ollama_env):
    """Ollama should set tool_choice='auto' when tools are provided."""
    mock_instance = mock_async_openai.return_value
    mock_choice = AsyncMock()
    mock_choice.message = "test"
    mock_response = AsyncMock()
    mock_response.choices = [mock_choice]
    mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)

    client = LLMClient()
    tools = [{"type": "function", "function": {"name": "test"}}]

    await client.generate_response([{"role": "user", "content": "hi"}], tools=tools)

    call_kwargs = mock_instance.chat.completions.create.call_args[1]
    assert call_kwargs["tool_choice"] == "auto"


@pytest.mark.asyncio
@patch("src.core.llm.AsyncOpenAI")
async def test_generate_response_no_tools(mock_async_openai, mock_openai_env):
    """When no tools are passed, tools and tool_choice should not be in kwargs."""
    mock_instance = mock_async_openai.return_value
    mock_choice = AsyncMock()
    mock_choice.message = "test"
    mock_response = AsyncMock()
    mock_response.choices = [mock_choice]
    mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)

    client = LLMClient()

    await client.generate_response([{"role": "user", "content": "hi"}])

    call_kwargs = mock_instance.chat.completions.create.call_args[1]
    assert "tools" not in call_kwargs
    assert "tool_choice" not in call_kwargs
