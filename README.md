# DEBUG AI AGENT

**Disclaimer:** This is not an officially supported Google product.

The **DEBUG AI AGENT** is an intelligent, multi-agent orchestration system powered by the [Google Agent Development Kit (ADK)](https://github.com/google/agent-development-kit). It is designed to interactively explore, secure, and debug public GitHub repositories alongside the developer.

Acting as an "Elite AI Software Architect," the primary agent scans repositories, highlights structural areas of interest, and delegates complex debugging traces to a highly specialized, secondary Agent-to-Agent (A2A) protocol.

## 🌟 Key Features

*   **Interactive Exploration**: Provides a targeted overview of project structures rather than blindly consuming entire codebases, ensuring you're in control of what gets analyzed.
*   **Agent-to-Agent (A2A) Architecture**: Heavy, deep-dive debugging and execution tracing are seamlessly delegated to specialized sub-agents (`invoke_debug_agent`), allowing the primary node to remain responsive.
*   **Flexible AI Provider Configurations**: Connects directly to a variety of Cloud AI providers (Gemini, OpenAI, HuggingFace, OpenRouter) or runs entirely locally (Ollama, vLLM) for enhanced privacy and zero-cost operation.
*   **Rapid Development**: Uses `uv` for lightning-fast environment resolution and dependency management.

## 🚀 Getting Started

### Prerequisites

*   **Python 3.12+**
*   **uv**: The modern Python package installer and resolver.
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

### Installation

1. Clone setup and change directories into the project root.
2. Ensure you have the required credentials in your `.env` file or have a local model running. See [CONFIGURATION.md](CONFIGURATION.md) for detailed AI engine setups.
3. Automatically configure environments and start the agent:
    ```bash
    ./run.sh
    ```

## 📚 Project Structure

The codebase is organized in `src/`, following modern asynchronous design principles:

*   **`src/main.py`**: The application's CLI interface and orchestration layer, managing the lifecycle of the `AIEngineerAgent`.
*   **`src/core/`**: Houses the `llm.py` connection manager and `agent.py`, containing the primary interactive AI loops.
*   **`src/tools/`**: Tool definitions, including the `GitHubClient` and the `A2ADebugToolClient` which implements agent task passing.

## 🤝 Contributing

Contributions are welcome! Please read through our contributing guidelines. Included are steps for running tests:

```bash
uv run pytest tests/
```

## 📄 License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.
