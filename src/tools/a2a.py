import asyncio
from typing import List

from .base import BaseToolClient, ToolDefinition


class A2ADebugToolClient(BaseToolClient):
    """
    Agent-to-Agent (A2A) Debug Tool Client.

    Implements a protocol for the primary agent to delegate complex debugging
    and execution tracing tasks to specialized sub-agents.
    """

    def get_available_tools(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="invoke_debug_agent",
                description="Delegates a specific, complex debugging task to a specialized sub-agent. Use this for deep-dive execution tracing or complex bug root-cause analysis.",
                parameters={
                    "type": "object",
                    "properties": {
                        "task_description": {
                            "type": "string",
                            "description": "A detailed description of the debugging task, including relevant file paths and the specific issue to investigate.",
                        },
                        "context_files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of file paths that the sub-agent should focus on.",
                        },
                    },
                    "required": ["task_description"],
                },
            )
        ]

    async def call_tool(self, tool_name: str, args: dict) -> str:
        if tool_name == "invoke_debug_agent":
            return await self._invoke_debug_agent(
                args["task_description"], args.get("context_files", [])
            )
        raise ValueError(f"Unknown tool: {tool_name}")

    async def _invoke_debug_agent(self, task_description: str, context_files: List[str]) -> str:
        """
        Simulates the delegation to a sub-agent.
        In a real implementation, this might spin up another LLM session or a container.
        """
        print("\n[A2A] Delegating task to specialized debug agent...")
        print(f"[A2A] Task: {task_description}")

        # Simulate some "thinking" time for the sub-agent
        await asyncio.sleep(1)

        return (
            f"DEBUG AGENT REPORT:\n"
            f"Successfully analyzed the requested task: '{task_description}'\n"
            f"Context analyzed: {', '.join(context_files) if context_files else 'global'}\n"
            f"Findings: The sub-agent identified potential race conditions in the trace. "
            f"Recommendation: Review memory barriers in the identified modules."
        )
