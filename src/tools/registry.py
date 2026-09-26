"""Tool Registry — central registry for all available tools"""
from typing import Dict, List, Optional
from rich.console import Console

from src.tools.base import BaseTool, ToolResult
from src.tools.filesystem import (
    ReadFileTool, WriteFileTool, ListFilesTool, DeleteFileTool,
)
from src.tools.github import (
    GetRepoInfoTool, ListRepoFilesTool, ReadRepoFileTool, ListIssuesTool,
)

console = Console()


class ToolRegistry:
    """Central registry of all tools available to the agent"""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register all built-in tools"""
        # Filesystem
        self.register(ReadFileTool())
        self.register(WriteFileTool())
        self.register(ListFilesTool())
        self.register(DeleteFileTool())
        
        # GitHub
        self.register(GetRepoInfoTool())
        self.register(ListRepoFilesTool())
        self.register(ReadRepoFileTool())
        self.register(ListIssuesTool())
    
    def register(self, tool: BaseTool):
        """Register a tool by name"""
        self.tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[BaseTool]:
        """Get tool by name"""
        return self.tools.get(name)
    
    def get_all_schemas(self) -> List[Dict]:
        """Return schemas for all tools (for LLM)"""
        return [tool.to_schema() for tool in self.tools.values()]
    
    def get_tools_for_task(self, tools_needed: List[str]) -> List[BaseTool]:
        """
        Given a list of tool categories needed (e.g., ['filesystem', 'github']),
        return matching tools.
        """
        category_map = {
            "filesystem": ["read_file", "write_file", "list_files", "delete_file"],
            "github": ["get_repo_info", "list_repo_files", "read_repo_file", "list_issues"],
            "browser": [],  # Not implemented yet
            "shell": [],    # Not implemented yet
        }
        
        selected = []
        for category in tools_needed:
            tool_names = category_map.get(category, [])
            for name in tool_names:
                tool = self.tools.get(name)
                if tool:
                    selected.append(tool)
        
        return selected
    
    def execute(self, tool_name: str, params: Dict) -> ToolResult:
        """Execute a tool by name"""
        tool = self.get(tool_name)
        if not tool:
            return ToolResult(success=False, error=f"Unknown tool: {tool_name}")
        
        console.print(f"[cyan]🔧 Executing {tool_name}...[/cyan]")
        try:
            return tool.run(**params)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


if __name__ == "__main__":
    from rich.table import Table
    
    console.print("\n[bold magenta]Tool Registry Test[/bold magenta]\n")
    
    registry = ToolRegistry()
    
    # List all tools
    table = Table(title="Registered Tools")
    table.add_column("Name", style="cyan")
    table.add_column("Risk", style="yellow")
    table.add_column("Description", style="white")
    
    for tool in registry.tools.values():
        table.add_row(tool.name, tool.risk_level, tool.description[:60])
    
    console.print(table)
    
    # Test task-based selection
    console.print("\n[cyan]Tools for 'filesystem':[/cyan]")
    tools = registry.get_tools_for_task(["filesystem"])
    for t in tools:
        console.print(f"  - {t.name}")
    
    console.print("\n[cyan]Tools for 'github':[/cyan]")
    tools = registry.get_tools_for_task(["github"])
    for t in tools:
        console.print(f"  - {t.name}")
    
    console.print("\n[cyan]Tools for 'filesystem + github':[/cyan]")
    tools = registry.get_tools_for_task(["filesystem", "github"])
    for t in tools:
        console.print(f"  - {t.name}")
    
    # Test execution
    console.print("\n[cyan]Test execution:[/cyan]")
    result = registry.execute("list_files", {"path": "."})
    console.print(f"  Success: {result.success}")
    if result.success:
        console.print(f"  Output: {result.output}")