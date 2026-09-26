"""Tool Agent — LLM + tools with ReAct-style loop"""
import json
import logging
from typing import List, Dict
from rich.console import Console

from src.utils.llm_client import get_llm, safe_invoke
from src.tools.registry import ToolRegistry
from src.tools.base import BaseTool, ToolResult

console = Console()
logger = logging.getLogger(__name__)


REACT_SYSTEM_PROMPT = """You are an AI agent with access to tools.

You work in a ReAct-style loop:
1. Think about what to do next
2. Choose a tool and provide arguments
3. Observe the result
4. Repeat until the task is complete

Available tools:
{tools_description}

To use a tool, respond ONLY with valid JSON:
{{
  "thought": "Brief reasoning about what to do",
  "action": "tool_name",
  "action_input": {{...}}
}}

When you have the final answer, respond with:
{{
  "thought": "Task complete",
  "action": "final_answer",
  "action_input": {{"answer": "your final answer here"}}
}}

Rules:
- ONE tool call per turn
- Use only tools listed above
- Be concise
- If task is complete, use "final_answer"
"""


class ToolAgent:
    """Agent that uses LLM + tools in a loop"""
    
    MAX_STEPS = 5  # Prevent infinite loops
    
    def __init__(self, model_name: str = "openai/gpt-oss-120b",
                 max_tools: int = 8):
        self.model_name = model_name
        self.registry = ToolRegistry()
        self.llm = get_llm(model_name=model_name, temperature=0.1, json_mode=True)
        self.max_tools = max_tools
        
        console.print(f"[cyan]Tool Agent initialized (model: {model_name})[/cyan]")
    
    def _format_tools(self, tools: List[BaseTool]) -> str:
        """Format tools for prompt"""
        lines = []
        for t in tools:
            lines.append(f"- {t.name}: {t.description}")
            params = t.parameters.get("properties", {})
            if params:
                param_list = ", ".join(params.keys())
                lines.append(f"  Arguments: {param_list}")
        return "\n".join(lines)
    
    def run(self, query: str, tools_needed: List[str]) -> dict:
        """
        Run agent loop.
        
        Returns:
            {
                "answer": str,
                "steps": list,
                "success": bool,
                "error": str,
            }
        """
        result = {
            "answer": "",
            "steps": [],
            "success": False,
            "error": None,
        }
        
        # Get relevant tools
        tools = self.registry.get_tools_for_task(tools_needed)[:self.max_tools]
        
        if not tools:
            result["error"] = f"No tools available for: {tools_needed}"
            result["answer"] = "I don't have the required tools for this task."
            return result
        
        console.print(f"\n[cyan]Agent starting with {len(tools)} tools[/cyan]")
        console.print(f"[dim]Tools: {[t.name for t in tools]}[/dim]\n")
        
        # Build initial prompt
        tools_desc = self._format_tools(tools)
        system_prompt = REACT_SYSTEM_PROMPT.format(tools_description=tools_desc)
        
        conversation = f"User task: {query}\n\nWhat is your first action?"
        
        # Agent loop
        for step_num in range(1, self.MAX_STEPS + 1):
            console.print(f"[bold cyan]Step {step_num}[/bold cyan]")
            
            # Get LLM decision
            try:
                full_prompt = f"{system_prompt}\n\n{conversation}"
                response = safe_invoke(self.llm, full_prompt)
                raw = response.content.strip()
                
                # Parse JSON
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                    raw = raw.strip()
                
                decision = json.loads(raw)
            except Exception as e:
                logger.error(f"LLM parse error: {e}")
                result["error"] = f"LLM error: {e}"
                break
            
            thought = decision.get("thought", "")
            action = decision.get("action", "")
            action_input = decision.get("action_input", {})
            
            console.print(f"   [yellow]Thought:[/yellow] {thought[:100]}")
            console.print(f"   [cyan]Action:[/cyan] {action}")
            
            step_record = {
                "step": step_num,
                "thought": thought,
                "action": action,
                "action_input": action_input,
                "observation": None,
            }
            
            # Check for final answer
            if action == "final_answer":
                result["answer"] = action_input.get("answer", "")
                result["success"] = True
                step_record["observation"] = "TASK COMPLETE"
                result["steps"].append(step_record)
                console.print(f"   [green]Final answer![/green]\n")
                break
            
            # Execute tool
            try:
                tool_result = self.registry.execute(action, action_input)
                step_record["observation"] = {
                    "success": tool_result.success,
                    "output": str(tool_result.output)[:500] if tool_result.output else "",
                    "error": tool_result.error,
                }
                
                if tool_result.success:
                    console.print(f"   [green]Observation:[/green] {str(tool_result.output)[:200]}")
                else:
                    console.print(f"   [red]Error:[/red] {tool_result.error[:200]}")
                
                result["steps"].append(step_record)
                
                # Add to conversation
                conversation += f"\n\nStep {step_num}:"
                conversation += f"\nThought: {thought}"
                conversation += f"\nAction: {action}({json.dumps(action_input)})"
                conversation += f"\nObservation: {json.dumps(step_record['observation'])}"
                conversation += f"\n\nWhat's your next action?"
                
            except Exception as e:
                logger.error(f"Tool exec error: {e}")
                step_record["observation"] = {"success": False, "error": str(e)}
                result["steps"].append(step_record)
                break
        
        if not result["success"] and not result["error"]:
            result["error"] = f"Max steps ({self.MAX_STEPS}) reached without final answer"
        
        return result


if __name__ == "__main__":
    console.print("\n" + "="*70)
    console.print("[bold magenta]Tool Agent Test[/bold magenta]")
    console.print("="*70)
    
    agent = ToolAgent()
    
    # Test 1: Simple file operation (no tools needed - direct answer)
    console.print("\n" + "="*70)
    console.print("[bold]Test 1: Simple file read[/bold]")
    console.print("="*70)
    
    # First create a file
    from src.tools.registry import ToolRegistry
    reg = ToolRegistry()
    reg.execute("write_file", {"path": "agent_test/notes.txt", "content": "AegisOS test file\nLine 2\nLine 3"})
    
    result = agent.run(
        query="Read the file agent_test/notes.txt and tell me how many lines it has",
        tools_needed=["filesystem"],
    )
    
    console.print(f"\n[bold]Final answer:[/bold] {result['answer']}")
    console.print(f"[dim]Success: {result['success']} | Steps: {len(result['steps'])}[/dim]")
    
    # Cleanup
    reg.execute("delete_file", {"path": "agent_test/notes.txt"})