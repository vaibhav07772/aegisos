"""Executor — runs LLM calls with fallback logic"""
import logging
from typing import Optional
from rich.console import Console

from src.utils.llm_client import get_llm, safe_invoke
from src.core.model_registry import ModelRegistry
from src.core.decision_log import DecisionLog
from src.core.rate_limiter import RateLimiter

console = Console()
logger = logging.getLogger(__name__)


class Executor:
    """Executes queries using selected model with fallback"""
    
    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or ModelRegistry()
        self.limiter = RateLimiter()
    
    def execute(self, query: str, decision: DecisionLog) -> dict:
        """
        Execute query with selected model. Fall back if needed.
        
        Returns:
            {
                "answer": str,
                "model_used": str,
                "fallback_used": bool,
                "success": bool,
                "error": str | None,
                "attempts": list,
            }
        """
        result = {
            "answer": "",
            "model_used": "",
            "fallback_used": False,
            "success": False,
            "error": None,
            "attempts": [],
        }
        
        # Build attempt list: primary + fallback
        attempts = [decision.selected_model_id]
        if decision.fallback_model_id:
            attempts.append(decision.fallback_model_id)
        
        for i, model_id in enumerate(attempts):
            model = self.registry.get_model(model_id)
            if not model:
                continue
            
            attempt_info = {
                "model_id": model_id,
                "model_name": model.name,
                "is_fallback": i > 0,
                "success": False,
                "error": None,
            }
            
            console.print(f"\n[cyan]Attempt {i+1}: {model_id} ({model.name})[/cyan]")
            
            try:
                answer = self._call_llm(model.name, query)
                result["answer"] = answer
                result["model_used"] = model_id
                result["fallback_used"] = i > 0
                result["success"] = True
                attempt_info["success"] = True
                result["attempts"].append(attempt_info)
                
                # Record usage (rough estimate)
                est_tokens = decision.estimated_tokens
                self.limiter.record_usage(model_id, est_tokens)
                
                console.print(f"   [green]Success[/green] (est {est_tokens} tokens)")
                break
                
            except Exception as e:
                logger.warning(f"Model {model_id} failed: {e}")
                attempt_info["error"] = str(e)[:200]
                result["attempts"].append(attempt_info)
                console.print(f"   [red]Failed: {str(e)[:100]}[/red]")
                continue
        
        if not result["success"]:
            result["error"] = "All models failed"
        
        return result
    
    def _call_llm(self, model_name: str, query: str) -> str:
        """Single LLM call"""
        llm = get_llm(model_name=model_name, temperature=0.3, max_tokens=1500)
        response = safe_invoke(llm, query)
        return response.content.strip()


if __name__ == "__main__":
    console.print("\n" + "="*70)
    console.print("[bold magenta]AegisOS Executor - Test[/bold magenta]")
    console.print("="*70)
    
    from src.core.intent_analyzer import IntentAnalyzer
    from src.core.decision_engine import DecisionEngine
    
    analyzer = IntentAnalyzer()
    engine = DecisionEngine()
    executor = Executor()
    
    query = "What is the capital of France?"
    console.print(f"\n[bold]Query:[/bold] {query}\n")
    
    intent = analyzer.analyze(query)
    decision = engine.decide(query, intent)
    
    console.print(f"\n[cyan]Selected model:[/cyan] {decision.selected_model_id}")
    console.print(f"[cyan]Fallback:[/cyan] {decision.fallback_model_id}")
    
    result = executor.execute(query, decision)
    
    console.print(f"\n{'='*70}")
    console.print("[bold green]RESULT[/bold green]")
    console.print(f"{'='*70}")
    console.print(f"Answer: {result['answer']}")
    console.print(f"Model used: {result['model_used']}")
    console.print(f"Fallback used: {result['fallback_used']}")
    console.print(f"Success: {result['success']}")