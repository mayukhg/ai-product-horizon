#!/usr/bin/env node
/**
 * HorizonAI headless browser E2E QA suite (Playwright)
 */
import { chromium } from "playwright";
import { writeFileSync, mkdirSync } from "fs";

const BASE = process.env.APP_BASE_URL || "http://127.0.0.1:5173";
const SHOTS = "/opt/cursor/artifacts/qa-screenshots";
mkdirSync(SHOTS, { recursive: true });

const results = [];

function record(id, name, passed, detail = "") {
  results.push({ id, name, passed, detail });
  const icon = passed ? "PASS" : "FAIL";
  console.log(`[${icon}] ${id}: ${name}${detail ? ` — ${detail}` : ""}`);
}

async function shot(page, name) {
  const path = `${SHOTS}/${name}.png`;
  await page.screenshot({ path, fullPage: true });
  return path;
}

async function run() {
  console.log(`\n=== HorizonAI Headless Browser E2E QA ===`);
  console.log(`Target: ${BASE}\n`);

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  // UI-01 App loads
  const loadRes = await page.goto(BASE, { waitUntil: "networkidle", timeout: 30000 });
  const loadOk = loadRes?.ok();
  record("UI-01", "Application loads (HTTP 200)", loadOk, `status=${loadRes?.status()}`);
  await shot(page, "01-cyberrisk-resident-default");

  // UI-02 Default view is CyberRisk Resident
  const titleVisible = await page.getByRole("heading", { name: "CyberRisk Resident" }).isVisible();
  record("UI-02", "CyberRisk Resident default view", titleVisible);

  // UI-03 Live API data — TruRisk scorecard present
  const truRisk = await page.getByText("Enterprise TruRisk").isVisible();
  record("UI-03", "Enterprise TruRisk scorecard visible", truRisk);

  // UI-04 Agent trajectory panel
  const trajectory = await page.getByText("Live agent trajectory").isVisible();
  record("UI-04", "Live agent trajectory panel", trajectory);

  // UI-05 CVE table with live data
  const cveVisible = await page.getByRole("table").getByText("CVE-2024-3094").first().isVisible();
  record("UI-05", "Priority threat intelligence table (CVE data)", cveVisible);

  // UI-06 Model routing shows OpenRouter
  const routing = await page.getByText("OpenRouter").isVisible();
  record("UI-06", "Model routing shows OpenRouter", routing);

  // UI-07 Remediation queue
  const remediation = await page.getByRole("button", { name: /Review & Approve Patch/i }).isVisible();
  record("UI-07", "Remediation action queue with HITL button", remediation);

  // UI-08 HITL approval dialog
  await page.getByRole("button", { name: /Review & Approve Patch/i }).click();
  const dialogVisible = await page.getByRole("dialog").isVisible();
  const dialogTitle = await page.getByText("Authorize production remediation").isVisible();
  record("UI-08", "HITL approval dialog opens", dialogVisible && dialogTitle);
  await shot(page, "02-hitl-approval-dialog");

  // UI-09 Approve remediation
  await page.getByRole("button", { name: /Approve & Execute/i }).click();
  await page.waitForTimeout(1500);
  const approved = await page.getByRole("button", { name: /Approved for execution/i }).isVisible();
  record("UI-09", "HITL approve submits to API", approved);
  await shot(page, "03-remediation-approved");

  // UI-10 Navigate to Eval Studio
  await page.getByRole("button", { name: /AI PRD & Eval Studio/i }).click();
  await page.waitForTimeout(1000);
  const evalTitle = await page.getByRole("heading", { name: "AI PRD & Eval Studio" }).isVisible();
  const ragChart = await page.getByText("RAG Triad · 7 hour window").isVisible();
  record("UI-10", "AI PRD & Eval Studio view", evalTitle && ragChart);
  await shot(page, "04-eval-studio");

  // UI-11 Navigate to Resident Roadmap
  await page.getByRole("button", { name: /Resident Roadmap/i }).click();
  await page.waitForTimeout(800);
  const roadmapTitle = await page.getByRole("heading", { name: "Resident Roadmap" }).isVisible();
  const attackSurface = await page.getByText("AttackSurface Resident").isVisible();
  record("UI-11", "Resident Roadmap view", roadmapTitle && attackSurface);
  await shot(page, "05-resident-roadmap");

  // UI-12 Data state simulator — loading
  await page.getByRole("button", { name: "CyberRisk Resident" }).click();
  await page.waitForTimeout(500);
  await page.getByRole("button", { name: "loading", exact: true }).click();
  await page.waitForTimeout(500);
  const skeleton = await page.locator('[aria-label="Loading cyber risk data"]').isVisible();
  record("UI-12", "Data state simulator — loading skeleton", skeleton);
  await shot(page, "06-loading-state");

  // UI-13 Data state simulator — drift
  await page.getByRole("button", { name: "drift", exact: true }).click();
  await page.waitForTimeout(500);
  const driftBanner = await page.getByText("Data Drift Detected").isVisible();
  record("UI-13", "Data state simulator — drift banner", driftBanner);
  await shot(page, "07-drift-state");

  // UI-14 Data state simulator — offline
  await page.getByRole("button", { name: "offline", exact: true }).click();
  await page.waitForTimeout(500);
  const offline = await page.getByText("Live telemetry unavailable").isVisible();
  record("UI-14", "Data state simulator — offline state", offline);
  await shot(page, "08-offline-state");

  // UI-15 Retry from offline returns to live
  await page.getByRole("button", { name: /Retry connection/i }).click();
  await page.waitForTimeout(1500);
  const backLive = await page.getByRole("heading", { name: "CyberRisk Resident" }).isVisible();
  record("UI-15", "Offline retry restores live view", backLive);
  await shot(page, "09-back-to-live");

  // UI-16 Mobile navigation
  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload({ waitUntil: "networkidle" });
  await page.getByRole("button", { name: "Open navigation" }).click();
  await page.waitForTimeout(400);
  const sidebar = await page.getByText("Autonomous risk operations").isVisible();
  record("UI-16", "Mobile sidebar navigation", sidebar);
  await shot(page, "10-mobile-sidebar");

  // UI-17 No backend offline banner when API healthy
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.reload({ waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  const offlineBanner = await page.getByText("Backend disconnected").isVisible().catch(() => false);
  record("UI-17", "No backend-disconnected banner (API healthy)", !offlineBanner);

  await browser.close();

  const passed = results.filter((r) => r.passed).length;
  const failed = results.filter((r) => !r.passed).length;
  console.log(`\nUI Summary: ${passed} passed, ${failed} failed, ${results.length} total\n`);

  return { results, passed, failed, total: results.length, screenshots: SHOTS };
}

const summary = await run();
writeFileSync("/opt/cursor/artifacts/qa-ui-results.json", JSON.stringify(summary, null, 2));
process.exit(summary.failed > 0 ? 1 : 0);
