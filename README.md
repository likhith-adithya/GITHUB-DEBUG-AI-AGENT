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

*   **`src/main.py`**: The main entry point and orchestration layer for the application. It initializes the LLM client, GitHub client, and the `AIEngineerAgent`, and manages the primary interactive loop for user queries.
*   **`src/cli/`**: Contains command-line interface related components.
    *   `menu.py`: Manages the interactive menu for configuring the LLM provider and model, guiding the user through selection based on available credentials.
*   **`src/config/`**: Houses configuration settings for the application.
    *   `settings.py`: Defines application settings, primarily loaded from environment variables (e.g., LLM API keys, model names, GitHub token).
*   **`src/core/`**: Contains the core logic and components of the AI agent.
    *   `agent.py`: Implements the `AIEngineerAgent`, responsible for managing the AI's behavior, processing user queries, and delegating tasks to tools.
    *   `llm.py`: Manages the connection and interaction with various Language Model (LLM) providers, handling model selection and API calls.
    *   `worker.py`: Defines the `DebugWorkerAgent`, a specialized autonomous agent designed to operate within a sandbox to solve specific debugging tasks.
*   **`src/tools/`**: Defines the various tools the AI agent can utilize.
    *   `a2a.py`: Implements the Agent-to-Agent (A2A) Debug Tool Client, enabling the primary agent to delegate complex debugging tasks to `DebugWorkerAgent` instances.
    *   `base.py`: Provides base classes and common utilities for other tool clients.
    *   `github.py`: Implements the `GitHubClient` for interacting with the GitHub API (e.g., reading repository content, fetching file details).
    *   `sandbox.py`: Implements the `SandboxToolClient`, providing sandboxed filesystem access (read/write/list) and command execution for safe operation by the `DebugWorkerAgent).

## 🤝 Contributing

Contributions are welcome! Please read through our contributing guidelines. Included are steps for running tests:

```bash
uv run pytest tests/
```

## 📄 License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.
