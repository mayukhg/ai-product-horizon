from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    code: str
    message: str


class TriageKpi(BaseModel):
    groundedness_pct: float
    latency_p95_ms: int
    model_cost_per_1k: float


class TriageSummary(BaseModel):
    scan_id: str
    tru_risk_score: int
    tru_risk_delta: int
    asset_count: int
    internet_facing_count: int
    critical_findings: int
    scope: str
    scanner: str
    policies: str
    last_delta_sec: int
    kpis: TriageKpi


class VulnerabilityItem(BaseModel):
    cve: str
    product: str
    assets: int
    cvss: str
    state: str
    severity: str


class TriageResponse(BaseModel):
    summary: TriageSummary
    vulnerabilities: list[VulnerabilityItem]


class TrajectoryStep(BaseModel):
    id: str
    title: str
    detail: str
    time: str
    step_type: str
    status: str


class WorkerAgent(BaseModel):
    name: str
    detail: str
    tone: Literal["success", "primary", "agent"]


class AgentTrajectoryResponse(BaseModel):
    run_id: str
    scan_id: str
    title: str
    region: str
    autonomy_level: int
    status: str
    steps: list[TrajectoryStep]
    workers: list[WorkerAgent]


class ModelRoute(BaseModel):
    label: str
    model: str
    detail: str
    active: bool


class ModelRoutingResponse(BaseModel):
    routes: list[ModelRoute]


class EvalMetricPoint(BaseModel):
    time: str
    retrieval: float
    groundedness: float
    relevance: float
    latency: int


class EvalRunItem(BaseModel):
    id: str
    name: str
    score: str
    state: str


class EvalMetricsResponse(BaseModel):
    total_runs: int
    pass_rate_pct: float
    drift_embedding_pct: float
    series: list[EvalMetricPoint]
    recent_runs: list[EvalRunItem]
    telemetry: list[dict[str, Any]]


class RemediateApproveRequest(BaseModel):
    remediation_id: str = "REM-CR-3094"
    approved_by: str = "MH"
    approval_id: str = "HITL-8821"


class RemediateApproveResponse(BaseModel):
    status: Literal["approved"] = "approved"
    remediation_id: str
    approval_id: str
    approved_at: datetime
    message: str
