"""Executor Agent — executes plan steps with tools"""
import json
import logging
from rich.console import Console

from src.utils.llm_client import get_llm, safe_invoke
from src.agents.state import AgentState, PlanStep
from src.tools.registry import ToolRegistry

console = Console()
logger = logging.getLogger(__name__)


EXECUTOR_PROMPT = """You are an Executor Agent for AegisOS.

Your job: Execute ONE step of a larger plan.

PLAN CONTEXT:
{plan_context}

CURRENT STEP (execute only this):
Step {step_id}: {step_description}
Tool needed: {tool_needed}

PREVIOUS RESULTS:
{previous_results}

AVAILABLE TOOLS:
{tools}

Decide how to execute the current step.

Return ONLY valid JSON:
{{
  "thought": "Brief reasoning about how to execute",
  "action": "tool_name" or "reasoning",
  "action_input": {{...}},
  "step_complete": true,
  "step_result": "Summary of what was accomplished"
}}

If the step is pure reasoning (no tool needed), use:
{{
  "thought": "...",
  "action": "reasoning",
  "action_input": {{}},
  "step_complete": true,
  "step_result": "your reasoning result"
}}

Start with {{ and end with }}."""


class ExecutorAgent:
    """Executes plan steps sequentially"""
    
    def __init__(self, model_name: str = "openai/gpt-oss-120b"):
        self.model_name = model_name
        self.llm = get_llm(model_name=model_name, temperature=0.1, json_mode=True)
        self.registry = ToolRegistry()
        console.print(f"[cyan]Executor initialized (model: {model_name})[/cyan]")
    
    def execute_plan(self, state: AgentState) -> AgentState:
        """Execute all plan steps"""
        console.print(f"\n[bold cyan]EXECUTOR[/bold cyan]")
        console.print(f"   Plan: {len(state.plan)} steps")
        
        for step in state.plan:
            if step.status == "completed":
                continue
            
            self._execute_step(state, step)
            
            # Stop if this step failed
            if step.status == "failed":
                console.print(f"   [red]Step {step.step_id} failed. Stopping.[/red]")
                break
        
        # Set final answer based on last step
        if state.plan and state.plan[-1].status == "completed":
            state.final_answer = state.plan[-1].result or ""
            state.success = True
        
        return state
    
    def _execute_step(self, state: AgentState, step: PlanStep):
        """Execute a single step"""
        step.status = "in_progress"
        
        console.print(f"\n[bold]Step {step.step_id}:[/bold] {step.description[:80]}")
        if step.tool_needed:
            console.print(f"   Tool: [cyan]{step.tool_needed}[/cyan]")
        
        # Build context
        plan_context = "\n".join([
            f"  {s.step_id}. [{s.status}] {s.description}"
            for s in state.plan
        ])
        
        previous_results = "None" if not state.execution_log else "\n".join([
            f"Step {log['step_id']}: {log.get('result', 'N/A')[:200]}"
            for log in state.execution_log
        ])
        
        tools_desc = "\n".join([
            f"- {t.name}: {t.description}"
            for t in self.registry.get_tools_for_task(state.tools_needed or ["filesystem"])
        ])
        
        prompt = EXECUTOR_PROMPT.format(
            plan_context=plan_context,
            step_id=step.step_id,
            step_description=step.description,
            tool_needed=step.tool_needed or "reasoning",
            previous_results=previous_results,
            tools=tools_desc,
        )
        
        # Get LLM decision
        try:
            response = safe_invoke(self.llm, prompt)
            raw = response.content.strip()
            
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            
            decision = json.loads(raw)
        except Exception as e:
            logger.error(f"Executor LLM error: {e}")
            step.status = "failed"
            step.error = f"LLM error: {e}"
            return
        
        thought = decision.get("thought", "")
        action = decision.get("action", "reasoning")
        action_input = decision.get("action_input", {})
        step_result = decision.get("step_result", "")
        
        console.print(f"   [yellow]Thought:[/yellow] {thought[:100]}")
        console.print(f"   [cyan]Action:[/cyan] {action}")
        
        # Execute
        result_output = None
        
        if action == "reasoning" or action == "":
            # Pure reasoning — no tool call
            result_output = step_result
            console.print(f"   [green]Reasoned:[/green] {step_result[:200]}")
        else:
            # Tool call
            tool_result = self.registry.execute(action, action_input)
            if tool_result.success:
                result_output = tool_result.output
                console.print(f"   [green]Success:[/green] {str(result_output)[:200]}")
            else:
                step.status = "failed"
                step.error = tool_result.error
                console.print(f"   [red]Tool failed:[/red] {tool_result.error[:200]}")
                state.execution_log.append({
                    "step_id": step.step_id,
                    "action": action,
                    "success": False,
                    "error": tool_result.error,
                })
                return
        
        # Update step
        step.status = "completed"
        step.result = str(result_output)[:2000]  # Cap at 2K chars
        state.execution_log.append({
            "step_id": step.step_id,
            "action": action,
            "success": True,
            "result": step.result,
        })


if __name__ == "__main__":
    console.print("\n" + "="*70)
    console.print("[bold magenta]Executor Agent Test[/bold magenta]")
    console.print("="*70)
    
    from src.agents.planner import PlannerAgent
    from src.agents.state import AgentState
    
    planner = PlannerAgent()
    executor = ExecutorAgent()
    
    # Test: fibonacci file creation
    state = AgentState(
        user_query="Create a Python file 'fib.py' that calculates fibonacci numbers",
        task_type="code_generation",
        complexity="medium",
        tools_needed=["filesystem"],
        max_steps=4,
    )
    
    # Plan
    state = planner.plan(state)
    
    # Execute
    state = executor.execute_plan(state)
    
    # Show final
    console.print(f"\n{'='*70}")
    console.print("[bold green]EXECUTION COMPLETE[/bold green]")
    console.print(f"{'='*70}")
    console.print(f"Success: {state.success}")
    console.print(f"Steps executed: {len(state.execution_log)}")
    console.print(f"Final answer: {state.final_answer[:300]}")
    
    # Cleanup
    executor.registry.execute("delete_file", {"path": "fib.py"})