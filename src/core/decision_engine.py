"""Decision Engine — Jev-style routing with complexity + rate limit awareness"""
import uuid
import logging
from datetime import datetime
from typing import Optional
from rich.console import Console

from src.core.model_registry import ModelRegistry, ModelInfo, TaskType
from src.core.intent_analyzer import Intent
from src.core.decision_log import DecisionLog, render_decision_log
from src.core.rate_limiter import RateLimiter

console = Console()
logger = logging.getLogger(__name__)


class DecisionEngine:
    """Routes user queries to optimal Groq models"""
    
    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or ModelRegistry()
        self.limiter = RateLimiter()
        console.print("[cyan]Decision Engine initialized (rate limit aware)[/cyan]")
    
    def decide(self, query: str, intent: Intent) -> DecisionLog:
        """Main decision logic with rate limit awareness"""
        
        # 1. Get task type config
        task_config = self.registry.get_task_type(intent.task_type)
        if not task_config:
            logger.warning(f"Unknown task type: {intent.task_type}, using default")
            task_config = self.registry.get_task_type("simple_qa")
        
        # 2. Get complexity-aware preferred models
        preferred = task_config.get_preferred(intent.complexity)
        
        # 3. Select model with rate limit awareness
        selected_model = None
        selection_notes = []
        
        for model_id in preferred:
            model = self.registry.get_model(model_id)
            if not model:
                continue
            
            # Check max_tokens
            if intent.estimated_tokens > model.max_tokens:
                selection_notes.append(f"{model_id}: exceeds max_tokens")
                continue
            
            # Check rate limit
            capacity = self.limiter.check_capacity(model_id, intent.estimated_tokens)
            if not capacity["can_proceed"]:
                selection_notes.append(f"{model_id}: rate limited")
                continue
            
            selected_model = model
            if capacity["usage_pct"] >= 80:
                selection_notes.append(f"{model_id}: {capacity['usage_pct']:.0f}% used")
            break
        
        # Fallback if nothing selected
        if selected_model is None:
            selected_model = self.registry.get_model("groq-gpt-oss-20b")
            selection_notes.append("fallback to default")
        
        # 4. Select fallback (next available)
        fallback_model = None
        for model_id in preferred:
            if model_id != selected_model.id:
                model = self.registry.get_model(model_id)
                if model and intent.estimated_tokens <= model.max_tokens:
                    fallback_model = model
                    break
        
        # 5. Compute rate limit impact
        quota_impact = (intent.estimated_tokens / selected_model.rate_limit_tpm) * 100
        
        # 6. Project cost (if using GPT-4)
        projected_cost = (intent.estimated_tokens / 1000) * 0.005
        
        # 7. Build reason
        reason = self._build_reason(intent, selected_model)
        if selection_notes:
            reason += " | " + " | ".join(selection_notes)
        
        # 8. Create decision log
        log = DecisionLog(
            user_query=query,
            task_type=intent.task_type,
            complexity=intent.complexity,
            risk_level=intent.risk_level,
            requires_tools=intent.requires_tools,
            tools_needed=intent.tools_needed,
            estimated_tokens=intent.estimated_tokens,
            selected_model_id=selected_model.id,
            selected_model_name=selected_model.name,
            selected_model_tier=selected_model.tier,
            fallback_model_id=fallback_model.id if fallback_model else None,
            selection_reason=reason,
            tpm_limit=selected_model.rate_limit_tpm,
            quota_impact_pct=quota_impact,
            projected_cost_usd=projected_cost,
            timestamp=datetime.now().isoformat(),
            decision_id=str(uuid.uuid4())[:8],
        )
        
        return log
    
    def _build_reason(self, intent: Intent, model: ModelInfo) -> str:
        """Build human-readable reason"""
        reasons = []
        
        if intent.complexity == "high":
            reasons.append(f"high complexity -> {model.tier} model")
        elif intent.complexity == "medium":
            reasons.append(f"medium complexity -> {model.tier} model")
        else:
            reasons.append(f"low complexity -> {model.tier} model")
        
        if intent.requires_tools:
            reasons.append("tool use required")
        
        if intent.risk_level == "high":
            reasons.append("high-risk needs reliable model")
        
        return " | ".join(reasons)


if __name__ == "__main__":
    from src.core.intent_analyzer import IntentAnalyzer
    
    console.print("\n" + "="*70)
    console.print("[bold magenta]AegisOS Decision Engine - Full Test[/bold magenta]")
    console.print("="*70)
    
    analyzer = IntentAnalyzer()
    engine = DecisionEngine()
    
    test_queries = [
        "What is the capital of France?",
        "Write a Python function to check if a number is prime",
        "My GitHub project is not production-ready. Make it production-ready.",
        "Review my code for security vulnerabilities",
        "Research latest trends in RAG systems",
    ]
    
    for query in test_queries:
        intent = analyzer.analyze(query)
        log = engine.decide(query, intent)
        render_decision_log(log)