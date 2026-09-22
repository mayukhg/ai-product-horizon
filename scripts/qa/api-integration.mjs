#!/usr/bin/env node
/**
 * HorizonAI API integration QA suite
 */
import { writeFileSync } from "fs";

const BASE = process.env.API_BASE_URL || "http://127.0.0.1:8000";
const results = [];

function record(id, name, passed, detail = "") {
  results.push({ id, name, passed, detail });
  const icon = passed ? "PASS" : "FAIL";
  console.log(`[${icon}] ${id}: ${name}${detail ? ` — ${detail}` : ""}`);
}

async function request(method, path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let json = null;
  try {
    json = JSON.parse(text);
  } catch {
    json = { raw: text };
  }
  return { status: res.status, json };
}

async function run() {
  console.log(`\n=== HorizonAI API Integration QA ===`);
  console.log(`Target: ${BASE}\n`);

  const health = await request("GET", "/health");
  record("API-01", "Health endpoint", health.status === 200 && health.json.status === "ok", `status=${health.status}`);

  const triage = await request("GET", "/api/v1/triage");
  const triageOk =
    triage.status === 200 &&
    triage.json.summary?.scan_id &&
    Array.isArray(triage.json.vulnerabilities) &&
    triage.json.vulnerabilities.length > 0;
  record("API-02", "Triage summary + vulnerabilities", triageOk, `CVEs=${triage.json.vulnerabilities?.length ?? 0}`);

  const trajectory = await request("GET", "/api/v1/agent/trajectory");
  const trajOk = trajectory.status === 200 && trajectory.json.steps?.length > 0;
  record("API-03", "Agent trajectory", trajOk, `steps=${trajectory.json.steps?.length ?? 0}`);

  const routes = await request("GET", "/api/v1/models/route");
  const routesOk = routes.status === 200 && routes.json.routes?.length >= 2;
  record("API-04", "Model routing", routesOk, `routes=${routes.json.routes?.length ?? 0}`);

  const evals = await request("GET", "/api/v1/evals");
  const evalsOk = evals.status === 200 && evals.json.series?.length > 0;
  record("API-05", "Eval metrics dashboard data", evalsOk, `pass_rate=${evals.json.pass_rate_pct}%`);

  const baseline = await request("POST", "/api/v1/evals/baseline");
  const baselineOk = baseline.status === 200 && baseline.json.status === "ok";
  record(
    "API-06",
    "Eval baseline config",
    baselineOk,
    `llm_mode=${baseline.json.llm_mode}, cases=${baseline.json.total_cases}`,
  );

  const evalRun = await request("POST", "/api/v1/evals/run", { limit: 2 });
  const evalRunOk = evalRun.status === 200 && evalRun.json.total_cases === 2;
  record(
    "API-07",
    "Golden dataset eval run (limit=2)",
    evalRunOk,
    `mode=${evalRun.json.llm_mode}, groundedness=${evalRun.json.mean_groundedness_pct}%`,
  );

  const approve = await request("POST", "/api/v1/remediate/approve", {
    remediation_id: "REM-CR-3094",
    approved_by: "QA",
    approval_id: "HITL-QA-001",
  });
  const approveOk = approve.status === 200 && approve.json.status === "approved";
  record("API-08", "HITL remediation approve", approveOk, approve.json.message || "");

  const agentRun = await request("POST", "/api/v1/agent/run?scan_id=CR-0922-0048");
  const agentOk = agentRun.status === 200 && agentRun.json.run_id;
  record("API-09", "Agent run trigger", agentOk, `run_id=${agentRun.json.run_id}`);

  const trajectory2 = await request("GET", `/api/v1/agent/trajectory?run_id=${agentRun.json.run_id || "7f4c-92a1"}`);
  record("API-10", "Trajectory after agent run", trajectory2.status === 200, `status=${trajectory2.status}`);

  const passed = results.filter((r) => r.passed).length;
  const failed = results.filter((r) => !r.passed).length;
  console.log(`\nAPI Summary: ${passed} passed, ${failed} failed, ${results.length} total\n`);

  return { results, passed, failed, total: results.length };
}

const summary = await run();
writeFileSync("/opt/cursor/artifacts/qa-api-results.json", JSON.stringify(summary, null, 2));
process.exit(summary.failed > 0 ? 1 : 0);
