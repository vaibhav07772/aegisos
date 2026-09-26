"""LangGraph orchestration — Planner → Executor → Verifier with retry"""
import logging
from typing import Literal
from rich.console import Console

from langgraph.graph import StateGraph, END

from src.agents.state import AgentState
from src.agents.planner import PlannerAgent
from src.agents.executor_agent import ExecutorAgent
from src.agents.verifier import VerifierAgent

console = Console()
logger = logging.getLogger(__name__)


# ─── Singleton agents ───
_planner = None
_executor = None
_verifier = None


def get_agents():
    global _planner, _executor, _verifier
    if _planner is None:
        _planner = PlannerAgent()
        _executor = ExecutorAgent()
        _verifier = VerifierAgent()
    return _planner, _executor, _verifier


# ─── Node functions ───
def planner_node(state: AgentState) -> dict:
    """Plan the task"""
    console.print(f"\n[bold magenta]NODE: Planner[/bold magenta]")
    planner, _, _ = get_agents()
    updated_state = planner.plan(state)
    return updated_state.model_dump()


def executor_node(state: AgentState) -> dict:
    """Execute the plan"""
    console.print(f"\n[bold magenta]NODE: Executor (attempt {state.retry_count + 1})[/bold magenta]")
    _, executor, _ = get_agents()
    updated_state = executor.execute_plan(state)
    return updated_state.model_dump()


def verifier_node(state: AgentState) -> dict:
    """Verify execution"""
    console.print(f"\n[bold magenta]NODE: Verifier[/bold magenta]")
    _, _, verifier = get_agents()
    updated_state = verifier.verify(state)
    return updated_state.model_dump()


# ─── Routing logic (NO state mutation here!) ───
def route_after_verification(state: AgentState) -> Literal["retry", "end"]:
    """
    Decide: retry execution or finish.
    
    IMPORTANT: Don't mutate state here — LangGraph ignores it.
    Return route name only.
    """
    status = state.verification_status
    
    if status == "approved":
        console.print(f"\n[green]✅ Approved — finishing[/green]")
        return "end"
    
    if status == "needs_retry":
        if state.retry_count < state.max_retries:
            console.print(f"\n[yellow]🔄 Retry {state.retry_count + 1}/{state.max_retries} needed[/yellow]")
            return "retry"
        else:
            console.print(f"\n[red]⛔ Max retries reached — finishing[/red]")
            return "end"
    
    # rejected
    console.print(f"\n[red]❌ Rejected — finishing[/red]")
    return "end"


def retry_node(state: AgentState) -> dict:
    """
    Prepare state for retry.
    - Increment retry counter
    - Reset plan step statuses
    This runs as a proper node so state changes persist.
    """
    console.print(f"\n[bold yellow]NODE: Preparing retry {state.retry_count + 1}[/bold yellow]")
    
    # Increment retry counter
    state.retry_count += 1
    
    # Reset plan steps for retry
    for step in state.plan:
        step.status = "pending"
        step.result = None
        step.error = None
    
    # Reset execution tracking
    state.current_step_index = 0
    state.execution_log = []
    state.final_answer = ""
    state.success = False
    
    return state.model_dump()


# ─── Build the graph ───
def build_graph():
    """Build the multi-agent LangGraph"""
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("verifier", verifier_node)
    graph.add_node("retry_prep", retry_node)
    
    # Entry
    graph.set_entry_point("planner")
    
    # Linear flow
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "verifier")
    
    # Conditional after verifier
    graph.add_conditional_edges(
        "verifier",
        route_after_verification,
        {
            "retry": "retry_prep",
            "end": END,
        },
    )
    
    # Retry prep → executor
    graph.add_edge("retry_prep", "executor")
    
    return graph.compile()


if __name__ == "__main__":
    from src.agents.state import AgentState
    
    console.print("\n" + "="*70)
    console.print("[bold magenta]AegisOS Multi-Agent Graph Test[/bold magenta]")
    console.print("="*70)
    
    app = build_graph()
    
    # Test query — max_retries=1 for quicker test
    initial_state = AgentState(
        user_query="How many open issues are in vaibhav07772/aegisos repo?",
        task_type="simple_qa",
        complexity="low",
        tools_needed=["github"],
        max_steps=3,
        max_retries=1,
    )
    
    console.print(f"\n[bold]Query:[/bold] {initial_state.user_query}")
    console.print(f"[bold]Max retries:[/bold] {initial_state.max_retries}")
    
    # Recursion limit badhao for safety
    config = {"recursion_limit": 50}
    
    try:
        final_state = app.invoke(initial_state, config=config)
        
        console.print(f"\n{'='*70}")
        console.print("[bold green]GRAPH COMPLETE[/bold green]")
        console.print(f"{'='*70}")
        console.print(f"Query: {final_state['user_query']}")
        console.print(f"Verdict: {final_state['verification_status']}")
        console.print(f"Retries used: {final_state['retry_count']}/{final_state['max_retries']}")
        console.print(f"Steps in plan: {len(final_state['plan'])}")
        console.print(f"Final answer: {final_state['final_answer'][:300]}")
        
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")