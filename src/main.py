"""
AI Code Debugger Agent — Main Entry Point

Orchestrates the LLM and GitHub tools to debug code,
analyze tech stacks, and review repositories.
"""

import asyncio

from src.cli import select_llm_configuration
from src.core.agent import AIEngineerAgent
from src.core.llm import LLMClient
from src.tools.a2a import A2ADebugToolClient
from src.tools.github import GitHubClient


async def main():
    # 1. Configuration Phase
    select_llm_configuration()

    # 2. Initialization Phase
    llm_client = LLMClient()
    github_client = GitHubClient()
    a2a_client = A2ADebugToolClient()

    agent = AIEngineerAgent(llm_client=llm_client, tools_clients=[github_client, a2a_client])

    try:
        # 3. Setup Phase
        await agent.setup()

        print("\n" + "=" * 60)
        print("  🐛 AI Code Debugger Agent")
        print("  Type your query or 'quit' to exit")
        print("=" * 60)

        # 4. Interaction Phase
        while True:
            try:
                query = input("\nDeveloper Query > ")
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if query.lower() in ["quit", "exit"]:
                print("Goodbye!")
                break
            if not query.strip():
                continue

            await agent.process_user_query(query)

    finally:
        # 5. Cleanup Phase
        await agent.teardown()


if __name__ == "__main__":
    asyncio.run(main())
