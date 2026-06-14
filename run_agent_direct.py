"""Direct test runner for the AI Debug Agent with full A2A pipeline execution."""

import asyncio
import sys

from src.core.agent import AIEngineerAgent
from src.core.llm import LLMClient
from src.tools.a2a import A2ADebugToolClient
from src.tools.github import GitHubClient


async def main():
    """Initialize and run the primary agent with a real A2A debug delegation query."""
    print("Starting direct agent query test...")

    # 1. Initialize Clientste
    
    try:
        llm_client = LLMClient()
        github_client = GitHubClient()
        a2a_client = A2ADebugToolClient()
    except (ValueError, RuntimeError) as e:
        print(f"Initialization failure: {e}")
        sys.exit(1)

    # 2. Instantiate Agent
    agent = AIEngineerAgent(
        llm_client=llm_client, tools_clients=[github_client, a2a_client]
    )

    # 3. Setup Agent
    print("Connecting to tool APIs...")
    try:
        await agent.setup()
    except (ValueError, RuntimeError) as e:
        print(f"Setup failure: {e}")
        sys.exit(1)

    # 4. Process Query
    query = (
        "Please check the repository owner: 'likhith-adithya', "
        "repo: 'GITHUB-DEBUG-AI-AGENT'. "
        "Delegate a task to the sub-agent to verify if test cases "
        "in tests/test_tools_a2a.py are correct."
    )
    print(f"Sending query to agent:\n{query}")

    try:
        await agent.process_user_query(query)
    except (ValueError, RuntimeError) as e:
        print(f"Execution failure: {e}")
    finally:
        # 5. Teardown
        print("Tearing down agent...")
        await agent.teardown()
        print("Direct agent query test completed!")


if __name__ == "__main__":
    asyncio.run(main())
