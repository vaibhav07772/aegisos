"""Planner Agent — decomposes user query into plan steps"""
import json
import logging
from typing import List
from rich.console import Console

from src.utils.llm_client import get_llm, safe_invoke
from src.agents.state import AgentState, PlanStep

console = Console()
logger = logging.getLogger(__name__)


PLANNER_PROMPT = """You are a Planner Agent for AegisOS.

Your job: Given a user query and available tools, create a concise step-by-step plan.

USER QUERY:
{query}

AVAILABLE TOOLS:
{tools}

RULES:
1. Maximum {max_steps} steps
2. Each step should be atomic and actionable
3. Specify which tool each step needs (or null if just reasoning)
4. Focus on solving the user's actual problem
5. Don't add unnecessary steps

Return ONLY valid JSON:
{{
  "reasoning": "Brief explanation of your planning approach",
  "steps": [
    {{
      "step_id": 1,
      "description": "Concrete action to take",
      "tool_needed": "filesystem" or "github" or null
    }}
  ]
}}

Start with {{ and end with }}."""


class PlannerAgent:
    """Creates execution plans from user queries"""
    
    def __init__(self, model_name: str = "openai/gpt-oss-120b"):
        self.model_name = model_name
        self.llm = get_llm(model_name=model_name, temperature=0.3, json_mode=True)
        console.print(f"[cyan]Planner initialized (model: {model_name})[/cyan]")
    
    def plan(self, state: AgentState) -> AgentState:
        """Generate plan from state"""
        console.print(f"\n[bold cyan]PLANNER[/bold cyan]")
        console.print(f"   Query: {state.user_query[:80]}")
        console.print(f"   Tools: {state.tools_needed}")
        
        tools_str = ", ".join(state.tools_needed) if state.tools_needed else "none"
        
        prompt = PLANNER_PROMPT.format(
            query=state.user_query,
            tools=tools_str,
            max_steps=state.max_steps,
        )
        
        try:
            response = safe_invoke(self.llm, prompt)
            raw = response.content.strip()
            
            # Strip markdown fences
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            
            data = json.loads(raw)
            
        except Exception as e:
            logger.error(f"Planner error: {e}")
            # Fallback: single-step plan
            data = {
                "reasoning": f"Planner failed: {e}. Using single-step fallback.",
                "steps": [{
                    "step_id": 1,
                    "description": f"Answer query: {state.user_query}",
                    "tool_needed": None,
                }],
            }
        
        # Parse steps
        steps = []
        for s in data.get("steps", [])[:state.max_steps]:
            steps.append(PlanStep(
                step_id=s.get("step_id", len(steps) + 1),
                description=s.get("description", ""),
                tool_needed=s.get("tool_needed"),
                status="pending",
            ))
        
        state.plan = steps
        state.plan_reasoning = data.get("reasoning", "")
        state.current_step_index = 0
        
        # Display
        console.print(f"   [green]Plan created: {len(steps)} steps[/green]")
        for s in steps:
            tool_str = f"[dim]({s.tool_needed})[/dim]" if s.tool_needed else ""
            console.print(f"     {s.step_id}. {s.description} {tool_str}")
        console.print(f"   [dim]Reasoning: {state.plan_reasoning[:100]}[/dim]")
        
        return state


if __name__ == "__main__":
    from src.agents.state import AgentState
    
    console.print("\n[bold magenta]Planner Agent Test[/bold magenta]\n")
    
    planner = PlannerAgent()
    
    # Test queries
    test_cases = [
        {
            "query": "Read the README.md from vaibhav07772/aegisos repo and tell me what it's about",
            "tools": ["filesystem", "github"],
            "complexity": "low",
        },
        {
            "query": "Check how many open issues are in my aegisos repo",
            "tools": ["github"],
            "complexity": "low",
        },
        {
            "query": "Create a Python file that calculates fibonacci numbers and save it",
            "tools": ["filesystem"],
            "complexity": "medium",
        },
    ]
    
    for tc in test_cases:
        console.print("\n" + "="*70)
        state = AgentState(
            user_query=tc["query"],
            tools_needed=tc["tools"],
            complexity=tc["complexity"],
            max_steps=5,
        )
        state = planner.plan(state)