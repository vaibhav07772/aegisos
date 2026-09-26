"""Filesystem tools — safe file operations within sandbox"""
import os
from pathlib import Path
from typing import Optional
from src.tools.base import BaseTool, ToolResult


# Sandbox: all file operations restricted to this directory
SANDBOX_ROOT = Path("./sandbox").resolve()
SANDBOX_ROOT.mkdir(exist_ok=True)

# Safe extensions (don't allow .exe, .bat, etc.)
SAFE_EXTENSIONS = {
    ".py", ".txt", ".md", ".json", ".yaml", ".yml",
    ".csv", ".html", ".css", ".js", ".ts", ".sql",
    ".toml", ".ini", ".cfg", ".env.example",
    ".sh", ".dockerfile",
}

MAX_FILE_SIZE = 1_000_000  # 1 MB


def _safe_path(relative_path: str) -> Path:
    """Resolve path and ensure it's within sandbox"""
    target = (SANDBOX_ROOT / relative_path).resolve()
    
    # Security check
    if not str(target).startswith(str(SANDBOX_ROOT)):
        raise ValueError(f"Path outside sandbox: {relative_path}")
    
    return target


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read contents of a file within the sandbox directory"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path to the file (e.g., 'project/main.py')",
            }
        },
        "required": ["path"],
    }
    risk_level = "low"
    
    def run(self, path: str) -> ToolResult:
        try:
            target = _safe_path(path)
            
            if not target.exists():
                return ToolResult(success=False, error=f"File not found: {path}")
            
            if not target.is_file():
                return ToolResult(success=False, error=f"Not a file: {path}")
            
            if target.stat().st_size > MAX_FILE_SIZE:
                return ToolResult(success=False, error=f"File too large (>{MAX_FILE_SIZE} bytes)")
            
            content = target.read_text(encoding="utf-8", errors="replace")
            return ToolResult(
                success=True,
                output=content,
                metadata={"path": path, "size": len(content)},
            )
        
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Write content to a file within the sandbox. Creates directories if needed."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative file path"},
            "content": {"type": "string", "description": "File content to write"},
        },
        "required": ["path", "content"],
    }
    risk_level = "medium"
    
    def run(self, path: str, content: str) -> ToolResult:
        try:
            target = _safe_path(path)
            
            # Check extension
            if target.suffix and target.suffix.lower() not in SAFE_EXTENSIONS:
                return ToolResult(
                    success=False,
                    error=f"Extension not allowed: {target.suffix}. Allowed: {sorted(SAFE_EXTENSIONS)}",
                )
            
            # Size check
            if len(content.encode("utf-8")) > MAX_FILE_SIZE:
                return ToolResult(success=False, error=f"Content too large (>{MAX_FILE_SIZE} bytes)")
            
            # Create parent dirs
            target.parent.mkdir(parents=True, exist_ok=True)
            
            # Write
            target.write_text(content, encoding="utf-8")
            
            return ToolResult(
                success=True,
                output=f"Wrote {len(content)} chars to {path}",
                metadata={"path": path, "bytes": len(content.encode("utf-8"))},
            )
        
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ListFilesTool(BaseTool):
    name = "list_files"
    description = "List files and directories within a sandbox path"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative directory path (use '.' for root)"},
        },
        "required": ["path"],
    }
    risk_level = "low"
    
    def run(self, path: str = ".") -> ToolResult:
        try:
            target = _safe_path(path)
            
            if not target.exists():
                return ToolResult(success=False, error=f"Directory not found: {path}")
            
            if not target.is_dir():
                return ToolResult(success=False, error=f"Not a directory: {path}")
            
            items = []
            for item in sorted(target.iterdir()):
                items.append({
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0,
                })
            
            return ToolResult(
                success=True,
                output=items,
                metadata={"path": path, "count": len(items)},
            )
        
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "Delete a file within the sandbox"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative file path to delete"},
        },
        "required": ["path"],
    }
    risk_level = "high"
    
    def run(self, path: str) -> ToolResult:
        try:
            target = _safe_path(path)
            
            if not target.exists():
                return ToolResult(success=False, error=f"File not found: {path}")
            
            if not target.is_file():
                return ToolResult(success=False, error=f"Not a file: {path}")
            
            target.unlink()
            return ToolResult(success=True, output=f"Deleted: {path}")
        
        except Exception as e:
            return ToolResult(success=False, error=str(e))


if __name__ == "__main__":
    from rich.console import Console
    console = Console()
    
    console.print("\n[bold magenta]Filesystem Tools Test[/bold magenta]\n")
    
    # Test write
    writer = WriteFileTool()
    r = writer.run("demo/hello.txt", "Hello from AegisOS!")
    console.print(f"Write: {r.success} | {r.output or r.error}")
    
    # Test read
    reader = ReadFileTool()
    r = reader.run("demo/hello.txt")
    console.print(f"Read: {r.success} | {r.output or r.error}")
    
    # Test list
    lister = ListFilesTool()
    r = lister.run("demo")
    console.print(f"List: {r.success} | {r.output or r.error}")
    
    # Test security
    r = reader.run("../../../etc/passwd")
    console.print(f"Security test: {r.success} | {r.error}")
    
    # Test delete
    deleter = DeleteFileTool()
    r = deleter.run("demo/hello.txt")
    console.print(f"Delete: {r.success} | {r.output or r.error}")