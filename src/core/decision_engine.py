"""Decision Engine — Jev-style routing"""
import uuid
import logging
from datetime import datetime
from typing import Optional
from rich.console import Console

from src.core.model_registry import ModelRegistry, ModelInfo, TaskType
from src.core.intent_analyzer import Intent
from src.core.decision_log import DecisionLog, render_decision_log

console = Console()
logger = logging.getLogger(__name__)


class DecisionEngine:
    """Routes user queries to optimal Groq models"""
    
    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or ModelRegistry()
        console.print("[cyan]Decision Engine initialized[/cyan]")
    
    def decide(self, query: str, intent: Intent) -> DecisionLog:
        """Main decision logic"""
        
        # 1. Get task type config
        task_config = self.registry.get_task_type(intent.task_type)
        if not task_config:
            logger.warning(f"Unknown task type: {intent.task_type}, using default")
            task_config = self.registry.get_task_type("simple_qa")
        
        # 2. Select best model
        selected_model = self._select_model(intent, task_config)
        fallback_model = self._select_fallback(intent, task_config, selected_model)
        
        # 3. Compute rate limit impact
        quota_impact = (intent.estimated_tokens / selected_model.rate_limit_tpm) * 100
        
        # 4. Project cost (if using GPT-4, ~$0.005/1K tokens)
        projected_cost = (intent.estimated_tokens / 1000) * 0.005
        
        # 5. Build selection reason
        reason = self._build_reason(intent, selected_model)
        
        # 6. Create decision log
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
    
    def _select_model(self, intent: Intent, task_config: TaskType) -> ModelInfo:
        """Select best model based on intent + task config"""
        for model_id in task_config.preferred_models:
            model = self.registry.get_model(model_id)
            if model:
                if intent.estimated_tokens <= model.max_tokens:
                    return model
        
        # Fallback to first preferred
        return self.registry.get_model(task_config.preferred_models[0])
    
    def _select_fallback(self, intent: Intent, task_config: TaskType,
                          selected: ModelInfo) -> Optional[ModelInfo]:
        """Select fallback model"""
        for model_id in task_config.preferred_models:
            if model_id != selected.id:
                model = self.registry.get_model(model_id)
                if model:
                    return model
        return None
    
    def _build_reason(self, intent: Intent, model: ModelInfo) -> str:
        """Build human-readable reason"""
        reasons = []
        
        if model.tier == "large":
            reasons.append(f"{intent.complexity} complexity requires large model")
        elif model.tier == "medium":
            reasons.append("balanced task - medium model sufficient")
        else:
            reasons.append("simple task - fast model optimal")
        
        if intent.requires_tools:
            reasons.append("tool use required")
        
        if intent.risk_level == "high":
            reasons.append("high-risk task needs reliable model")
        
        return " | ".join(reasons)


if __name__ == "__main__":
    from src.core.intent_analyzer import IntentAnalyzer
    
    console.print("\n" + "="*70)
    console.print("[bold magenta]AegisOS Decision Engine - Test[/bold magenta]")
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