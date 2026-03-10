"""
Pure Python GitHub client for the AI Debug Agent.

Provides GitHub API tools (search repos, read files, list issues, etc.)
using httpx — no Node.js, npx, or MCP required.
"""

import json
import base64
from typing import List, Dict, Any

import httpx
from src.config import settings
from src.tools.base import BaseToolClient, ToolDefinition

GITHUB_API_BASE = "https://api.github.com"



# ─── Tool Registry ────────────────────────────────────────────────────────────
# Each tool is defined with its name, description, and JSON Schema parameters.

GITHUB_TOOLS: List[ToolDefinition] = [
    ToolDefinition(
        name="search_repositories",
        description="Search for GitHub repositories by keyword. Returns repository names, descriptions, stars, and language.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g., 'machine learning python')"
                },
                "per_page": {
                    "type": "integer",
                    "description": "Number of results to return (max 30, default 5)"
                }
            },
            "required": ["query"]
        }
    ),
    ToolDefinition(
        name="get_file_contents",
        description="Read the contents of a file from a GitHub repository. Returns the decoded file content.",
        parameters={
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "Repository owner (e.g., 'octocat')"
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name (e.g., 'hello-world')"
                },
                "path": {
                    "type": "string",
                    "description": "File path within the repository (e.g., 'src/main.py')"
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name (default: repo's default branch)"
                }
            },
            "required": ["owner", "repo", "path"]
        }
    ),
    ToolDefinition(
        name="list_repository_files",
        description="List all files and directories at a given path in a GitHub repository.",
        parameters={
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "Repository owner"
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name"
                },
                "path": {
                    "type": "string",
                    "description": "Directory path (use '' or '.' for root)"
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name (default: repo's default branch)"
                }
            },
            "required": ["owner", "repo"]
        }
    ),
    ToolDefinition(
        name="search_code",
        description="Search for code across GitHub repositories. Returns matching file paths and code snippets.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Code search query. Use qualifiers like 'repo:owner/name' to search within a specific repo."
                },
                "per_page": {
                    "type": "integer",
                    "description": "Number of results (max 30, default 5)"
                }
            },
            "required": ["query"]
        }
    ),
    ToolDefinition(
        name="list_issues",
        description="List issues for a GitHub repository, optionally filtered by state.",
        parameters={
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "Repository owner"
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name"
                },
                "state": {
                    "type": "string",
                    "description": "Filter by state: 'open', 'closed', or 'all' (default: 'open')",
                    "enum": ["open", "closed", "all"]
                },
                "per_page": {
                    "type": "integer",
                    "description": "Number of results (max 30, default 10)"
                }
            },
            "required": ["owner", "repo"]
        }
    ),
    ToolDefinition(
        name="get_issue",
        description="Get detailed information about a specific GitHub issue, including its body and comments.",
        parameters={
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "Repository owner"
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name"
                },
                "issue_number": {
                    "type": "integer",
                    "description": "The issue number"
                }
            },
            "required": ["owner", "repo", "issue_number"]
        }
    ),
    ToolDefinition(
        name="list_commits",
        description="List recent commits for a GitHub repository.",
        parameters={
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "Repository owner"
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name"
                },
                "path": {
                    "type": "string",
                    "description": "Only commits containing this file path"
                },
                "per_page": {
                    "type": "integer",
                    "description": "Number of results (max 30, default 10)"
                }
            },
            "required": ["owner", "repo"]
        }
    ),
    ToolDefinition(
        name="get_repository_info",
        description="Get detailed information about a GitHub repository including description, stars, forks, language, and default branch.",
        parameters={
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "Repository owner"
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name"
                }
            },
            "required": ["owner", "repo"]
        }
    ),
]


class GitHubClient(BaseToolClient):
    """Pure Python GitHub API client that provides tool-calling interface for the LLM agent."""

    def __init__(self):
        self.github_token = settings.GITHUB_TOKEN
        if not self.github_token:
            raise ValueError(
                "GITHUB_PERSONAL_ACCESS_TOKEN environment variable is required.\n"
                "Set it in your .env file or export it in your shell.\n"
                "Generate one at: https://github.com/settings/tokens"
            )

        self._client = httpx.AsyncClient(
            base_url=GITHUB_API_BASE,
            headers={
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "AI-Debug-Agent/1.0",
            },
            timeout=30.0,
        )

    async def connect(self):
        """Verify the GitHub token is valid by making a test API call."""
        print("Connecting to GitHub API...")
        try:
            response = await self._client.get("/user")
            if response.status_code == 200:
                user = response.json()
                print(f"Connected to GitHub as: {user.get('login', 'unknown')}")
            elif response.status_code == 401:
                raise ValueError(
                    "GitHub token is invalid or expired. "
                    "Please generate a new token at: https://github.com/settings/tokens"
                )
            else:
                # Token might have limited scopes but still be valid
                print(f"Connected to GitHub (status: {response.status_code})")
        except httpx.ConnectError:
            raise RuntimeError(
                "Cannot reach GitHub API. Check your internet connection."
            )

    async def disconnect(self):
        """Close the HTTP client."""
        await self._client.aclose()
        print("Disconnected from GitHub API.")

    def get_available_tools(self) -> List[ToolDefinition]:
        """Returns the list of available GitHub tools."""
        return GITHUB_TOOLS

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a GitHub tool and return the result as a string."""
        # Dispatch to the appropriate handler
        handler = getattr(self, f"_tool_{tool_name}", None)
        if handler is None:
            return f"Error: Unknown tool '{tool_name}'. Available tools: {[t.name for t in GITHUB_TOOLS]}"

        try:
            return await handler(**arguments)
        except httpx.HTTPStatusError as e:
            return f"GitHub API error: {e.response.status_code} - {e.response.text[:500]}"
        except Exception as e:
            return f"Error executing {tool_name}: {type(e).__name__} - {e}"

    # ─── Tool Implementations ─────────────────────────────────────────────────

    async def _tool_search_repositories(self, query: str, per_page: int = 5) -> str:
        """Search GitHub repositories."""
        per_page = min(per_page, 30)
        response = await self._client.get(
            "/search/repositories",
            params={"q": query, "per_page": per_page, "sort": "stars", "order": "desc"}
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("items"):
            return f"No repositories found for query: '{query}'"

        results = []
        for repo in data["items"]:
            results.append(
                f"📦 {repo['full_name']}\n"
                f"   Description: {repo.get('description', 'N/A')}\n"
                f"   Language: {repo.get('language', 'N/A')} | "
                f"⭐ {repo.get('stargazers_count', 0)} | "
                f"🍴 {repo.get('forks_count', 0)}\n"
                f"   URL: {repo['html_url']}"
            )
        return f"Found {data['total_count']} repositories:\n\n" + "\n\n".join(results)

    async def _tool_get_file_contents(self, owner: str, repo: str, path: str, branch: str = None) -> str:
        """Read a file's contents from a GitHub repository."""
        url = f"/repos/{owner}/{repo}/contents/{path}"
        params = {}
        if branch:
            params["ref"] = branch

        response = await self._client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Handle directory listing
        if isinstance(data, list):
            entries = []
            for item in data:
                icon = "📁" if item["type"] == "dir" else "📄"
                size = f" ({item.get('size', 0)} bytes)" if item["type"] == "file" else ""
                entries.append(f"  {icon} {item['name']}{size}")
            return f"Directory listing for {owner}/{repo}/{path}:\n" + "\n".join(entries)

        # Handle file content
        if data.get("type") == "file":
            content = data.get("content", "")
            encoding = data.get("encoding", "")

            if encoding == "base64":
                try:
                    decoded = base64.b64decode(content).decode("utf-8")
                except (UnicodeDecodeError, Exception):
                    return f"File {path} exists but contains binary content ({data.get('size', 0)} bytes)"
            else:
                decoded = content

            return (
                f"File: {path} ({data.get('size', 0)} bytes)\n"
                f"{'─' * 60}\n"
                f"{decoded}"
            )

        return f"Unexpected content type for {path}: {data.get('type', 'unknown')}"

    async def _tool_list_repository_files(self, owner: str, repo: str, path: str = "", branch: str = None) -> str:
        """List files in a repository directory."""
        if path in (".", ""):
            path = ""
        url = f"/repos/{owner}/{repo}/contents/{path}"
        params = {}
        if branch:
            params["ref"] = branch

        response = await self._client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list):
            return f"{path} is a file, not a directory. Use get_file_contents to read it."

        entries = []
        for item in sorted(data, key=lambda x: (x["type"] != "dir", x["name"])):
            icon = "📁" if item["type"] == "dir" else "📄"
            size = f" ({item.get('size', 0)} bytes)" if item["type"] == "file" else ""
            entries.append(f"  {icon} {item['name']}{size}")

        dir_label = f"{owner}/{repo}/{path}" if path else f"{owner}/{repo} (root)"
        return f"Contents of {dir_label}:\n" + "\n".join(entries)

    async def _tool_search_code(self, query: str, per_page: int = 5) -> str:
        """Search for code across GitHub."""
        per_page = min(per_page, 30)
        response = await self._client.get(
            "/search/code",
            params={"q": query, "per_page": per_page}
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("items"):
            return f"No code results found for query: '{query}'"

        results = []
        for item in data["items"]:
            results.append(
                f"📄 {item['repository']['full_name']}/{item['path']}\n"
                f"   URL: {item['html_url']}"
            )
        return f"Found {data['total_count']} code results:\n\n" + "\n\n".join(results)

    async def _tool_list_issues(self, owner: str, repo: str, state: str = "open", per_page: int = 10) -> str:
        """List issues for a repository."""
        per_page = min(per_page, 30)
        response = await self._client.get(
            f"/repos/{owner}/{repo}/issues",
            params={"state": state, "per_page": per_page}
        )
        response.raise_for_status()
        data = response.json()

        if not data:
            return f"No {state} issues found for {owner}/{repo}"

        results = []
        for issue in data:
            labels = ", ".join(l["name"] for l in issue.get("labels", []))
            labels_str = f" [{labels}]" if labels else ""
            results.append(
                f"  #{issue['number']} {issue['title']}{labels_str}\n"
                f"     State: {issue['state']} | "
                f"Author: {issue['user']['login']} | "
                f"Created: {issue['created_at'][:10]}"
            )
        return f"Issues for {owner}/{repo} ({state}):\n\n" + "\n\n".join(results)

    async def _tool_get_issue(self, owner: str, repo: str, issue_number: int) -> str:
        """Get detailed info about a specific issue."""
        response = await self._client.get(
            f"/repos/{owner}/{repo}/issues/{issue_number}"
        )
        response.raise_for_status()
        issue = response.json()

        labels = ", ".join(l["name"] for l in issue.get("labels", []))
        labels_str = f"\nLabels: {labels}" if labels else ""

        result = (
            f"Issue #{issue['number']}: {issue['title']}\n"
            f"State: {issue['state']} | Author: {issue['user']['login']}\n"
            f"Created: {issue['created_at'][:10]} | Updated: {issue['updated_at'][:10]}"
            f"{labels_str}\n"
            f"{'─' * 60}\n"
            f"{issue.get('body', 'No description provided.')}"
        )

        # Also fetch comments if any
        if issue.get("comments", 0) > 0:
            comments_resp = await self._client.get(
                f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
                params={"per_page": 10}
            )
            if comments_resp.status_code == 200:
                comments = comments_resp.json()
                result += f"\n\n{'─' * 60}\nComments ({len(comments)}):\n"
                for c in comments:
                    result += (
                        f"\n  💬 {c['user']['login']} ({c['created_at'][:10]}):\n"
                        f"  {c['body'][:500]}\n"
                    )

        return result

    async def _tool_list_commits(self, owner: str, repo: str, path: str = None, per_page: int = 10) -> str:
        """List recent commits."""
        per_page = min(per_page, 30)
        params = {"per_page": per_page}
        if path:
            params["path"] = path

        response = await self._client.get(
            f"/repos/{owner}/{repo}/commits",
            params=params
        )
        response.raise_for_status()
        data = response.json()

        if not data:
            return f"No commits found for {owner}/{repo}"

        results = []
        for commit in data:
            sha = commit["sha"][:7]
            msg = commit["commit"]["message"].split("\n")[0][:80]
            author = commit["commit"]["author"]["name"]
            date = commit["commit"]["author"]["date"][:10]
            results.append(f"  {sha} {msg} ({author}, {date})")

        return f"Recent commits for {owner}/{repo}:\n\n" + "\n".join(results)

    async def _tool_get_repository_info(self, owner: str, repo: str) -> str:
        """Get detailed repository information."""
        response = await self._client.get(f"/repos/{owner}/{repo}")
        response.raise_for_status()
        data = response.json()

        return (
            f"Repository: {data['full_name']}\n"
            f"Description: {data.get('description', 'N/A')}\n"
            f"Language: {data.get('language', 'N/A')}\n"
            f"Default Branch: {data.get('default_branch', 'main')}\n"
            f"Stars: {data.get('stargazers_count', 0)} | "
            f"Forks: {data.get('forks_count', 0)} | "
            f"Open Issues: {data.get('open_issues_count', 0)}\n"
            f"Created: {data['created_at'][:10]} | "
            f"Last Push: {data.get('pushed_at', 'N/A')[:10]}\n"
            f"URL: {data['html_url']}\n"
            f"Topics: {', '.join(data.get('topics', [])) or 'None'}\n"
            f"License: {data.get('license', {}).get('name', 'None') if data.get('license') else 'None'}"
        )
