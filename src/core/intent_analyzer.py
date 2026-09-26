"""Intent Analyzer — converts user query to structured intent"""
import json
import logging
from rich.console import Console
from pydantic import BaseModel, Field
from typing import List

from src.utils.llm_client import get_llm, safe_json_invoke

console = Console()
logger = logging.getLogger(__name__)


INTENT_PROMPT = """You are an Intent Analyzer for an AI Operating System.

Your job: Analyze the user's query and extract structured intent.

Analyze these dimensions:
1. **task_type**: One of:
   - simple_qa (basic questions, definitions)
   - code_generation (write code, build features)
   - code_review (review, audit, debug code)
   - complex_analysis (deep analysis, research, strategy)
   - research (explore, investigate, gather info)
   - automation (set up workflows, scripts, pipelines)
   - routing (simple routing/classification tasks)

2. **complexity**: low | medium | high

3. **risk_level**: low | medium | high
   (based on: affects production? sensitive data? irreversible?)

4. **requires_tools**: true/false
   (does it need file access, git, browser, etc.?)

5. **tools_needed**: List of tools (can be empty):
   - filesystem, github, browser, shell, python

6. **estimated_tokens**: Rough output token estimate (integer)

Return ONLY valid JSON (no markdown):
{
  "task_type": "code_generation",
  "complexity": "high",
  "risk_level": "medium",
  "requires_tools": true,
  "tools_needed": ["filesystem", "github"],
  "estimated_tokens": 4000,
  "reasoning": "Brief explanation of analysis"
}

Start with { and end with }."""


class Intent(BaseModel):
    """Structured intent extracted from user query"""
    task_type: str
    complexity: str
    risk_level: str
    requires_tools: bool
    tools_needed: List[str] = Field(default_factory=list)
    estimated_tokens: int
    reasoning: str = ""


class IntentAnalyzer:
    """Analyzes user query → structured intent"""
    
    def __init__(self, model: str = "openai/gpt-oss-20b"):
        # Use fast small model for intent analysis
        self.llm = get_llm(model_name=model, temperature=0.0, json_mode=True)
        console.print(f"[cyan]🔧 Intent Analyzer initialized (model: {model})[/cyan]")
    
    def analyze(self, query: str) -> Intent:
        """Analyze user query and return Intent"""
        console.print(f"\n[cyan]🧠 Analyzing intent...[/cyan]")
        console.print(f"   Query: {query[:100]}{'...' if len(query) > 100 else ''}")
        
        prompt = f"{INTENT_PROMPT}\n\nUSER QUERY:\n{query}"
        
        try:
            result = safe_json_invoke(self.llm, prompt)
        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            # Fallback
            result = {
                "task_type": "simple_qa",
                "complexity": "low",
                "risk_level": "low",
                "requires_tools": False,
                "tools_needed": [],
                "estimated_tokens": 500,
                "reasoning": f"Fallback due to error: {e}",
            }
        
        intent = Intent(**result)
        
        console.print(f"   ✅ Task: {intent.task_type}")
        console.print(f"   ✅ Complexity: {intent.complexity}")
        console.print(f"   ✅ Risk: {intent.risk_level}")
        console.print(f"   ✅ Tools: {intent.tools_needed}")
        
        return intent


if __name__ == "__main__":
    import sys
    
    analyzer = IntentAnalyzer()
    
    # Test queries
    test_queries = [
        "What is the capital of France?",
        "Write a Python function to check if a number is prime",
        "My GitHub project is not production-ready. Make it production-ready.",
        "Review my code for security vulnerabilities",
        "Research latest trends in RAG systems",
    ]
    
    for q in test_queries:
        console.print(f"\n{'='*70}")
        intent = analyzer.analyze(q)
        console.print(f"[dim]Reasoning: {intent.reasoning}[/dim]")