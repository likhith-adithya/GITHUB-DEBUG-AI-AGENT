from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ToolDefinition:
    """Describes a tool the LLM can call, in a format compatible with OpenAI function calling."""

    name: str
    description: str
    parameters: Dict[str, Any]


class BaseToolClient(ABC):
    """Abstract base class for a tool client that provides tools to the AI agent."""

    @abstractmethod
    def get_available_tools(self) -> List[ToolDefinition]:
        """Returns the list of tools defined by this client."""
        pass

    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool provided by this client and return the string result."""
        pass
