"""Base tool classes for AegisOS"""
from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel


class ToolResult(BaseModel):
    """Standard result from any tool"""
    success: bool
    output: Any = None
    error: str = ""
    metadata: Dict = {}


class BaseTool(ABC):
    """Abstract base for all tools"""
    
    name: str = ""
    description: str = ""
    parameters: Dict = {}
    risk_level: str = "low"  # low | medium | high
    
    @abstractmethod
    def run(self, **kwargs) -> ToolResult:
        """Execute the tool"""
        pass
    
    def to_schema(self) -> Dict:
        """Return schema for LLM tool calling"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }