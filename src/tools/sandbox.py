import asyncio
import os
from typing import Any, Dict, List

from .base import BaseToolClient, ToolDefinition


class SandboxToolClient(BaseToolClient):
    """
    Provides filesystem and command-line execution tools scoped strictly
    to a sandbox directory.
    """

    def __init__(self, sandbox_dir: str):
        self.sandbox_dir = os.path.abspath(sandbox_dir)

    def _resolve_path(self, path: str) -> str:
        """Resolve a path and ensure it does not escape the sandbox directory."""
        resolved = os.path.abspath(os.path.join(self.sandbox_dir, path))
        if not resolved.startswith(self.sandbox_dir):
            raise PermissionError(f"Access denied: {path} is outside the sandbox.")
        return resolved

    def get_available_tools(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="read_sandbox_file",
                description="Read the content of a file inside the sandbox.",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative path of the file from sandbox root.",
                        }
                    },
                    "required": ["path"],
                },
            ),
            ToolDefinition(
                name="write_sandbox_file",
                description="Create or overwrite a file inside the sandbox with new content.",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative path of the file from sandbox root.",
                        },
                        "content": {
                            "type": "string",
                            "description": "The full content to write to the file.",
                        },
                    },
                    "required": ["path", "content"],
                },
            ),
            ToolDefinition(
                name="list_sandbox_dir",
                description="List files and directories in a given path in the sandbox.",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative path to list (use '.' or '' for root).",
                        }
                    },
                    "required": ["path"],
                },
            ),
            ToolDefinition(
                name="run_sandbox_command",
                description="Run a shell command inside the sandbox directory. Useful for running tests, compilers, or debuggers.",
                parameters={
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The shell command to run (e.g. 'pytest', 'python main.py').",
                        }
                    },
                    "required": ["command"],
                },
            ),
        ]

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        if tool_name == "read_sandbox_file":
            path = self._resolve_path(arguments["path"])
            if not os.path.isfile(path):
                return f"Error: File not found at {arguments['path']}"
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

        elif tool_name == "write_sandbox_file":
            path = self._resolve_path(arguments["path"])
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(arguments["content"])
            return f"Successfully wrote {len(arguments['content'])} characters to {arguments['path']}."

        elif tool_name == "list_sandbox_dir":
            path = self._resolve_path(arguments["path"])
            if not os.path.isdir(path):
                return f"Error: Directory not found at {arguments['path']}"
            entries = os.listdir(path)
            lines = []
            for entry in sorted(entries):
                entry_path = os.path.join(path, entry)
                if os.path.isdir(entry_path):
                    lines.append(f"📁 {entry}/")
                else:
                    lines.append(f"📄 {entry}")
            return "\n".join(lines) if lines else "Directory is empty."

        elif tool_name == "run_sandbox_command":
            command = arguments["command"]
            try:
                proc = await asyncio.create_subprocess_shell(
                    command,
                    cwd=self.sandbox_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                return (
                    f"Exit code: {proc.returncode}\n"
                    f"STDOUT:\n{stdout.decode('utf-8', errors='replace')}\n"
                    f"STDERR:\n{stderr.decode('utf-8', errors='replace')}"
                )
            except Exception as e:
                return f"Error running command: {str(e)}"

        raise ValueError(f"Unknown tool: {tool_name}")
