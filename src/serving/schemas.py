"""Pydantic schemas for AegisOS API"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict


class RunRequest(BaseModel):
    """Request to run AegisOS pipeline"""
    model_config = ConfigDict(protected_namespaces=())
    
    query: str = Field(..., min_length=5, max_length=1000, description="User query")
    max_retries: int = Field(default=1, ge=0, le=3)
    max_steps: int = Field(default=5, ge=1, le=10)


class IntentInfo(BaseModel):
    task_type: str
    complexity: str
    risk_level: str
    requires_tools: bool
    tools_needed: List[str]
    estimated_tokens: int


class DecisionInfo(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    selected_model_id: str
    selected_model_name: str
    selected_model_tier: str
    fallback_model_id: Optional[str] = None
    selection_reason: str
    quota_impact_pct: float
    projected_cost_usd: float


class PlanStepInfo(BaseModel):
    step_id: int
    description: str
    tool_needed: Optional[str] = None
    status: str
    result: Optional[str] = None
    error: Optional[str] = None


class RunResponse(BaseModel):
    """Response from AegisOS pipeline"""
    model_config = ConfigDict(protected_namespaces=())
    
    query: str
    decision_id: str
    intent: IntentInfo
    decision: DecisionInfo
    plan: List[PlanStepInfo]
    verification_status: str
    verification_reason: str
    retry_count: int
    final_answer: str
    success: bool
    elapsed_seconds: float


class HealthResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    status: str
    version: str
    groq_configured: bool
    models_loaded: int
    tools_registered: int


class UsageResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    models: Dict[str, Dict]