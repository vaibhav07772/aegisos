"""Model registry — loads Groq models from configs/models.yaml"""
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel


class ModelInfo(BaseModel):
    id: str
    provider: str
    name: str
    tier: str
    max_tokens: int
    strengths: List[str]
    weaknesses: List[str]
    rate_limit_tpm: int


class TaskType(BaseModel):
    name: str
    complexity: str
    preferred_models: List[str]
    requires_tools: bool
    risk_level: str
    est_tokens: int


class ModelRegistry:
    """Registry of available Groq models and task types"""
    
    def __init__(self, config_path: str = "configs/models.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        self.models: Dict[str, ModelInfo] = {}
        for model_id, data in config["models"].items():
            self.models[model_id] = ModelInfo(id=model_id, **data)
        
        self.task_types: Dict[str, TaskType] = {}
        for task_name, data in config["task_types"].items():
            self.task_types[task_name] = TaskType(name=task_name, **data)
    
    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        return self.models.get(model_id)
    
    def get_task_type(self, name: str) -> Optional[TaskType]:
        return self.task_types.get(name)
    
    def list_models(self) -> List[str]:
        return list(self.models.keys())
    
    def list_task_types(self) -> List[str]:
        return list(self.task_types.keys())


if __name__ == "__main__":
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    registry = ModelRegistry()
    
    # Models table
    table = Table(title="🤖 AegisOS Model Registry (Groq)")
    table.add_column("ID", style="cyan")
    table.add_column("Groq Name", style="white")
    table.add_column("Tier", style="yellow")
    table.add_column("TPM Limit", style="green")
    table.add_column("Strengths", style="magenta")
    
    for m in registry.models.values():
        table.add_row(
            m.id, m.name, m.tier,
            f"{m.rate_limit_tpm:,}",
            ", ".join(m.strengths[:2])
        )
    
    console.print(table)
    console.print()
    
    # Task types table
    table2 = Table(title="📋 Task Routing Rules")
    table2.add_column("Task", style="cyan")
    table2.add_column("Complexity", style="yellow")
    table2.add_column("Preferred Models", style="green")
    table2.add_column("Risk", style="red")
    table2.add_column("Est Tokens", style="white")
    
    for t in registry.task_types.values():
        table2.add_row(
            t.name, t.complexity,
            ", ".join(t.preferred_models[:2]),
            t.risk_level,
            str(t.est_tokens)
        )
    
    console.print(table2)
    
    console.print(f"\n✅ Total models: {len(registry.models)}")
    console.print(f"✅ Total task types: {len(registry.task_types)}")