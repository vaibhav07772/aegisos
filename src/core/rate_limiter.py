"""Rate Limit Manager — tracks Groq token usage per model"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel
from rich.console import Console

console = Console()

STATE_FILE = Path("data/rate_limit_state.json")


class ModelUsage(BaseModel):
    """Usage stats for a single model"""
    tokens_used_today: int = 0
    requests_today: int = 0
    last_reset: str = ""
    last_request: str = ""


class RateLimiter:
    """
    Tracks Groq token usage per model per day.
    Groq free tier: 200K tokens/day per model (approximately)
    """
    
    DAILY_LIMIT = 200_000  # tokens per model per day
    WARN_THRESHOLD = 0.8   # warn at 80%
    
    def __init__(self, state_file: Path = STATE_FILE):
        self.state_file = state_file
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.usage: Dict[str, ModelUsage] = self._load_state()
    
    def _load_state(self) -> Dict[str, ModelUsage]:
        """Load usage state from disk"""
        if not self.state_file.exists():
            return {}
        
        try:
            data = json.loads(self.state_file.read_text(encoding="utf-8"))
            return {
                model_id: ModelUsage(**stats)
                for model_id, stats in data.items()
            }
        except Exception as e:
            console.print(f"[yellow]Could not load rate state: {e}[/yellow]")
            return {}
    
    def _save_state(self):
        """Persist usage state"""
        data = {
            model_id: usage.model_dump()
            for model_id, usage in self.usage.items()
        }
        self.state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    
    def _reset_if_new_day(self, model_id: str):
        """Reset counters if day changed"""
        if model_id not in self.usage:
            self.usage[model_id] = ModelUsage(
                last_reset=datetime.now().date().isoformat()
            )
            return
        
        usage = self.usage[model_id]
        today = datetime.now().date().isoformat()
        
        if usage.last_reset != today:
            usage.tokens_used_today = 0
            usage.requests_today = 0
            usage.last_reset = today
    
    def check_capacity(self, model_id: str, estimated_tokens: int) -> dict:
        """
        Check if model has capacity for a request.
        
        Returns:
            {
                "can_proceed": bool,
                "reason": str,
                "remaining_tokens": int,
                "usage_pct": float,
            }
        """
        self._reset_if_new_day(model_id)
        usage = self.usage.get(model_id, ModelUsage())
        
        remaining = self.DAILY_LIMIT - usage.tokens_used_today
        usage_pct = (usage.tokens_used_today / self.DAILY_LIMIT) * 100
        
        if estimated_tokens > remaining:
            return {
                "can_proceed": False,
                "reason": f"insufficient_tokens: need {estimated_tokens}, have {remaining}",
                "remaining_tokens": remaining,
                "usage_pct": usage_pct,
            }
        
        if usage_pct >= self.WARN_THRESHOLD * 100:
            return {
                "can_proceed": True,
                "reason": f"warning: {usage_pct:.1f}% of daily limit used",
                "remaining_tokens": remaining,
                "usage_pct": usage_pct,
            }
        
        return {
            "can_proceed": True,
            "reason": "ok",
            "remaining_tokens": remaining,
            "usage_pct": usage_pct,
        }
    
    def record_usage(self, model_id: str, tokens_used: int):
        """Record actual token usage"""
        self._reset_if_new_day(model_id)
        
        if model_id not in self.usage:
            self.usage[model_id] = ModelUsage(
                last_reset=datetime.now().date().isoformat()
            )
        
        usage = self.usage[model_id]
        usage.tokens_used_today += tokens_used
        usage.requests_today += 1
        usage.last_request = datetime.now().isoformat()
        
        self._save_state()
    
    def get_stats(self, model_id: str) -> dict:
        """Get current usage stats for a model"""
        self._reset_if_new_day(model_id)
        usage = self.usage.get(model_id, ModelUsage())
        
        return {
            "model_id": model_id,
            "tokens_used_today": usage.tokens_used_today,
            "requests_today": usage.requests_today,
            "remaining": self.DAILY_LIMIT - usage.tokens_used_today,
            "usage_pct": (usage.tokens_used_today / self.DAILY_LIMIT) * 100,
            "last_request": usage.last_request,
        }
    
    def get_all_stats(self) -> Dict[str, dict]:
        """Get stats for all models"""
        return {model_id: self.get_stats(model_id) for model_id in self.usage}


if __name__ == "__main__":
    from rich.table import Table
    
    console.print("\n" + "="*70)
    console.print("[bold magenta]AegisOS Rate Limiter - Test[/bold magenta]")
    console.print("="*70)
    
    limiter = RateLimiter()
    
    # Simulate usage
    console.print("\n[cyan]Simulating usage...[/cyan]")
    limiter.record_usage("groq-gpt-oss-20b", 1500)
    limiter.record_usage("groq-gpt-oss-120b", 3000)
    limiter.record_usage("groq-qwen-27b", 2000)
    limiter.record_usage("groq-gpt-oss-20b", 800)
    
    # Check capacity
    console.print("\n[cyan]Capacity checks:[/cyan]")
    checks = [
        ("groq-gpt-oss-20b", 500),
        ("groq-gpt-oss-120b", 5000),
        ("groq-kimi-k2", 2000),
    ]
    
    for model_id, tokens in checks:
        result = limiter.check_capacity(model_id, tokens)
        status = "[green]OK[/green]" if result["can_proceed"] else "[red]BLOCKED[/red]"
        console.print(f"   {model_id} ({tokens} tokens): {status} - {result['reason']}")
    
    # Display all stats
    console.print()
    table = Table(title="Rate Limit Status")
    table.add_column("Model", style="cyan")
    table.add_column("Tokens Today", style="yellow")
    table.add_column("Requests", style="white")
    table.add_column("Remaining", style="green")
    table.add_column("Usage %", style="red")
    
    for model_id, stats in limiter.get_all_stats().items():
        table.add_row(
            model_id,
            f"{stats['tokens_used_today']:,}",
            str(stats["requests_today"]),
            f"{stats['remaining']:,}",
            f"{stats['usage_pct']:.1f}%",
        )
    
    console.print(table)