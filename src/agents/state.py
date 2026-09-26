"""AegisOS shared state for LangGraph multi-agent system"""
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class PlanStep(BaseModel):
    """Single step in the plan"""
    step_id: int
    description: str
    tool_needed: Optional[str] = None  # e.g., "filesystem", "github", None
    status: Literal["pending", "in_progress", "completed", "failed"] = "pending"
    result: Optional[str] = None
    error: Optional[str] = None


class AgentState(BaseModel):
    """
    Shared state passed between agents in the LangGraph.
    
    Flow: Planner → Executor → Verifier → (retry or done)
    """
    # ─── INPUT ───
    user_query: str = ""
    task_type: str = ""
    complexity: str = "low"
    tools_needed: List[str] = Field(default_factory=list)
    max_steps: int = 5
    
    # ─── PLAN (from Planner) ───
    plan: List[PlanStep] = Field(default_factory=list)
    plan_reasoning: str = ""
    
    # ─── EXECUTION (from Executor) ───
    current_step_index: int = 0
    execution_log: List[Dict] = Field(default_factory=list)
    
    # ─── VERIFICATION (from Verifier) ───
    verification_status: Literal["pending", "approved", "needs_retry", "rejected"] = "pending"
    verification_reason: str = ""
    retry_count: int = 0
    max_retries: int = 2
    
    # ─── FINAL OUTPUT ───
    final_answer: str = ""
    success: bool = False
    
    # ─── META ───
    decision_id: str = ""
    selected_model: str = ""
    started_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    
    def get_current_step(self) -> Optional[PlanStep]:
        """Get current step being worked on"""
        if 0 <= self.current_step_index < len(self.plan):
            return self.plan[self.current_step_index]
        return None
    
    def all_steps_complete(self) -> bool:
        """Check if all plan steps are done"""
        if not self.plan:
            return False
        return all(s.status in ("completed", "failed") for s in self.plan)


if __name__ == "__main__":
    from rich.console import Console
    
    console = Console()
    console.print("\n[bold magenta]Agent State Test[/bold magenta]\n")
    
    state = AgentState(
        user_query="Fix my GitHub project",
        task_type="code_generation",
        complexity="high",
        tools_needed=["filesystem", "github"],
    )
    
    # Simulate a plan
    state.plan = [
        PlanStep(step_id=1, description="Clone repo", tool_needed="github"),
        PlanStep(step_id=2, description="Analyze code", tool_needed="filesystem"),
        PlanStep(step_id=3, description="Add tests", tool_needed="filesystem"),
    ]
    
    console.print(f"Query: {state.user_query}")
    console.print(f"Plan: {len(state.plan)} steps")
    console.print(f"Current step: {state.get_current_step().description}")
    console.print(f"All complete? {state.all_steps_complete()}")
    
    # Mark first as done
    state.plan[0].status = "completed"
    state.current_step_index = 1
    console.print(f"\nAfter step 1 done:")
    console.print(f"Current step: {state.get_current_step().description}")
    console.print(f"All complete? {state.all_steps_complete()}")