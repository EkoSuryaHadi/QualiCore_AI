"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type Project = { id: string; code: string; name: string };
type Report = {
  generated_at: string;
  scope: string;
  project_id?: string | null;
  project_code?: string | null;
  project_name?: string | null;
  project_count: number;
  active_projects: number;
  assurance_score: number;
  health_status: string;
  total_inspections: number;
  failed_inspections: number;
  pass_rate: number;
  open_ncr: number;
  critical_ncr: number;
  open_punch: number;
  overdue_punch: number;
  open_documents: number;
  documents_in_review: number;
  open_risks: number;
  high_risks: number;
  vendor_count: number;
  vendor_watchlist: number;
  vendor_suspended: number;
  average_vendor_score: number;
  narrative: string;
  priorities: string[];
};

export default function ReportsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setProjectId(params.get("project_id") || "");
    api<Project[]>("/projects").then(setProjects).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    setError("");
    const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
    api<Report>(`/reports/executive${query}`)
      .then(setReport)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to generate report"))
      .finally(() => setLoading(false));
  }, [projectId]);

  function downloadCsv() {
    if (!report) return;
    const rows: (string | number)[][] = [
      ["QualiCore Executive Assurance Report"],
      ["Generated At", new Date(report.generated_at).toLocaleString()],
      ["Scope", report.scope],
    ];
    if (report.project_code) rows.push(["Project", `${report.project_code} - ${report.project_name || ""}`]);
    rows.push(
      [],
      ["Metric", "Value"],
      ["Assurance Score", report.assurance_score],
      ["Health Status", report.health_status],
      ["Inspection Pass Rate", `${report.pass_rate}%`],
      ["Failed Inspections", report.failed_inspections],
      ["Open NCR", report.open_ncr],
      ["High/Critical NCR", report.critical_ncr],
      ["Open Punch", report.open_punch],
      ["Overdue Punch", report.overdue_punch],
      ["Open Documents", report.open_documents],
      ["Documents In Review", report.documents_in_review],
      ["Open Risks", report.open_risks],
      ["High Risks", report.high_risks],
      ["Vendor Count", report.vendor_count],
      ["Vendor Watchlist", report.vendor_watchlist],
      ["Vendor Suspended", report.vendor_suspended],
      ["Average Vendor Score", report.average_vendor_score],
      [],
      ["Executive Narrative", report.narrative],
      [],
      ["Priority Actions"],
      ...report.priorities.map((p) => [p]),
    );
    const csv = rows.map((row) => row.map(csvCell).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `qualicore-${report.project_code || "portfolio"}-assurance-report.csv`.toLowerCase();
    anchor.click();
    URL.revokeObjectURL(url);
  }

  const selectedProject = projects.find((p) => p.id === projectId);
  const healthClass = report?.health_status === "GOOD" ? "health-good" : report?.health_status === "ATTENTION" ? "health-attention" : "health-critical";

  return (
    <AuthGuard>
      <Shell>
        <div className="report-screen">
          <div className="page-head report-toolbar">
            <div>
              <p className="eyebrow">Assurance Reporting</p>
              <h1>Executive Report</h1>
              <p className="muted">Generate a current assurance snapshot for the portfolio or a selected EPC project.</p>
            </div>
            <div className="head-actions no-print">
              {selectedProject ? <Link className="secondary-btn" href={`/projects/${selectedProject.id}`}>Project Workspace</Link> : null}
              <button className="secondary-btn" onClick={() => window.print()}>Print / PDF</button>
              <button className="btn-action" onClick={downloadCsv} disabled={!report}>Download CSV</button>
            </div>
          </div>

          <div className="card report-filter no-print">
            <label>
              <span>Report Scope</span>
              <select value={projectId} onChange={(e) => setProjectId(e.target.value)}>
                <option value="">Portfolio — All Projects</option>
                {projects.map((p) => <option key={p.id} value={p.id}>{p.code} — {p.name}</option>)}
              </select>
            </label>
          </div>

          {error ? <div className="error">{error}</div> : null}
          {loading ? <p className="muted">Generating assurance report...</p> : null}

          {report ? (
            <article className="report-paper">
              <div className="report-cover">
                <div>
                  <div className="report-brand">QUALICORE AI</div>
                  <p className="eyebrow">Executive Assurance Snapshot</p>
                  <h2>{report.project_code ? `${report.project_code} — ${report.project_name}` : "Portfolio Assurance Report"}</h2>
                  <p className="muted">Generated {new Date(report.generated_at).toLocaleString()}</p>
                </div>
                <div className={`health-pill ${healthClass}`}>{report.health_status}</div>
              </div>

              <div className="report-score-block">
                <div>
                  <div className="muted">Assurance Score</div>
                  <div className="assurance-score">{report.assurance_score}</div>
                </div>
                <div className="report-narrative">
                  <h3>Executive Summary</h3>
                  <p>{report.narrative}</p>
                </div>
              </div>

              <div className="grid report-kpis">
                <ReportMetric label="Inspection Pass Rate" value={`${report.pass_rate}%`} sub={`${report.failed_inspections} failed / ${report.total_inspections} total`} />
                <ReportMetric label="Open NCR" value={report.open_ncr} sub={`${report.critical_ncr} high / critical`} alert={report.critical_ncr > 0} />
                <ReportMetric label="Open Punch" value={report.open_punch} sub={`${report.overdue_punch} overdue`} alert={report.overdue_punch > 0} />
                <ReportMetric label="Open Documents" value={report.open_documents} sub={`${report.documents_in_review} in review`} />
                <ReportMetric label="High Risks" value={report.high_risks} sub={`${report.open_risks} open total`} alert={report.high_risks > 0} />
                <ReportMetric label="Vendor Alerts" value={report.vendor_watchlist + report.vendor_suspended} sub={`${report.vendor_watchlist} watchlist · ${report.vendor_suspended} suspended`} alert={report.vendor_watchlist + report.vendor_suspended > 0} />
                <ReportMetric label="Average Vendor Score" value={report.average_vendor_score} sub={`${report.vendor_count} vendor records`} />
                <ReportMetric label="Projects" value={report.project_count} sub={report.scope === "PORTFOLIO" ? `${report.active_projects} active` : "Selected project"} />
              </div>

              <section className="report-section">
                <h3>Priority Actions</h3>
                <div className="priority-list">
                  {report.priorities.map((priority, index) => (
                    <div className="priority-row" key={priority}>
                      <span className="priority-index">{index + 1}</span>
                      <span>{priority}</span>
                    </div>
                  ))}
                </div>
              </section>

              <section className="report-section">
                <h3>Assurance Exposure Detail</h3>
                <div className="table-wrap">
                  <table className="data-table report-table">
                    <thead><tr><th>Workstream</th><th>Primary KPI</th><th>Exposure</th></tr></thead>
                    <tbody>
                      <tr><td>Inspection / ITP</td><td>{report.pass_rate}% pass rate</td><td>{report.failed_inspections} failed inspections</td></tr>
                      <tr><td>NCR & Corrective Action</td><td>{report.open_ncr} open</td><td>{report.critical_ncr} high / critical</td></tr>
                      <tr><td>Punch List</td><td>{report.open_punch} open</td><td>{report.overdue_punch} overdue</td></tr>
                      <tr><td>Document Control</td><td>{report.open_documents} open</td><td>{report.documents_in_review} in review</td></tr>
                      <tr><td>Risk Register</td><td>{report.open_risks} open</td><td>{report.high_risks} high risks</td></tr>
                      <tr><td>Vendor Quality</td><td>{report.average_vendor_score} avg score</td><td>{report.vendor_watchlist + report.vendor_suspended} alerts</td></tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <footer className="report-footer">QualiCore AI · Assure Before Failure · Snapshot reflects records available at generation time.</footer>
            </article>
          ) : null}
        </div>
      </Shell>
    </AuthGuard>
  );
}

function ReportMetric({ label, value, sub, alert = false }: { label: string; value: string | number; sub: string; alert?: boolean }) {
  return <div className={`card report-metric ${alert ? "metric-alert" : ""}`}><div className="muted small">{label}</div><div className="metric metric-small">{value}</div><div className="muted small">{sub}</div></div>;
}

function csvCell(value: string | number) {
  const text = String(value ?? "");
  return `"${text.replaceAll('"', '""')}"`;
}
