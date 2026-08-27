"use client";

// deployment trigger: executive assurance dashboard v1
import Link from "next/link";
import { useEffect, useState } from "react";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type ProjectHealth = {
  project_id: string;
  code: string;
  name: string;
  progress: number;
  quality_score: number;
  failed_inspections: number;
  open_ncr: number;
  open_punch: number;
  open_documents: number;
  high_risks: number;
  vendor_watchlist: number;
};

type Dashboard = {
  total_projects: number;
  active_projects: number;
  total_inspections: number;
  failed_inspections: number;
  pass_rate: number;
  open_ncr: number;
  critical_ncr: number;
  open_punch: number;
  overdue_punch: number;
  open_documents: number;
  documents_in_review: number;
  high_risks: number;
  open_risks: number;
  vendor_count: number;
  vendor_watchlist: number;
  vendor_suspended: number;
  average_vendor_score: number;
  assurance_score: number;
  health_status: string;
  projects: ProjectHealth[];
};

export default function DashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Dashboard>("/dashboard/executive")
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load dashboard"));
  }, []);

  const healthClass = data?.health_status === "GOOD" ? "health-good" : data?.health_status === "ATTENTION" ? "health-attention" : "health-critical";

  return (
    <AuthGuard>
      <Shell>
        <div className="page-head dashboard-head">
          <div>
            <p className="eyebrow">Executive Assurance</p>
            <h1>Portfolio Assurance</h1>
            <p className="muted">Live quality, completion, document, risk and vendor assurance across active EPC projects.</p>
          </div>
          {data ? <div className={`health-pill ${healthClass}`}>{data.health_status}</div> : null}
        </div>

        {error ? <div className="error">{error}</div> : null}
        {!data ? <p className="muted">Loading assurance dashboard...</p> : (
          <>
            <div className="executive-grid">
              <div className="card assurance-hero">
                <div className="muted">Portfolio Assurance Score</div>
                <div className="assurance-score">{data.assurance_score}</div>
                <div className="muted small">Composite exposure indicator · higher is better</div>
                <div className="score-track"><span style={{ width: `${data.assurance_score}%` }} /></div>
              </div>
              <div className="grid dashboard-kpis">
                <Metric label="Active Projects" value={data.active_projects} sub={`${data.total_projects} total`} />
                <Metric label="Inspection Pass Rate" value={`${data.pass_rate}%`} sub={`${data.failed_inspections} failed`} />
                <Metric label="Critical NCR" value={data.critical_ncr} sub={`${data.open_ncr} open total`} alert={data.critical_ncr > 0} />
                <Metric label="High Risks" value={data.high_risks} sub={`${data.open_risks} open risks`} alert={data.high_risks > 0} />
              </div>
            </div>

            <div className="grid dashboard-kpis section-card">
              <Metric label="Open Punch" value={data.open_punch} sub={`${data.overdue_punch} overdue`} alert={data.overdue_punch > 0} />
              <Metric label="Open Documents" value={data.open_documents} sub={`${data.documents_in_review} in review`} />
              <Metric label="Vendor Watchlist" value={data.vendor_watchlist} sub={`${data.vendor_suspended} suspended`} alert={data.vendor_watchlist + data.vendor_suspended > 0} />
              <Metric label="Avg Vendor Score" value={data.average_vendor_score} sub={`${data.vendor_count} vendors`} />
            </div>

            <div className="card section-card">
              <div className="toolbar">
                <div>
                  <h2>Project Assurance Ranking</h2>
                  <p className="muted small">Projects are ranked from highest assurance exposure to healthiest.</p>
                </div>
                <Link className="secondary-btn" href="/projects">View Projects</Link>
              </div>
              {!data.projects.length ? <div className="empty-state">No projects available yet.</div> : (
                <div className="table-wrap">
                  <table className="data-table dashboard-table">
                    <thead><tr><th>Project</th><th>Assurance</th><th>Progress</th><th>Failed Insp.</th><th>Open NCR</th><th>Punch</th><th>Docs</th><th>High Risk</th><th>Vendor Alert</th><th></th></tr></thead>
                    <tbody>{data.projects.map((p) => (
                      <tr key={p.project_id}>
                        <td><strong>{p.code}</strong><div className="muted small">{p.name}</div></td>
                        <td><span className={`risk-score ${p.quality_score >= 85 ? "risk-score-low" : p.quality_score >= 70 ? "risk-score-medium" : "risk-score-high"}`}>{p.quality_score}</span></td>
                        <td>{p.progress}%</td>
                        <td>{p.failed_inspections}</td>
                        <td>{p.open_ncr}</td>
                        <td>{p.open_punch}</td>
                        <td>{p.open_documents}</td>
                        <td>{p.high_risks}</td>
                        <td>{p.vendor_watchlist}</td>
                        <td><Link className="text-link" href={`/projects/${p.project_id}`}>Workspace →</Link></td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="card section-card">
              <div className="toolbar"><div><h2>Assurance Workstreams</h2><p className="muted small">Jump directly to open assurance workflows.</p></div></div>
              <div className="module-grid">
                <QuickLink href="/inspections" title="Inspections" text={`${data.failed_inspections} failed inspections`} />
                <QuickLink href="/ncrs" title="NCR" text={`${data.open_ncr} open NCR`} />
                <QuickLink href="/punchlist" title="Punch List" text={`${data.overdue_punch} overdue punch`} />
                <QuickLink href="/documents" title="Document Control" text={`${data.documents_in_review} documents in review`} />
                <QuickLink href="/risks" title="Risk Register" text={`${data.high_risks} high risks`} />
                <QuickLink href="/vendors" title="Vendor Quality" text={`${data.vendor_watchlist} vendors on watchlist`} />
              </div>
            </div>
          </>
        )}
      </Shell>
    </AuthGuard>
  );
}

function Metric({ label, value, sub, alert = false }: { label: string; value: string | number; sub?: string; alert?: boolean }) {
  return <div className={`card dashboard-metric ${alert ? "metric-alert" : ""}`}><div className="muted">{label}</div><div className="metric">{value}</div>{sub ? <div className="muted small">{sub}</div> : null}</div>;
}

function QuickLink({ href, title, text }: { href: string; title: string; text: string }) {
  return <Link className="module-card" href={href}><strong>{title}</strong><span className="muted small">{text}</span><span className="module-arrow">→</span></Link>;
}
