"""AegisOS — Main CLI entry point"""
import sys
import logging
from rich.console import Console
from rich.panel import Panel

from src.core.intent_analyzer import IntentAnalyzer
from src.core.decision_engine import DecisionEngine
from src.core.decision_log import render_decision_log
from src.core.executor import Executor
from src.core.rate_limiter import RateLimiter

logging.basicConfig(level=logging.WARNING)
console = Console()


def run_aegis(query: str):
    """Full pipeline: analyze → decide → execute"""
    
    console.print("\n" + "="*70)
    console.print(Panel.fit(
        "[bold magenta]AegisOS — AI Operating System[/bold magenta]\n"
        "[dim]Intent -> Decision -> Execution[/dim]",
        border_style="magenta",
    ))
    
    # Initialize
    analyzer = IntentAnalyzer()
    engine = DecisionEngine()
    executor = Executor()
    
    # 1. Analyze intent
    intent = analyzer.analyze(query)
    
    # 2. Make decision
    decision = engine.decide(query, intent)
    render_decision_log(decision)
    
    # 3. Execute
    console.print("\n[bold cyan]EXECUTION[/bold cyan]")
    result = executor.execute(query, decision)
    
    # 4. Display result
    console.print("\n" + "="*70)
    console.print("[bold green]FINAL ANSWER[/bold green]")
    console.print("="*70 + "\n")
    console.print(result["answer"])
    
    console.print(f"\n[dim]Model: {result['model_used']} | "
                  f"Fallback: {result['fallback_used']} | "
                  f"Success: {result['success']}[/dim]")
    
    return result


def show_usage():
    """Show current rate limit usage"""
    from rich.table import Table
    
    limiter = RateLimiter()
    stats = limiter.get_all_stats()
    
    if not stats:
        console.print("\n[yellow]No usage data yet[/yellow]\n")
        return
    
    table = Table(title="Rate Limit Status")
    table.add_column("Model", style="cyan")
    table.add_column("Tokens Today", style="yellow")
    table.add_column("Requests", style="white")
    table.add_column("Remaining", style="green")
    table.add_column("Usage %", style="red")
    
    for model_id, s in stats.items():
        table.add_row(
            model_id,
            f"{s['tokens_used_today']:,}",
            str(s["requests_today"]),
            f"{s['remaining']:,}",
            f"{s['usage_pct']:.1f}%",
        )
    
    console.print(table)


def main():
    if len(sys.argv) < 2:
        console.print("[yellow]Usage: python main.py '<query>'[/yellow]")
        console.print("[dim]       python main.py usage   (show rate limits)[/dim]")
        return
    
    if sys.argv[1] == "usage":
        show_usage()
        return
    
    query = " ".join(sys.argv[1:])
    run_aegis(query)


if __name__ == "__main__":
    main()