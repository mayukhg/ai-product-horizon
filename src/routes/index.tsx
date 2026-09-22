import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Bot,
  BrainCircuit,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  CircleDot,
  Clock3,
  CloudOff,
  Code2,
  Database,
  FileCheck2,
  Fingerprint,
  GitBranch,
  Hexagon,
  LayoutDashboard,
  LockKeyhole,
  Menu,
  Network,
  Play,
  Radar,
  RefreshCw,
  Route as RouteIcon,
  Server,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Terminal,
  TrendingDown,
  X,
  Zap,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "HorizonAI — CyberRisk Resident" },
      {
        name: "description",
        content:
          "HorizonAI CyberRisk Resident command center for agentic risk analysis, remediation, and production AI evaluation.",
      },
      { property: "og:title", content: "HorizonAI — CyberRisk Resident" },
      {
        property: "og:description",
        content: "Enterprise cyber risk intelligence with human-approved AI remediation.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: HorizonDashboard,
});

type View = "resident" | "eval" | "roadmap";
type DataState = "live" | "loading" | "drift" | "offline";

const trajectory = [
  { id: "01", title: "Plan", detail: "Decompose scan delta into exploitable paths", time: "0.2s", icon: BrainCircuit },
  { id: "02", title: "Tool Call", detail: "query_asset_graph · prod-us-east", time: "1.1s", icon: Terminal },
  { id: "03", title: "Context Retrieval", detail: "12 assets · 43 observations · 8 CVEs", time: "2.4s", icon: Database },
  { id: "04", title: "Observation", detail: "XZ Utils backdoor signature confirmed", time: "3.8s", icon: CircleDot },
  { id: "05", title: "Check", detail: "Policy + blast-radius guardrail passed", time: "4.1s", icon: ShieldCheck },
];

const evalData = [
  { time: "09:00", retrieval: 91, groundedness: 94, relevance: 89, latency: 760 },
  { time: "10:00", retrieval: 93, groundedness: 95, relevance: 91, latency: 710 },
  { time: "11:00", retrieval: 88, groundedness: 92, relevance: 90, latency: 824 },
  { time: "12:00", retrieval: 95, groundedness: 96, relevance: 93, latency: 680 },
  { time: "13:00", retrieval: 92, groundedness: 97, relevance: 94, latency: 642 },
  { time: "14:00", retrieval: 86, groundedness: 89, relevance: 87, latency: 910 },
  { time: "15:00", retrieval: 94, groundedness: 97, relevance: 92, latency: 684 },
];

const vulnerabilities = [
  { cve: "CVE-2024-3094", product: "XZ Utils 5.6.1", assets: 12, cvss: "10.0", state: "Active exploit", severity: "critical" },
  { cve: "CVE-2024-6387", product: "OpenSSH 8.5p1", assets: 8, cvss: "8.1", state: "PoC observed", severity: "high" },
  { cve: "CVE-2023-4863", product: "libwebp 1.3.1", assets: 21, cvss: "8.8", state: "Patch available", severity: "high" },
];

function HorizonDashboard() {
  const [view, setView] = useState<View>("resident");
  const [dataState, setDataState] = useState<DataState>("live");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [approvalOpen, setApprovalOpen] = useState(false);
  const [approved, setApproved] = useState(false);

  const title = useMemo(() => {
    if (view === "eval") return "AI PRD & Eval Studio";
    if (view === "roadmap") return "Resident Roadmap";
    return "CyberRisk Resident";
  }, [view]);

  function selectView(next: View) {
    setView(next);
    setSidebarOpen(false);
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="pointer-events-none fixed inset-0 z-0 cyber-grid opacity-35" />
      {sidebarOpen && (
        <div className="fixed inset-0 z-30 bg-overlay/80 lg:hidden" onClick={() => setSidebarOpen(false)} aria-hidden="true" />
      )}
      <Sidebar view={view} onSelect={selectView} open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <main className="relative z-10 min-h-screen lg:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-border/70 bg-background/90 px-4 backdrop-blur-xl sm:px-6 lg:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setSidebarOpen(true)} aria-label="Open navigation">
              <Menu />
            </Button>
            <div className="min-w-0">
              <div className="flex items-center gap-2 text-[10px] font-semibold uppercase text-muted-foreground">
                <span>HorizonAI</span><ChevronRight className="size-3" /><span className="truncate">{title}</span>
              </div>
              <div className="mt-0.5 flex items-center gap-2">
                <span className="size-1.5 rounded-full bg-success shadow-status-success" />
                <span className="text-xs text-foreground/80">System operational</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="hidden items-center gap-1 rounded-md border border-border bg-panel p-1 md:flex" aria-label="Data state simulator">
              {(["live", "loading", "drift", "offline"] as DataState[]).map((state) => (
                <Button key={state} size="sm" variant={dataState === state ? "secondary" : "ghost"} onClick={() => setDataState(state)} className="h-7 px-2 text-[10px] uppercase">
                  {state}
                </Button>
              ))}
            </div>
            <Button variant="outline" size="sm" className="hidden border-primary/30 text-primary sm:inline-flex">
              <RefreshCw className="size-3.5" /> Sync scan
            </Button>
            <div className="grid size-8 place-items-center rounded-md border border-primary/30 bg-primary/10 font-mono text-xs font-bold text-primary">MH</div>
          </div>
        </header>

        <div className="mx-auto max-w-[1600px] px-4 py-5 sm:px-6 lg:px-8">
          {dataState === "drift" && <DriftBanner />}
          {dataState === "offline" ? (
            <OfflineState onRetry={() => setDataState("live")} />
          ) : dataState === "loading" ? (
            <LoadingState />
          ) : view === "eval" ? (
            <EvalStudio drift={dataState === "drift"} />
          ) : view === "roadmap" ? (
            <Roadmap />
          ) : (
            <ResidentView onReview={() => setApprovalOpen(true)} approved={approved} />
          )}
        </div>
      </main>

      <ApprovalDialog
        open={approvalOpen}
        onOpenChange={setApprovalOpen}
        onApprove={() => {
          setApproved(true);
          setApprovalOpen(false);
        }}
      />
    </div>
  );
}

function Sidebar({ view, onSelect, open, onClose }: { view: View; onSelect: (view: View) => void; open: boolean; onClose: () => void }) {
  return (
    <aside className={cn("fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-border bg-sidebar/95 backdrop-blur-xl transition-transform lg:translate-x-0", open ? "translate-x-0" : "-translate-x-full")}>
      <div className="flex h-16 items-center border-b border-border px-5">
        <div className="relative mr-3 grid size-8 place-items-center">
          <Hexagon className="absolute size-8 text-primary" strokeWidth={1.5} />
          <Radar className="size-4 text-primary" />
        </div>
        <div><div className="text-sm font-bold tracking-wide">HORIZON<span className="text-primary">AI</span></div><div className="font-mono text-[9px] uppercase text-muted-foreground">Autonomous risk operations</div></div>
        <Button variant="ghost" size="icon" className="ml-auto lg:hidden" onClick={onClose} aria-label="Close navigation"><X /></Button>
      </div>
      <div className="flex-1 overflow-y-auto px-3 py-5">
        <p className="px-2 text-[10px] font-semibold uppercase text-muted-foreground">Active pilot</p>
        <NavButton active={view === "resident"} icon={ShieldCheck} label="CyberRisk Resident" badge="Live" onClick={() => onSelect("resident")} />
        <div className="my-5 h-px bg-border" />
        <p className="px-2 text-[10px] font-semibold uppercase text-muted-foreground">Intelligence</p>
        <NavButton active={view === "eval"} icon={Activity} label="AI PRD & Eval Studio" onClick={() => onSelect("eval")} />
        <NavButton active={view === "roadmap"} icon={GitBranch} label="Resident Roadmap" onClick={() => onSelect("roadmap")} />
        <div className="my-5 h-px bg-border" />
        <p className="px-2 text-[10px] font-semibold uppercase text-muted-foreground">Future residents</p>
        <div className="mt-2 space-y-1">
          <PreviewNav icon={Network} title="AttackSurface" />
          <PreviewNav icon={FileCheck2} title="ComplianceSentinel" />
        </div>
      </div>
      <div className="border-t border-border p-4">
        <div className="mb-3 flex items-center justify-between text-[10px]"><span className="uppercase text-muted-foreground">Control plane</span><span className="font-mono text-success">CONNECTED</span></div>
        <div className="h-1 overflow-hidden rounded-full bg-muted"><div className="h-full w-[78%] bg-primary" /></div>
        <div className="mt-2 flex justify-between font-mono text-[9px] text-muted-foreground"><span>38 agents online</span><span>v2.4.1</span></div>
      </div>
    </aside>
  );
}

function NavButton({ active, icon: Icon, label, badge, onClick }: { active: boolean; icon: typeof ShieldCheck; label: string; badge?: string; onClick: () => void }) {
  return <Button variant="ghost" onClick={onClick} className={cn("mt-2 h-10 w-full justify-start px-2 text-xs", active && "bg-primary/10 text-primary ring-1 ring-primary/20")}><Icon className="size-4" /><span className="truncate">{label}</span>{badge && <span className="ml-auto rounded-sm bg-success/10 px-1.5 py-0.5 font-mono text-[9px] text-success">{badge}</span>}</Button>;
}

function PreviewNav({ icon: Icon, title }: { icon: typeof Network; title: string }) {
  return <div className="flex items-center gap-2 rounded-md px-2 py-2 text-muted-foreground"><Icon className="size-4" /><span className="text-xs">{title}</span><LockKeyhole className="ml-auto size-3" /></div>;
}

function ResidentView({ onReview, approved }: { onReview: () => void; approved: boolean }) {
  return (
    <div className="animate-fade-up space-y-5">
      <section className="flex flex-col justify-between gap-4 xl:flex-row xl:items-end">
        <div>
          <div className="mb-2 flex items-center gap-2"><span className="status-pill border-primary/30 bg-primary/10 text-primary"><Sparkles className="size-3" /> Active pilot</span><span className="font-mono text-[10px] text-muted-foreground">SCAN / CR-0922-0048</span></div>
          <h1 className="text-2xl font-semibold sm:text-3xl">CyberRisk Resident</h1>
          <p className="mt-1 text-sm text-muted-foreground">Autonomous exposure analysis across production infrastructure.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <MetricBadge label="Groundedness" value="97.2%" tone="success" />
          <MetricBadge label="Latency P95" value="684 ms" tone="cyan" />
          <MetricBadge label="Model cost / 1k" value="$0.84" tone="purple" />
        </div>
      </section>

      <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <ScoreCard />
        <StatCard icon={Server} label="Assets in context" value="2,847" detail="164 internet-facing" tone="cyan" />
        <StatCard icon={ShieldAlert} label="Critical findings" value="07" detail="+2 since last scan" tone="danger" />
        <StatCard icon={RouteIcon} label="Model routing" value="On-prem" detail="Llama-3.3-70B · healthy" tone="purple" />
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1.45fr)_minmax(340px,.75fr)]">
        <div className="panel overflow-hidden">
          <PanelHeader icon={GitBranch} title="Live agent trajectory" aside={<span className="status-pill border-success/30 bg-success/10 text-success"><span className="size-1.5 animate-pulse rounded-full bg-success" /> Executing</span>} />
          <div className="p-4 sm:p-5">
            <div className="mb-5 flex items-start gap-3 border-b border-border pb-4">
              <div className="grid size-9 shrink-0 place-items-center rounded-md bg-primary/10 text-primary"><Bot className="size-4" /></div>
              <div><p className="text-sm font-medium">Investigate critical scan delta</p><p className="mt-1 font-mono text-[10px] text-muted-foreground">RUN-ID 7f4c-92a1 · prod-us-east · autonomous level 2</p></div>
            </div>
            <div className="relative space-y-0">
              <div className="absolute bottom-7 left-[17px] top-7 w-px bg-border" />
              {trajectory.map((step, index) => {
                const Icon = step.icon;
                return <div key={step.id} className="group relative flex gap-3 py-2.5"><div className={cn("relative z-10 grid size-9 shrink-0 place-items-center rounded-md border bg-panel transition-colors", index === 4 ? "border-primary text-primary shadow-status-cyan" : "border-success/30 text-success")}><Icon className="size-4" /></div><div className="min-w-0 flex-1 rounded-md border border-transparent px-2 py-0.5 transition-colors group-hover:border-border group-hover:bg-muted/30"><div className="flex items-center justify-between gap-2"><p className="text-xs font-semibold"><span className="mr-2 font-mono text-[9px] text-muted-foreground">{step.id}</span>{step.title}</p><span className="font-mono text-[9px] text-muted-foreground">{step.time}</span></div><p className="mt-1 truncate font-mono text-[10px] text-muted-foreground">{step.detail}</p>{index === 2 && <WorkerAgents />}</div></div>;
              })}
            </div>
          </div>
        </div>

        <div className="space-y-5">
          <div className="panel overflow-hidden">
            <PanelHeader icon={BrainCircuit} title="Adaptive routing" aside={<span className="font-mono text-[9px] text-success">AUTO</span>} />
            <div className="space-y-3 p-4">
              <RoutingRow label="CVE lookup" model="Smart Intern" detail="On-prem · 22× cost saving" active />
              <RoutingRow label="Attack-chain synthesis" model="PhD Reasoner" detail="Escalated · high complexity" />
            </div>
          </div>
          <div className="panel overflow-hidden">
            <PanelHeader icon={Radar} title="Active scan context" aside={<span className="font-mono text-[9px] text-muted-foreground">14:42:18 UTC</span>} />
            <div className="grid grid-cols-2 divide-x divide-y divide-border">
              {[['Scope','AWS prod'],['Scanner','QScanner-07'],['Policies','CIS + PCI'],['Last delta','42 sec']].map(([label,value]) => <div key={label} className="p-3"><p className="text-[9px] uppercase text-muted-foreground">{label}</p><p className="mt-1 text-xs font-medium">{value}</p></div>)}
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(360px,.8fr)]">
        <VulnerabilityTable />
        <RemediationQueue onReview={onReview} approved={approved} />
      </section>
    </div>
  );
}

function MetricBadge({ label, value, tone }: { label: string; value: string; tone: "success" | "cyan" | "purple" }) {
  return <div className={cn("rounded-md border bg-panel px-3 py-2", tone === "success" && "border-success/25", tone === "cyan" && "border-primary/25", tone === "purple" && "border-agent/25")}><p className="text-[9px] uppercase text-muted-foreground">{label}</p><p className={cn("mt-0.5 font-mono text-sm font-semibold", tone === "success" && "text-success", tone === "cyan" && "text-primary", tone === "purple" && "text-agent")}>{value}</p></div>;
}

function ScoreCard() {
  return <div className="panel relative overflow-hidden p-4"><div className="absolute inset-y-0 right-0 w-1 bg-danger" /><div className="flex items-start justify-between"><div><p className="text-[10px] uppercase text-muted-foreground">Enterprise TruRisk</p><div className="mt-1 flex items-end gap-2"><span className="font-mono text-3xl font-semibold">742</span><span className="mb-1 text-[10px] text-muted-foreground">/ 1000</span></div></div><div className="grid size-10 place-items-center rounded-full border-2 border-danger/50 text-danger"><TrendingDown className="size-4" /></div></div><div className="mt-3 flex items-center gap-2 text-[10px]"><span className="text-danger">↑ 28 risk</span><span className="text-muted-foreground">in 24 hours</span></div></div>;
}

function StatCard({ icon: Icon, label, value, detail, tone }: { icon: typeof Server; label: string; value: string; detail: string; tone: string }) {
  return <div className="panel p-4"><div className="flex items-start justify-between"><div><p className="text-[10px] uppercase text-muted-foreground">{label}</p><p className="mt-2 font-mono text-2xl font-semibold">{value}</p></div><Icon className={cn("size-5", tone === "danger" ? "text-danger" : tone === "purple" ? "text-agent" : "text-primary")} /></div><p className="mt-3 text-[10px] text-muted-foreground">{detail}</p></div>;
}

function PanelHeader({ icon: Icon, title, aside }: { icon: typeof GitBranch; title: string; aside?: React.ReactNode }) {
  return <div className="flex h-12 items-center justify-between border-b border-border bg-panel-raised/50 px-4"><div className="flex items-center gap-2"><Icon className="size-4 text-primary" /><h2 className="text-xs font-semibold">{title}</h2></div>{aside}</div>;
}

function WorkerAgents() {
  return <div className="mt-3 grid gap-2 sm:grid-cols-3">{[["Asset mapper","12 nodes","success"],["Threat intel","3 feeds","primary"],["Policy verifier","CIS 2.0","agent"]].map(([name,detail,tone]) => <div key={name} className="rounded-md border border-border bg-background px-2.5 py-2"><div className="flex items-center gap-1.5"><span className={cn("size-1.5 rounded-full", tone === "success" ? "bg-success" : tone === "agent" ? "bg-agent" : "bg-primary")} /><p className="text-[9px] font-semibold">{name}</p></div><p className="mt-1 font-mono text-[8px] text-muted-foreground">{detail}</p></div>)}</div>;
}

function RoutingRow({ label, model, detail, active }: { label: string; model: string; detail: string; active?: boolean }) {
  return <div className={cn("rounded-md border p-3", active ? "border-primary/25 bg-primary/5" : "border-border bg-background")}><div className="flex items-center justify-between"><span className="text-[10px] text-muted-foreground">{label}</span>{active ? <Zap className="size-3 text-primary" /> : <ArrowUpRight className="size-3 text-agent" />}</div><p className="mt-1 text-xs font-semibold">{model}</p><p className="mt-1 font-mono text-[9px] text-muted-foreground">{detail}</p></div>;
}

function VulnerabilityTable() {
  return <div className="panel overflow-hidden"><PanelHeader icon={ShieldAlert} title="Priority threat intelligence" aside={<Button size="sm" variant="ghost" className="h-7 text-[10px]">All findings <ChevronRight className="size-3" /></Button>} /><div className="overflow-x-auto"><table className="w-full min-w-[620px] text-left"><thead><tr className="border-b border-border bg-panel-raised/30 text-[9px] uppercase text-muted-foreground"><th className="px-4 py-3 font-medium">Vulnerability</th><th className="px-4 py-3 font-medium">Affected</th><th className="px-4 py-3 font-medium">CVSS</th><th className="px-4 py-3 font-medium">Threat state</th></tr></thead><tbody>{vulnerabilities.map((item) => <tr key={item.cve} className="border-b border-border/70 last:border-0 hover:bg-muted/20"><td className="px-4 py-3"><p className="font-mono text-xs font-semibold text-foreground">{item.cve}</p><p className="mt-1 text-[10px] text-muted-foreground">{item.product}</p></td><td className="px-4 py-3 font-mono text-xs">{item.assets} assets</td><td className="px-4 py-3"><span className={cn("font-mono text-xs font-semibold", item.severity === "critical" ? "text-danger" : "text-warning")}>{item.cvss}</span></td><td className="px-4 py-3"><span className={cn("status-pill", item.severity === "critical" ? "border-danger/30 bg-danger/10 text-danger" : "border-warning/30 bg-warning/10 text-warning")}>{item.state}</span></td></tr>)}</tbody></table></div></div>;
}

function RemediationQueue({ onReview, approved }: { onReview: () => void; approved: boolean }) {
  return <div className="panel overflow-hidden"><PanelHeader icon={Code2} title="Remediation action queue" aside={<span className="status-pill border-warning/30 bg-warning/10 text-warning">3 pending</span>} /><div className="p-4"><div className="rounded-md border border-danger/30 bg-danger/5 p-4"><div className="flex items-start gap-3"><div className="grid size-8 shrink-0 place-items-center rounded-md bg-danger/10 text-danger"><AlertTriangle className="size-4" /></div><div><p className="font-mono text-xs font-semibold">CVE-2024-3094</p><p className="mt-1 text-[10px] leading-4 text-muted-foreground">Downgrade compromised XZ packages on 12 production hosts. Rolling strategy prepared.</p></div></div><div className="my-3 h-px bg-border" /><div className="flex items-center justify-between"><span className="text-[10px] text-muted-foreground">Blast radius <strong className="text-warning">Medium</strong></span><span className="font-mono text-[9px] text-success">98% confidence</span></div><Button onClick={onReview} className={cn("mt-4 w-full", approved && "bg-success text-success-foreground hover:bg-success/90")} disabled={approved}>{approved ? <><CheckCircle2 /> Approved for execution</> : <><ShieldCheck /> Review & Approve Patch</>}</Button></div><div className="mt-3 space-y-2">{["Rotate exposed SSH host keys", "Restart canary web tier"].map((action, index) => <div key={action} className="flex items-center gap-2 rounded-md border border-border px-3 py-2.5"><Clock3 className="size-3.5 text-muted-foreground" /><span className="text-[10px]">{action}</span><span className="ml-auto font-mono text-[9px] text-muted-foreground">P{index + 2}</span></div>)}</div></div></div>;
}

function ApprovalDialog({ open, onOpenChange, onApprove }: { open: boolean; onOpenChange: (open: boolean) => void; onApprove: () => void }) {
  return <Dialog open={open} onOpenChange={onOpenChange}><DialogContent className="max-w-2xl border-warning/40 bg-panel p-0 shadow-warning-glow"><DialogHeader className="border-b border-border p-5 pr-12 text-left"><div className="mb-2 flex items-center gap-2"><span className="status-pill border-warning/30 bg-warning/10 text-warning"><Fingerprint className="size-3" /> Human-In-The-Loop</span><span className="font-mono text-[9px] text-muted-foreground">APPROVAL HITL-8821</span></div><DialogTitle className="text-base">Authorize production remediation</DialogTitle><DialogDescription>This action changes 12 production hosts. Verify the command, scope, and rollback before approval.</DialogDescription></DialogHeader><div className="space-y-4 p-5"><div className="grid gap-3 sm:grid-cols-3">{[["Risk","Medium"],["Assets","12 hosts"],["Window","Rolling · 4 min"]].map(([label,value]) => <div key={label} className="rounded-md border border-border bg-background p-3"><p className="text-[9px] uppercase text-muted-foreground">{label}</p><p className="mt-1 text-xs font-semibold">{value}</p></div>)}</div><div><p className="mb-2 text-[10px] font-semibold uppercase text-muted-foreground">Proposed shell commands</p><pre className="overflow-x-auto rounded-md border border-border bg-terminal p-4 font-mono text-[10px] leading-5 text-terminal-foreground"><code>{`sudo apt-get update\nsudo apt-get install --allow-downgrades xz-utils=5.4.1-0.2\nsudo systemctl restart ssh --no-block\nxz --version && systemctl is-active ssh`}</code></pre></div><div className="flex gap-2 rounded-md border border-primary/20 bg-primary/5 p-3"><ShieldCheck className="mt-0.5 size-4 shrink-0 text-primary" /><p className="text-[10px] leading-4 text-muted-foreground">Guardrail check passed: signed package source verified, canary-first rollout enabled, automatic rollback at 5% health degradation.</p></div></div><DialogFooter className="border-t border-border bg-panel-raised/40 p-4"><Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button><Button onClick={onApprove} className="bg-warning text-warning-foreground hover:bg-warning/90"><Play /> Approve & Execute</Button></DialogFooter></DialogContent></Dialog>;
}

function EvalStudio({ drift }: { drift: boolean }) {
  return <div className="animate-fade-up space-y-5"><section className="flex flex-col justify-between gap-4 md:flex-row md:items-end"><div><span className="status-pill border-agent/30 bg-agent/10 text-agent"><BrainCircuit className="size-3" /> Production intelligence</span><h1 className="mt-3 text-2xl font-semibold sm:text-3xl">AI PRD & Eval Studio</h1><p className="mt-1 text-sm text-muted-foreground">Continuous evaluation for CyberRisk Resident model behavior.</p></div><div className="flex gap-2"><MetricBadge label="Eval runs" value="18,420" tone="cyan" /><MetricBadge label="Pass rate" value={drift ? "89.1%" : "96.8%"} tone={drift ? "purple" : "success"} /></div></section><section className="grid gap-5 xl:grid-cols-3"><div className="panel xl:col-span-2"><PanelHeader icon={Activity} title="RAG Triad · 7 hour window" aside={<span className="font-mono text-[9px] text-muted-foreground">Threshold 90%</span>} /><div className="h-[320px] p-4"><ResponsiveContainer width="100%" height="100%"><LineChart data={evalData}><CartesianGrid stroke="var(--chart-grid)" vertical={false} /><XAxis dataKey="time" stroke="var(--muted-foreground)" fontSize={9} tickLine={false} axisLine={false} /><YAxis domain={[75,100]} stroke="var(--muted-foreground)" fontSize={9} tickLine={false} axisLine={false} /><Tooltip contentStyle={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 6, fontSize: 11 }} /><Line type="monotone" dataKey="retrieval" stroke="var(--chart-cyan)" strokeWidth={2} dot={false} /><Line type="monotone" dataKey="groundedness" stroke="var(--chart-purple)" strokeWidth={2} dot={false} /><Line type="monotone" dataKey="relevance" stroke="var(--chart-amber)" strokeWidth={2} dot={false} /></LineChart></ResponsiveContainer></div><div className="flex flex-wrap gap-4 border-t border-border px-4 py-3">{[["Retrieval Quality","bg-primary"],["Groundedness","bg-agent"],["Answer Relevance","bg-warning"]].map(([label,color]) => <div key={label} className="flex items-center gap-2 text-[10px] text-muted-foreground"><span className={cn("size-2 rounded-full", color)} />{label}</div>)}</div></div><div className="panel"><PanelHeader icon={AlertTriangle} title="Quality drift telemetry" /><div className="p-4"><div className="h-40"><ResponsiveContainer width="100%" height="100%"><AreaChart data={evalData}><defs><linearGradient id="latency" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="var(--chart-red)" stopOpacity={0.3}/><stop offset="95%" stopColor="var(--chart-red)" stopOpacity={0}/></linearGradient></defs><Area type="monotone" dataKey="latency" stroke="var(--chart-red)" fill="url(#latency)" /><XAxis dataKey="time" hide /><Tooltip contentStyle={{ background: "var(--panel)", border: "1px solid var(--border)", fontSize: 11 }} /></AreaChart></ResponsiveContainer></div><div className="mt-3 space-y-3">{[["Knowledge freshness","99.2%","Healthy"],["Citation coverage","94.7%","Healthy"],["Embedding drift","6.8%", drift ? "Alert" : "Watch"]].map(([label,value,status]) => <div key={label} className="flex items-center justify-between border-b border-border pb-3 last:border-0"><div><p className="text-[10px] text-muted-foreground">{label}</p><p className="mt-1 font-mono text-sm">{value}</p></div><span className={cn("status-pill", status === "Healthy" ? "border-success/30 bg-success/10 text-success" : status === "Alert" ? "border-danger/30 bg-danger/10 text-danger" : "border-warning/30 bg-warning/10 text-warning")}>{status}</span></div>)}</div></div></div></section><EvalRuns /></div>;
}

function EvalRuns() {
  return <section className="panel overflow-hidden"><PanelHeader icon={CheckCircle2} title="Recent evaluation runs" aside={<Button variant="outline" size="sm" className="h-7 text-[10px]">Configure gates</Button>} /><div className="grid gap-px bg-border sm:grid-cols-3">{[["CR-EVAL-441","CVE response fidelity","97.4%","Passed"],["CR-EVAL-440","Adversarial context","91.2%","Passed"],["CR-EVAL-439","Citation grounding","86.7%","Review"]].map(([id,name,score,state]) => <div key={id} className="bg-panel p-4"><div className="flex justify-between"><span className="font-mono text-[9px] text-muted-foreground">{id}</span><span className={cn("text-[9px]", state === "Passed" ? "text-success" : "text-warning")}>{state}</span></div><p className="mt-3 text-xs font-semibold">{name}</p><p className="mt-2 font-mono text-xl">{score}</p></div>)}</div></section>;
}

function Roadmap() {
  return <div className="animate-fade-up"><section className="mb-6"><span className="status-pill border-agent/30 bg-agent/10 text-agent"><GitBranch className="size-3" /> Product horizon</span><h1 className="mt-3 text-2xl font-semibold sm:text-3xl">Resident Roadmap</h1><p className="mt-1 max-w-xl text-sm text-muted-foreground">The next autonomous operators joining the HorizonAI control plane.</p></section><div className="grid gap-5 lg:grid-cols-2"><RoadmapCard icon={Network} title="AttackSurface Resident" subtitle="External attack surface intelligence" accent="cyan" stats={["Continuous asset discovery","Shadow IT attribution","Attack-path prioritization"]} /><RoadmapCard icon={FileCheck2} title="ComplianceSentinel" subtitle="Continuous control assurance" accent="purple" stats={["Evidence auto-collection","Control drift detection","Audit-ready narratives"]} /></div><section className="mt-5 panel p-5"><div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between"><div><p className="text-[10px] uppercase text-muted-foreground">Resident architecture</p><p className="mt-1 text-sm font-semibold">One context fabric. Specialized autonomous operators.</p></div><div className="flex items-center gap-2 overflow-x-auto">{["CyberRisk","AttackSurface","Compliance"].map((name,index) => <div key={name} className={cn("flex shrink-0 items-center gap-2 rounded-md border px-3 py-2 text-[10px]", index === 0 ? "border-success/30 bg-success/5 text-success" : "border-border text-muted-foreground")}><span className={cn("size-1.5 rounded-full", index === 0 ? "bg-success" : "bg-muted-foreground")} />{name}</div>)}</div></div></section></div>;
}

function RoadmapCard({ icon: Icon, title, subtitle, accent, stats }: { icon: typeof Network; title: string; subtitle: string; accent: "cyan" | "purple"; stats: string[] }) {
  return <article className={cn("panel group relative overflow-hidden p-6 transition-transform hover:-translate-y-1", accent === "cyan" ? "hover:border-primary/40" : "hover:border-agent/40")}><div className={cn("absolute right-0 top-0 h-24 w-24 opacity-10", accent === "cyan" ? "bg-primary" : "bg-agent")} /><div className="flex items-start justify-between"><div className={cn("grid size-11 place-items-center rounded-md border", accent === "cyan" ? "border-primary/30 bg-primary/10 text-primary" : "border-agent/30 bg-agent/10 text-agent")}><Icon className="size-5" /></div><span className="status-pill border-warning/30 bg-warning/10 text-warning">Coming in Phase 4</span></div><h2 className="mt-8 text-xl font-semibold">{title}</h2><p className="mt-1 text-xs text-muted-foreground">{subtitle}</p><div className="mt-6 space-y-3">{stats.map((item) => <div key={item} className="flex items-center gap-2 border-b border-border pb-3 last:border-0"><Check className={cn("size-3.5", accent === "cyan" ? "text-primary" : "text-agent")} /><span className="text-xs">{item}</span></div>)}</div><Button variant="ghost" className="mt-4 px-0 text-muted-foreground">Preview capability map <ArrowUpRight /></Button></article>;
}

function DriftBanner() {
  return <div className="mb-5 flex flex-col gap-3 rounded-md border border-danger/40 bg-danger/10 p-3 sm:flex-row sm:items-center"><div className="flex items-center gap-2"><AlertTriangle className="size-4 text-danger" /><div><p className="text-xs font-semibold text-danger">Data Drift Detected</p><p className="text-[10px] text-muted-foreground">Embedding distribution shifted 6.8% in the last evaluation window.</p></div></div><Button variant="outline" size="sm" className="sm:ml-auto">Open drift report</Button></div>;
}

function LoadingState() {
  return <div className="space-y-5" aria-label="Loading cyber risk data"><div className="space-y-2"><Skeleton className="h-5 w-32" /><Skeleton className="h-9 w-72 max-w-full" /></div><div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">{Array.from({ length: 4 }).map((_,i) => <Skeleton key={i} className="h-32" />)}</div><div className="grid gap-5 xl:grid-cols-[1.45fr_.75fr]"><Skeleton className="h-[480px]" /><div className="space-y-5"><Skeleton className="h-60" /><Skeleton className="h-44" /></div></div></div>;
}

function OfflineState({ onRetry }: { onRetry: () => void }) {
  return <div className="grid min-h-[70vh] place-items-center"><div className="max-w-md text-center"><div className="mx-auto grid size-14 place-items-center rounded-md border border-border bg-panel"><CloudOff className="size-6 text-muted-foreground" /></div><h1 className="mt-5 text-xl font-semibold">Live telemetry unavailable</h1><p className="mt-2 text-sm leading-6 text-muted-foreground">The latest verified snapshot remains protected. Reconnect to resume agent trajectories and scan updates.</p><div className="mt-4 rounded-md border border-border bg-panel p-3 text-left font-mono text-[10px] text-muted-foreground"><div className="flex justify-between"><span>Last trusted sync</span><span className="text-foreground">14:41:36 UTC</span></div><div className="mt-2 flex justify-between"><span>Cached assets</span><span className="text-foreground">2,847</span></div></div><Button onClick={onRetry} className="mt-5"><RefreshCw /> Retry connection</Button></div></div>;
}