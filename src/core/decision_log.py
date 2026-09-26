"""Decision Log — structured, transparent decision output"""
from datetime import datetime
from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from pydantic import BaseModel

console = Console()


class DecisionLog(BaseModel):
    """Transparent decision record for every request"""
    
    # Input
    user_query: str
    
    # Intent analysis
    task_type: str
    complexity: str
    risk_level: str
    requires_tools: bool
    tools_needed: List[str]
    estimated_tokens: int
    
    # Model selection
    selected_model_id: str
    selected_model_name: str
    selected_model_tier: str
    fallback_model_id: Optional[str] = None
    selection_reason: str = ""
    
    # Rate limit
    tpm_limit: int = 8000
    quota_impact_pct: float = 0.0
    
    # Projection
    projected_cost_usd: float = 0.0
    
    # Meta
    timestamp: str = ""
    decision_id: str = ""


def render_decision_log(log: DecisionLog):
    """Pretty-print decision log"""
    
    console.print("\n" + "="*70)
    console.print(Panel.fit(
        "[bold yellow]DECISION LOG[/bold yellow]",
        border_style="yellow",
    ))
    
    # Input
    console.print(f"\n[bold]INPUT[/bold]")
    console.print(f"   Query: {log.user_query[:100]}")
    console.print(f"   Time: {log.timestamp[:19]}")
    console.print(f"   ID: {log.decision_id}")
    
    # Intent
    console.print(f"\n[bold]INTENT ANALYSIS[/bold]")
    console.print(f"   Task Type:   [cyan]{log.task_type}[/cyan]")
    console.print(f"   Complexity:  [yellow]{log.complexity}[/yellow]")
    console.print(f"   Risk Level:  [red]{log.risk_level}[/red]")
    console.print(f"   Requires Tools: {log.requires_tools}")
    if log.tools_needed:
        console.print(f"   Tools: {', '.join(log.tools_needed)}")
    
    # Model selection
    console.print(f"\n[bold]MODEL SELECTION[/bold]")
    console.print(f"   Selected:    [green]{log.selected_model_id}[/green]")
    console.print(f"   Groq Name:   {log.selected_model_name}")
    console.print(f"   Tier:        {log.selected_model_tier}")
    if log.fallback_model_id:
        console.print(f"   Fallback:    [dim]{log.fallback_model_id}[/dim]")
    console.print(f"   Reason:      {log.selection_reason}")
    
    # Rate limit
    console.print(f"\n[bold]RATE LIMIT BUDGET[/bold]")
    console.print(f"   Est Tokens:  {log.estimated_tokens:,}")
    console.print(f"   TPM Limit:   {log.tpm_limit:,}")
    console.print(f"   Quota Impact: [yellow]{log.quota_impact_pct:.1f}%[/yellow]")
    
    # Cost projection
    console.print(f"\n[bold]COST PROJECTION[/bold]")
    console.print(f"   If using GPT-4:  [dim]${log.projected_cost_usd:.4f}[/dim]")
    console.print(f"   Actual (Groq):   [green]$0.0000[/green]")
    
    console.print("\n" + "="*70 + "\n")