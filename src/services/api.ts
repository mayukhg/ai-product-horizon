const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  code: string;

  constructor(message: string, code = "API_ERROR") {
    super(message);
    this.code = code;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    let payload: { code?: string; message?: string; detail?: { code?: string; message?: string } } = {};
    try {
      payload = await response.json();
    } catch {
      payload = {};
    }
    const detail = payload.detail;
    const code = detail?.code ?? payload.code ?? "API_ERROR";
    const message = detail?.message ?? payload.message ?? `Request failed (${response.status})`;
    throw new ApiError(message, code);
  }

  return response.json() as Promise<T>;
}

export type TriageResponse = {
  summary: {
    scan_id: string;
    tru_risk_score: number;
    tru_risk_delta: number;
    asset_count: number;
    internet_facing_count: number;
    critical_findings: number;
    scope: string;
    scanner: string;
    policies: string;
    last_delta_sec: number;
    kpis: {
      groundedness_pct: number;
      latency_p95_ms: number;
      model_cost_per_1k: number;
    };
  };
  vulnerabilities: Array<{
    cve: string;
    product: string;
    assets: number;
    cvss: string;
    state: string;
    severity: string;
  }>;
};

export type AgentTrajectoryResponse = {
  run_id: string;
  scan_id: string;
  title: string;
  region: string;
  autonomy_level: number;
  status: string;
  steps: Array<{
    id: string;
    title: string;
    detail: string;
    time: string;
    step_type: string;
    status: string;
  }>;
  workers: Array<{
    name: string;
    detail: string;
    tone: "success" | "primary" | "agent";
  }>;
};

export type ModelRoutingResponse = {
  routes: Array<{
    label: string;
    model: string;
    detail: string;
    active: boolean;
  }>;
};

export type EvalMetricsResponse = {
  total_runs: number;
  pass_rate_pct: number;
  drift_embedding_pct: number;
  series: Array<{
    time: string;
    retrieval: number;
    groundedness: number;
    relevance: number;
    latency: number;
  }>;
  recent_runs: Array<{
    id: string;
    name: string;
    score: string;
    state: string;
  }>;
  telemetry: Array<{
    label: string;
    value: string;
    status: string;
  }>;
};

export type RemediateApproveResponse = {
  status: "approved";
  remediation_id: string;
  approval_id: string;
  approved_at: string;
  message: string;
};

export const api = {
  getTriage: () => request<TriageResponse>("/triage"),
  getAgentTrajectory: (runId = "7f4c-92a1") => request<AgentTrajectoryResponse>(`/agent/trajectory?run_id=${runId}`),
  getModelRoutes: () => request<ModelRoutingResponse>("/models/route"),
  getEvalMetrics: () => request<EvalMetricsResponse>("/evals"),
  approveRemediation: (payload: { remediation_id?: string; approved_by?: string; approval_id?: string }) =>
    request<RemediateApproveResponse>("/remediate/approve", {
      method: "POST",
      body: JSON.stringify({
        remediation_id: payload.remediation_id ?? "REM-CR-3094",
        approved_by: payload.approved_by ?? "MH",
        approval_id: payload.approval_id ?? "HITL-8821",
      }),
    }),
};
