import json
from typing import List, Optional

from src.tools.base import BaseToolClient

# Maximum words to keep from a single tool result to prevent context overflow
# Modern LLMs (Llama 3, Gemini) have 100k+ token windows, so we can be generous
MAX_TOOL_RESULT_WORDS = 8000


class AIEngineerAgent:
    def __init__(self, llm_client, tools_clients: Optional[List[BaseToolClient]] = None):
        self.llm = llm_client
        self.tools_clients = tools_clients or []

    async def setup(self):
        """Connect and verify credentials for all tools."""
        for client in self.tools_clients:
            if hasattr(client, "connect"):
                await client.connect()

    async def teardown(self):
        """Clean up resources."""
        for client in self.tools_clients:
            if hasattr(client, "disconnect"):
                await client.disconnect()

    def _build_tools_list(self) -> list:
        """Convert tool definitions to OpenAI function-calling format."""
        openai_tools = []
        for client in self.tools_clients:
            tools = client.get_available_tools()
            for tool in tools:
                openai_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.parameters,
                        },
                    }
                )
        return openai_tools

    async def _dispatch_tool_call(self, tool_name: str, tool_args: dict) -> str:
        for client in self.tools_clients:
            try:
                tools = client.get_available_tools()
                if any(t.name == tool_name for t in tools):
                    return await client.call_tool(tool_name, tool_args)
            except Exception as e:
                return f"Error executing tool {tool_name} on {type(client).__name__}: {str(e)}"
        return f"Error: Tool {tool_name} not found in any registered clients."

    def _truncate_result(self, text: str, max_words: int = MAX_TOOL_RESULT_WORDS) -> str:
        """Truncate long tool results by word count to prevent context window overflow."""
        words = text.split()
        if len(words) <= max_words:
            return text

        half = max_words // 2
        return (
            " ".join(words[:half])
            + f"\n\n... [TRUNCATED {len(words) - max_words} words] ...\n\n"
            + " ".join(words[-half:])
        )

    def _response_to_dict(self, response) -> dict:
        """Convert the LLM response object to a serializable dict for the message history.

        This is necessary because some providers return SDK objects that don't serialize
        properly when appended to the messages list for subsequent API calls.
        """
        msg = {
            "role": "assistant",
            "content": getattr(response, "content", None) or "",
        }
        if getattr(response, "tool_calls", None):
            msg["tool_calls"] = []
            for tc in response.tool_calls:
                msg["tool_calls"].append(
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                )
        return msg

    async def process_user_query(self, query: str):
        """Main agent loop for handling the user query, orchestrating the LLM and Tools."""
        tools_list = self._build_tools_list()

        system_prompt = """You are an Elite AI Software Architect and Interactive GitHub Auditor. 
Your goal is to collaborate dynamically with the user to explore, secure, and improve any public GitHub repository in the world.

Instead of doing everything in one massive response, you take an INTERACTIVE, conversational approach:
1. When asked to review a repository, start by scanning the high-level project structure (`list_repository_files`) and key metadata (`get_repository_info`).
2. Give the user a quick, high-level overview of what you see.
3. HIGHLIGHT potential areas of interest (e.g., "I see a docker-compose.yml and an authentication module. Would you like me to scan the auth module for security flaws, or review the Docker configuration first?").
4. Wait for the user's direction.

When the user asks you to dive into a specific area:
1. Use `get_file_contents` to deeply read the specific files.
2. ACTIVELY HUNT FOR:
   - Security vulnerabilities (hardcoded secrets, auth bypasses, injection vectors).
   - Architectural flaws and tech-debt (e.g., monolith bloat, bad abstractions).
3. Present your findings naturally and conversationally like a Senior Staff Engineer pairing with the user.
4. PROPOSE concrete fixes (architectural or code-level). Provide specific code snippets.
5. ASK the user if they'd like you to write the updated code or explore another part of the codebase.

IMPORTANT RULES:
- If a user asks a vague question (like "hi" or "review my repo" without giving a repo name), DO NOT HALLUCINATE. Ask them explicitly: "Please elaborate or provide the specific repository owner/name you'd like me to review."
- If a user asks you to review a repo, exhaustively search its files before answering.
- Proactively suggest structural improvements—do not wait to be asked.
- Call out security flaws and code-smells aggressively.
- Talk conversationally! Explain your reasoning step-by-step.
- When you have thoroughly mapped the codebase and gathered evidence, provide your final response.
- Do NOT try to read every single file at once. Explore interactively based on user feedback.
- ALWAYS ask a question at the end of your response to guide the user's next step.
- You are a partner, not a robot. Be conversational, highly proactive, and focused strictly on repository analysis and improvement."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        print("\nThinking...")

        # Max iteration limit to prevent infinite loops
        for _ in range(10):
            try:
                response = await self.llm.generate_response(messages, tools=tools_list)
            except Exception as e:
                print(f"\n[!] Failed to connect to LLM: {type(e).__name__} - {e}")
                print("Please ensure your LLM is running or check your .env configuration.")
                break

            # If the LLM didn't request a tool, it's done providing the final answer
            if not getattr(response, "tool_calls", None):
                print(f"\n{'=' * 60}")
                print("  Agent Final Output")
                print(f"{'=' * 60}")
                content = getattr(response, "content", None) or "No content returned."
                print(content)
                print(f"{'=' * 60}\n")
                break

            # If the LLM requested an action (a tool call)
            # Convert and append the assistant message as a proper dict
            messages.append(self._response_to_dict(response))

            for tool_call in response.tool_calls:
                tool_name = tool_call.function.name

                # Safely parse tool arguments
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": f"Error: Invalid JSON arguments: {tool_call.function.arguments}",
                        }
                    )
                    continue

                try:
                    tool_result = await self._dispatch_tool_call(tool_name, tool_args)
                    # Truncate very long results to prevent context overflow
                    tool_result = self._truncate_result(tool_result)

                    # Store the result so the LLM knows what happened
                    messages.append(
                        {"role": "tool", "tool_call_id": tool_call.id, "content": tool_result}
                    )
                except Exception as e:
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": f"Error executing tool: {e}",
                        }
                    )
        else:
            print("\n[!] Agent reached maximum iteration limit without finalizing an answer.")
