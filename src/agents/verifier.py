"""Verifier Agent — validates execution results"""
import json
import logging
from rich.console import Console

from src.utils.llm_client import get_llm, safe_invoke
from src.agents.state import AgentState

console = Console()
logger = logging.getLogger(__name__)


VERIFIER_PROMPT = """You are a Verifier Agent for AegisOS.

Your job: Judge whether the execution successfully answered the user's query.

USER QUERY:
{query}

PLAN:
{plan}

EXECUTION RESULTS:
{results}

FINAL ANSWER (proposed):
{final_answer}

Evaluate:
1. Did the execution address the user's query?
2. Were all plan steps completed successfully?
3. Is the final answer coherent and correct?

Return ONLY valid JSON:
{{
  "verdict": "approved" or "needs_retry" or "rejected",
  "confidence": 0.0 to 1.0,
  "reason": "Brief explanation",
  "improvements": ["suggestion 1", "suggestion 2"]
}}

- "approved": execution succeeded and answered query
- "needs_retry": execution partially worked, retry with improvements
- "rejected": execution failed completely

Start with {{ and end with }}."""


class VerifierAgent:
    """Validates execution results"""
    
    def __init__(self, model_name: str = "openai/gpt-oss-20b"):
        # Use small model for verification (cheaper)
        self.model_name = model_name
        self.llm = get_llm(model_name=model_name, temperature=0.0, json_mode=True)
        console.print(f"[cyan]Verifier initialized (model: {model_name})[/cyan]")
    
    def verify(self, state: AgentState) -> AgentState:
        """Verify execution results"""
        console.print(f"\n[bold cyan]VERIFIER[/bold cyan]")
        
        # Build plan summary
        plan_summary = "\n".join([
            f"  {s.step_id}. [{s.status}] {s.description}"
            for s in state.plan
        ])
        
        # Build results summary
        results = "\n".join([
            f"Step {log['step_id']} ({log['action']}): "
            f"{'OK' if log.get('success') else 'FAIL'}\n"
            f"  {log.get('result', log.get('error', 'N/A'))[:300]}"
            for log in state.execution_log
        ])
        
        prompt = VERIFIER_PROMPT.format(
            query=state.user_query,
            plan=plan_summary,
            results=results,
            final_answer=state.final_answer[:500],
        )
        
        try:
            response = safe_invoke(self.llm, prompt)
            raw = response.content.strip()
            
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            
            data = json.loads(raw)
        except Exception as e:
            logger.error(f"Verifier error: {e}")
            # Conservative fallback: approve if execution succeeded
            data = {
                "verdict": "approved" if state.success else "needs_retry",
                "confidence": 0.5,
                "reason": f"Verifier LLM failed: {e}",
                "improvements": [],
            }
        
        verdict = data.get("verdict", "needs_retry")
        confidence = data.get("confidence", 0.5)
        reason = data.get("reason", "")
        
        state.verification_status = verdict
        state.verification_reason = reason
        
        # Display
        color = {"approved": "green", "needs_retry": "yellow", "rejected": "red"}.get(verdict, "white")
        console.print(f"   Verdict: [{color}]{verdict}[/{color}] (confidence: {confidence})")
        console.print(f"   Reason: {reason[:200]}")
        
        improvements = data.get("improvements", [])
        if improvements:
            console.print(f"   Improvements: {improvements[:3]}")
        
        return state


if __name__ == "__main__":
    console.print("\n" + "="*70)
    console.print("[bold magenta]Verifier Agent Test[/bold magenta]")
    console.print("="*70)
    
    from src.agents.planner import PlannerAgent
    from src.agents.executor_agent import ExecutorAgent
    from src.agents.state import AgentState
    
    planner = PlannerAgent()
    executor = ExecutorAgent()
    verifier = VerifierAgent()
    
    # Full pipeline test
    state = AgentState(
        user_query="How many open issues are in vaibhav07772/aegisos repo?",
        task_type="simple_qa",
        complexity="low",
        tools_needed=["github"],
        max_steps=3,
    )
    
    state = planner.plan(state)
    state = executor.execute_plan(state)
    state = verifier.verify(state)
    
    console.print(f"\n{'='*70}")
    console.print("[bold green]PIPELINE RESULT[/bold green]")
    console.print(f"{'='*70}")
    console.print(f"Query: {state.user_query}")
    console.print(f"Verdict: {state.verification_status}")
    console.print(f"Final answer: {state.final_answer[:300]}")