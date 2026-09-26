"""GitHub tools — repo info, file read, issues, PRs"""
import os
import requests
from typing import Optional, List
from src.tools.base import BaseTool, ToolResult

GITHUB_API = "https://api.github.com"


def _headers() -> dict:
    """GitHub API headers with optional token"""
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get(url: str, params: dict = None) -> dict:
    """GET request to GitHub API"""
    resp = requests.get(url, headers=_headers(), params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


class GetRepoInfoTool(BaseTool):
    name = "get_repo_info"
    description = "Get information about a GitHub repository (stars, forks, language, description)"
    parameters = {
        "type": "object",
        "properties": {
            "owner": {"type": "string", "description": "Repo owner (username or org)"},
            "repo": {"type": "string", "description": "Repository name"},
        },
        "required": ["owner", "repo"],
    }
    risk_level = "low"
    
    def run(self, owner: str, repo: str) -> ToolResult:
        try:
            data = _get(f"{GITHUB_API}/repos/{owner}/{repo}")
            info = {
                "full_name": data["full_name"],
                "description": data.get("description", ""),
                "stars": data["stargazers_count"],
                "forks": data["forks_count"],
                "language": data.get("language", ""),
                "open_issues": data["open_issues_count"],
                "default_branch": data["default_branch"],
                "created_at": data["created_at"],
                "updated_at": data["updated_at"],
                "topics": data.get("topics", []),
                "url": data["html_url"],
            }
            return ToolResult(success=True, output=info)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ListRepoFilesTool(BaseTool):
    name = "list_repo_files"
    description = "List files in a GitHub repository at a given path"
    parameters = {
        "type": "object",
        "properties": {
            "owner": {"type": "string"},
            "repo": {"type": "string"},
            "path": {"type": "string", "description": "Path within repo (use '' for root)"},
        },
        "required": ["owner", "repo"],
    }
    risk_level = "low"
    
    def run(self, owner: str, repo: str, path: str = "") -> ToolResult:
        try:
            data = _get(f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}")
            if isinstance(data, dict):
                data = [data]
            items = [
                {
                    "name": item["name"],
                    "type": item["type"],
                    "size": item.get("size", 0),
                    "path": item["path"],
                }
                for item in data
            ]
            return ToolResult(success=True, output=items, metadata={"count": len(items)})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ReadRepoFileTool(BaseTool):
    name = "read_repo_file"
    description = "Read the content of a file in a GitHub repository"
    parameters = {
        "type": "object",
        "properties": {
            "owner": {"type": "string"},
            "repo": {"type": "string"},
            "path": {"type": "string"},
        },
        "required": ["owner", "repo", "path"],
    }
    risk_level = "low"
    
    def run(self, owner: str, repo: str, path: str) -> ToolResult:
        try:
            import base64
            data = _get(f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}")
            if data.get("type") != "file":
                return ToolResult(success=False, error=f"Not a file: {path}")
            
            content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            
            # Limit to 50KB for safety
            if len(content) > 50_000:
                content = content[:50_000] + "\n... [truncated]"
            
            return ToolResult(
                success=True,
                output=content,
                metadata={"path": path, "size": data.get("size", 0)},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ListIssuesTool(BaseTool):
    name = "list_issues"
    description = "List open issues for a GitHub repository"
    parameters = {
        "type": "object",
        "properties": {
            "owner": {"type": "string"},
            "repo": {"type": "string"},
            "state": {"type": "string", "description": "open | closed | all"},
            "limit": {"type": "integer", "description": "Max issues to return"},
        },
        "required": ["owner", "repo"],
    }
    risk_level = "low"
    
    def run(self, owner: str, repo: str, state: str = "open", limit: int = 10) -> ToolResult:
        try:
            data = _get(
                f"{GITHUB_API}/repos/{owner}/{repo}/issues",
                params={"state": state, "per_page": min(limit, 30)},
            )
            issues = [
                {
                    "number": i["number"],
                    "title": i["title"],
                    "state": i["state"],
                    "labels": [l["name"] for l in i.get("labels", [])],
                    "url": i["html_url"],
                    "created_at": i["created_at"],
                }
                for i in data
                if "pull_request" not in i  # Skip PRs
            ]
            return ToolResult(success=True, output=issues, metadata={"count": len(issues)})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


if __name__ == "__main__":
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    console.print("\n[bold magenta]GitHub Tools Test[/bold magenta]\n")
    
    # Test repo info
    tool = GetRepoInfoTool()
    r = tool.run("vaibhav07772", "aegisos")
    if r.success:
        info = r.output
        console.print(f"[green]Repo:[/green] {info['full_name']}")
        console.print(f"  Description: {info['description']}")
        console.print(f"  Stars: {info['stars']} | Forks: {info['forks']} | Language: {info['language']}")
    else:
        console.print(f"[red]Error:[/red] {r.error}")
    
    # Test file listing
    console.print()
    tool = ListRepoFilesTool()
    r = tool.run("vaibhav07772", "aegisos", "src/core")
    if r.success:
        console.print("[green]Files in src/core:[/green]")
        for f in r.output:
            console.print(f"  [{f['type']}] {f['name']} ({f['size']} bytes)")
    else:
        console.print(f"[red]Error:[/red] {r.error}")
    
    # Test read file
    console.print()
    tool = ReadRepoFileTool()
    r = tool.run("vaibhav07772", "aegisos", "README.md")
    if r.success:
        console.print(f"[green]README.md (first 200 chars):[/green]")
        console.print(r.output[:200])
    else:
        console.print(f"[red]Error:[/red] {r.error}")