import json
import logging
from typing import List

from src.core.llm import LLMClient
from src.tools.base import BaseToolClient

logger = logging.getLogger(__name__)


class DebugWorkerAgent:
    """
    A specialized, autonomous agent that operates within a sandbox
    to solve a specific debugging task using scoped file and execution tools.
    """

    def __init__(self, llm_client: LLMClient, tools_clients: List[BaseToolClient]):
        self.llm = llm_client
        self.tools_clients = tools_clients

    def _build_tools_list(self) -> list:
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
            tools = client.get_available_tools()
            if any(t.name == tool_name for t in tools):
                return await client.call_tool(tool_name, tool_args)
        return f"Error: Tool {tool_name} not found."

    async def run_autonomous_loop(self, task_description: str, context_files: List[str]) -> str:
        tools_list = self._build_tools_list()

        system_prompt = """You are a Specialized Sandboxed Debug Agent. 
Your goal is to solve a specific debugging task inside an isolated workspace.

You have access to tools to read/write files and run shell commands (like running test suites or checking code execution).
Use them to investigate the problem, implement a clean fix, and verify it by running the tests.

When you have completed the task or verified the fix (or if you determine it is not possible to fix), formulate your final response as a clear diagnostic report outlining:
1. Root Cause: What the issue was.
2. Changes Made: Specific file modifications.
3. Verification: Results of running tests or commands.
4. Recommendation: Next steps.

Do NOT print intermediate conversation to the user. Simply execute your tools to investigate and fix, then output your final report."""

        user_prompt = f"Task: {task_description}\nContext Files: {', '.join(context_files) if context_files else 'None'}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Autonomous loop up to 8 iterations
        for i in range(8):
            try:
                response = await self.llm.generate_response(messages, tools=tools_list)
            except Exception as e:
                return f"Error during sub-agent execution: {str(e)}"

            if not getattr(response, "tool_calls", None):
                # No tool calls means the sub-agent has finalized its report
                return getattr(response, "content", None) or "No report content returned from sub-agent."

            # Append the assistant's request to messages
            msg = {
                "role": "assistant",
                "content": getattr(response, "content", None) or "",
            }
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
            messages.append(msg)

            # Process tool calls
            for tool_call in response.tool_calls:
                tool_name = tool_call.function.name
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": f"Error: Invalid JSON arguments: {tool_call.function.arguments}"
                    })
                    continue

                tool_result = await self._dispatch_tool_call(tool_name, tool_args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })

        return "Error: Sub-agent exceeded maximum autonomous iterations without returning a report."
