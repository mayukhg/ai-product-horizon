CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS assets (
    id SERIAL PRIMARY KEY,
    hostname VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    asset_type VARCHAR(100) NOT NULL,
    environment VARCHAR(50) NOT NULL,
    region VARCHAR(50) NOT NULL,
    internet_facing BOOLEAN NOT NULL DEFAULT FALSE,
    tru_risk_score INTEGER NOT NULL DEFAULT 0,
    embedding vector(1536)
);

CREATE TABLE IF NOT EXISTS vulnerabilities (
    id SERIAL PRIMARY KEY,
    cve_id VARCHAR(50) UNIQUE NOT NULL,
    product VARCHAR(255) NOT NULL,
    cvss DECIMAL(4, 1) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    threat_state VARCHAR(100) NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS asset_vulnerabilities (
    asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    vulnerability_id INTEGER NOT NULL REFERENCES vulnerabilities(id) ON DELETE CASCADE,
    PRIMARY KEY (asset_id, vulnerability_id)
);

CREATE TABLE IF NOT EXISTS eval_cases (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(20) UNIQUE NOT NULL,
    slice VARCHAR(100) NOT NULL,
    eval_type VARCHAR(50) NOT NULL,
    input_prompt TEXT NOT NULL,
    expected_output JSONB NOT NULL,
    routing_recommendation VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS eval_runs (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    score DECIMAL(5, 2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    retrieval_score DECIMAL(5, 2),
    groundedness_score DECIMAL(5, 2),
    relevance_score DECIMAL(5, 2),
    latency_ms INTEGER,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_runs (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(50) UNIQUE NOT NULL,
    scan_id VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    region VARCHAR(50) NOT NULL,
    autonomy_level INTEGER NOT NULL DEFAULT 2,
    status VARCHAR(50) NOT NULL DEFAULT 'executing',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_trajectory_steps (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(50) NOT NULL REFERENCES agent_runs(run_id) ON DELETE CASCADE,
    step_order INTEGER NOT NULL,
    step_id VARCHAR(10) NOT NULL,
    title VARCHAR(255) NOT NULL,
    detail TEXT NOT NULL,
    duration_ms INTEGER NOT NULL,
    step_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'completed',
    UNIQUE (run_id, step_order)
);

CREATE TABLE IF NOT EXISTS agent_execution_logs (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(50) NOT NULL,
    agent_role VARCHAR(50) NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    action TEXT NOT NULL,
    result JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS remediation_actions (
    id SERIAL PRIMARY KEY,
    remediation_id VARCHAR(50) UNIQUE NOT NULL,
    cve_id VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    blast_radius VARCHAR(20) NOT NULL,
    confidence DECIMAL(5, 2) NOT NULL,
    priority INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    shell_commands TEXT[] NOT NULL,
    assets_affected INTEGER NOT NULL DEFAULT 0,
    approval_id VARCHAR(50),
    approved_at TIMESTAMPTZ,
    approved_by VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS scan_context (
    id SERIAL PRIMARY KEY,
    scan_id VARCHAR(50) UNIQUE NOT NULL,
    scope VARCHAR(100) NOT NULL,
    scanner VARCHAR(100) NOT NULL,
    policies VARCHAR(100) NOT NULL,
    last_delta_sec INTEGER NOT NULL,
    tru_risk_score INTEGER NOT NULL,
    tru_risk_delta INTEGER NOT NULL,
    asset_count INTEGER NOT NULL,
    internet_facing_count INTEGER NOT NULL,
    critical_findings INTEGER NOT NULL,
    groundedness_pct DECIMAL(5, 2) NOT NULL,
    latency_p95_ms INTEGER NOT NULL,
    model_cost_per_1k DECIMAL(6, 2) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS model_routes (
    id SERIAL PRIMARY KEY,
    task_label VARCHAR(100) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    detail TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    cost_multiplier DECIMAL(6, 2) NOT NULL DEFAULT 1.0
);

CREATE INDEX IF NOT EXISTS idx_eval_cases_slice ON eval_cases(slice);
CREATE INDEX IF NOT EXISTS idx_agent_trajectory_run ON agent_trajectory_steps(run_id);
CREATE INDEX IF NOT EXISTS idx_remediation_status ON remediation_actions(status);
