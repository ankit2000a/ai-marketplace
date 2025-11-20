"""
A2A Protocol Definitions
========================
Shared JSON schemas for Agent-to-Agent communication.
Protocol Version: AI_MARKETPLACE_v1
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal

class JobConstraints(BaseModel):
    """Constraints imposed by the buyer"""
    max_price: float = Field(..., description="Maximum amount buyer will pay (USD)")
    max_latency_ms: Optional[int] = Field(None, description="Maximum acceptable response time")
    min_quality: Optional[float] = Field(None, ge=1.0, le=5.0, description="Minimum required rating")
    deadline: Optional[str] = Field(None, description="ISO 8601 deadline")
    required_format: Optional[str] = Field(None, description="Required output format")

class JobOffer(BaseModel):
    """Standardized Job Offer (AI_MARKETPLACE_v1)"""
    protocol: Literal["AI_MARKETPLACE_v1"] = "AI_MARKETPLACE_v1"
    job_id: str = Field(..., description="Unique job identifier")
    buyer_id: str = Field(..., description="Agent requesting the work")
    capability: str = Field(..., description="What service is needed")
    constraints: JobConstraints
    task_payload: Dict[str, Any] = Field(..., description="Actual data/instructions for the task")

class JobBid(BaseModel):
    """Bid submitted by an agent in response to a Job Offer"""
    protocol: Literal["AI_MARKETPLACE_v1"] = "AI_MARKETPLACE_v1"
    type: Literal["bid"] = "bid"
    job_id: str
    agent_id: str
    proposed_price: float
    estimated_completion_ms: int
    guarantees: Optional[Dict[str, Any]] = None

class AgentCard(BaseModel):
    """Public 'Passport' for an Agent"""
    protocol_version: str = "AI_MARKETPLACE_v1"
    agent: Dict[str, Any] # name, version, description, etc.
    capabilities: List[Dict[str, Any]]
    pricing: Dict[str, Any]
    performance: Optional[Dict[str, Any]] = None
    quality: Optional[Dict[str, Any]] = None
    endpoints: Dict[str, str]
    payment: Optional[Dict[str, Any]] = None
