"""FastAPI serving for AegisOS"""
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from datetime import datetime
import os
import time
import logging

from src.serving.schemas import (
    RunRequest, RunResponse,
    IntentInfo, DecisionInfo, PlanStepInfo,
    HealthResponse, UsageResponse,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global components
_analyzer = None
_engine = None
_graph = None
_registry = None
_tool_registry = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load components at startup"""
    global _analyzer, _engine, _graph, _registry, _tool_registry
    
    logger.info("🚀 Loading AegisOS components...")
    
    try:
        from src.core.model_registry import ModelRegistry
        from src.core.intent_analyzer import IntentAnalyzer
        from src.core.decision_engine import DecisionEngine
        from src.agents.graph import build_graph
        from src.tools.registry import ToolRegistry
        
        _registry = ModelRegistry()
        _analyzer = IntentAnalyzer()
        _engine = DecisionEngine(_registry)
        _graph = build_graph()
        _tool_registry = ToolRegistry()
        
        logger.info("✅ AegisOS ready!")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
    
    yield
    
    logger.info("🛑 Shutting down")


app = FastAPI(
    title="AegisOS API",
    description="AI Operating System — intent-driven model routing, multi-agent execution, and transparent decision logs.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", tags=["Info"])
def root():
    return {
        "service": "AegisOS API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["Info"])
def health():
    groq_ok = bool(os.getenv("GROQ_API_KEY"))
    models_count = len(_registry.models) if _registry else 0
    tools_count = len(_tool_registry.tools) if _tool_registry else 0
    
    return HealthResponse(
        status="healthy" if _graph is not None else "unhealthy",
        version="1.0.0",
        groq_configured=groq_ok,
        models_loaded=models_count,
        tools_registered=tools_count,
    )


@app.get("/models", tags=["Info"])
def list_models():
    """List all available Groq models"""
    if _registry is None:
        raise HTTPException(503, "Registry not loaded")
    
    return {
        "models": [
            {
                "id": m.id,
                "name": m.name,
                "tier": m.tier,
                "tpm_limit": m.rate_limit_tpm,
                "strengths": m.strengths,
            }
            for m in _registry.models.values()
        ]
    }


@app.get("/tools", tags=["Info"])
def list_tools():
    """List all registered tools"""
    if _tool_registry is None:
        raise HTTPException(503, "Tools not loaded")
    
    return {
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "risk_level": t.risk_level,
            }
            for t in _tool_registry.tools.values()
        ]
    }


@app.get("/usage", response_model=UsageResponse, tags=["Monitoring"])
def usage():
    """Get current rate limit usage"""
    from src.core.rate_limiter import RateLimiter
    limiter = RateLimiter()
    return UsageResponse(models=limiter.get_all_stats())


@app.post("/run", response_model=RunResponse, tags=["Pipeline"])
def run_pipeline(request: RunRequest):
    """
    Run full AegisOS pipeline:
    Intent → Decision → Multi-Agent Execution → Verification
    """
    if _graph is None:
        raise HTTPException(503, "Pipeline not loaded")
    
    t0 = time.time()
    
    try:
        # 1. Intent analysis
        logger.info(f"[{request.query[:50]}] Analyzing intent...")
        intent = _analyzer.analyze(request.query)
        
        # 2. Decision
        logger.info(f"[{request.query[:50]}] Making decision...")
        decision = _engine.decide(request.query, intent)
        
        # 3. Build initial state
        from src.agents.state import AgentState
        initial_state = AgentState(
            user_query=request.query,
            task_type=intent.task_type,
            complexity=intent.complexity,
            risk_level=intent.risk_level,
            requires_tools=intent.requires_tools,
            tools_needed=intent.tools_needed,
            estimated_tokens=intent.estimated_tokens,
            max_steps=request.max_steps,
            max_retries=request.max_retries,
            decision_id=decision.decision_id,
            selected_model=decision.selected_model_id,
        )
        
        # 4. Run multi-agent graph
        logger.info(f"[{request.query[:50]}] Running multi-agent graph...")
        config = {"recursion_limit": 50}
        final_state_dict = _graph.invoke(initial_state, config=config)
        
        # Convert dict back to AgentState for attribute access
        final_state = AgentState(**final_state_dict)
        
        elapsed = time.time() - t0
        logger.info(f"[{request.query[:50]}] Complete in {elapsed:.1f}s")
        
        # 5. Build response
        return RunResponse(
            query=request.query,
            decision_id=decision.decision_id,
            intent=IntentInfo(
                task_type=intent.task_type,
                complexity=intent.complexity,
                risk_level=intent.risk_level,
                requires_tools=intent.requires_tools,
                tools_needed=intent.tools_needed,
                estimated_tokens=intent.estimated_tokens,
            ),
            decision=DecisionInfo(
                selected_model_id=decision.selected_model_id,
                selected_model_name=decision.selected_model_name,
                selected_model_tier=decision.selected_model_tier,
                fallback_model_id=decision.fallback_model_id,
                selection_reason=decision.selection_reason,
                quota_impact_pct=decision.quota_impact_pct,
                projected_cost_usd=decision.projected_cost_usd,
            ),
            plan=[
                PlanStepInfo(
                    step_id=s.step_id,
                    description=s.description,
                    tool_needed=s.tool_needed,
                    status=s.status,
                    result=s.result,
                    error=s.error,
                )
                for s in final_state.plan
            ],
            verification_status=final_state.verification_status,
            verification_reason=final_state.verification_reason,
            retry_count=final_state.retry_count,
            final_answer=final_state.final_answer,
            success=final_state.success,
            elapsed_seconds=round(elapsed, 2),
        )
    
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise HTTPException(500, str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.serving.app:app", host="0.0.0.0", port=8000, reload=True)