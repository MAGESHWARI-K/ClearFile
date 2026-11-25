"""Validated contracts shared by ClearFile's supervisor and worker agents."""
from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict

class WorkflowRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    application_id: str = Field(min_length=1, max_length=100)
    extracted: dict[str, dict[str, Any]] = Field(default_factory=dict)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    anomalies: list[dict[str, Any]] = Field(default_factory=list)

class AgentResult(BaseModel):
    agent: str = Field(min_length=1)
    status: Literal['completed', 'failed']
    summary: str
    evidence_count: int = Field(default=0, ge=0)
    flags: list[str] = Field(default_factory=list)
    attempts: int = Field(default=1, ge=1)
    duration_seconds: float = Field(default=0.0, ge=0)

class JobRequest(BaseModel):
    application_id: str = Field(min_length=1, max_length=100)
