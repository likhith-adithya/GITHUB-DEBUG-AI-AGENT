import asyncio
import os
import shutil
import uuid
from typing import Any, Dict, List

from src.config import settings
from src.core.llm import LLMClient
from src.core.worker import DebugWorkerAgent
from src.tools.sandbox import SandboxToolClient

from .base import BaseToolClient, ToolDefinition


class A2ADebugToolClient(BaseToolClient):
    """
    Agent-to-Agent (A2A) Debug Tool Client.

    Implements a protocol for the primary agent to delegate complex debugging
    and execution tracing tasks to specialized sub-agents running inside sandboxes.
    """

    def get_available_tools(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="invoke_debug_agent",
                description=(
                    "Delegates a specific, complex debugging task to a specialized sub-agent. "
                    "This clones the target repository, profiles/runs code, and returns a detailed report."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "owner": {
                            "type": "string",
                            "description": "The owner of the GitHub repository (e.g., 'octocat').",
                        },
                        "repo": {
                            "type": "string",
                            "description": "The name of the GitHub repository (e.g., 'hello-world').",
                        },
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
                    "required": ["owner", "repo", "task_description"],
                },
            )
        ]

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        if tool_name == "invoke_debug_agent":
            return await self._invoke_debug_agent(
                owner=arguments["owner"],
                repo=arguments["repo"],
                task_description=arguments["task_description"],
                context_files=arguments.get("context_files", []),
            )
        raise ValueError(f"Unknown tool: {tool_name}")

    async def _invoke_debug_agent(
        self, owner: str, repo: str, task_description: str, context_files: List[str]
    ) -> str:
        """
        Clones the specified repository into a local sandbox, runs a DebugWorkerAgent
        autonomously on it, and cleans up the sandbox before returning the report.
        """
        # Determine the sandboxes directory under project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        sandboxes_dir = os.path.join(project_root, ".sandboxes")
        os.makedirs(sandboxes_dir, exist_ok=True)

        # Generate unique sandbox path
        sandbox_id = str(uuid.uuid4())[:8]
        sandbox_path = os.path.join(sandboxes_dir, f"{owner}_{repo}_{sandbox_id}")

        print("\n[A2A] Preparing to delegate task to specialized debug agent...")
        print(f"[A2A] Repository: {owner}/{repo}")
        print(f"[A2A] Task: {task_description}")

        # Git clone
        token = settings.GITHUB_TOKEN
        if token:
            clone_url = f"https://{token}@github.com/{owner}/{repo}.git"
        else:
            clone_url = f"https://github.com/{owner}/{repo}.git"

        print(f"[A2A] Cloning repository to {sandbox_path}...")
        try:
            proc = await asyncio.create_subprocess_exec(
                "git",
                "clone",
                "--depth",
                "1",
                clone_url,
                sandbox_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                err_msg = stderr.decode("utf-8", errors="replace")
                # Redact token from error message if present
                if token:
                    err_msg = err_msg.replace(token, "******")
                return f"Error cloning repository: {err_msg}"
        except Exception as e:
            return f"Error starting clone process: {str(e)}"

        try:
            # Setup LLM, Sandbox Tool Client, and Worker Agent
            llm_client = LLMClient()
            sandbox_client = SandboxToolClient(sandbox_dir=sandbox_path)
            worker_agent = DebugWorkerAgent(
                llm_client=llm_client, tools_clients=[sandbox_client]
            )

            print("[A2A] Running autonomous debug worker loop...")
            report = await worker_agent.run_autonomous_loop(
                task_description=task_description, context_files=context_files
            )
            return f"DEBUG AGENT REPORT:\n{report}"

        finally:
            # Clean up the sandbox directory to avoid disk bloat
            print(f"[A2A] Cleaning up sandbox at {sandbox_path}...")
            try:
                if os.path.exists(sandbox_path) and sandbox_path.startswith(sandboxes_dir):
                    # Run a process or shutil rmtree
                    # Since git clone makes some read-only files occasionally on Mac,
                    # we define an error handler or use shutil.rmtree with onerror
                    def handle_remove_readonly(func, path, exc):
                        import stat
                        excvalue = exc[1]
                        if func in (os.rmdir, os.remove) and excvalue.errno == 13:
                            os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                            func(path)
                        else:
                            raise

                    shutil.rmtree(sandbox_path, onerror=handle_remove_readonly)
            except Exception as e:
                print(f"[A2A] Warning: Failed to clean up sandbox: {e}")
