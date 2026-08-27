"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type Project = { id: string; code: string; name: string };
type Finding = {
  code: string;
  severity: string;
  confidence: number;
  workstream: string;
  title: string;
  rationale: string;
  recommended_action: string;
  project_id?: string | null;
  project_code?: string | null;
  evidence?: Record<string, unknown> | null;
};
type Analysis = {
  scope: string;
  project_id?: string | null;
  project_count: number;
  assurance_index: number;
  health_status: string;
  finding_count: number;
  severity_counts: Record<string, number>;
  findings: Finding[];
};

export default function AssurancePage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
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
    api<Analysis>(`/assurance/analyze${query}`)
      .then(setAnalysis)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to analyze assurance data"))
      .finally(() => setLoading(false));
  }, [projectId]);

  const selected = projects.find((p) => p.id === projectId);
  const findings = useMemo(() => analysis?.findings || [], [analysis]);
  const healthClass = analysis?.health_status === "GOOD" ? "health-good" : analysis?.health_status === "ATTENTION" ? "health-attention" : "health-critical";

  return (
    <AuthGuard>
      <Shell>
        <div className="page-head">
          <div>
            <p className="eyebrow">AI Assurance Engine</p>
            <h1>Assurance Findings</h1>
            <p className="muted">Deterministic early warnings generated from live assurance records across EPC workstreams.</p>
          </div>
          <div className="head-actions">
            {selected ? <Link className="secondary-btn" href={`/projects/${selected.id}`}>Project Workspace</Link> : null}
            <Link className="secondary-btn" href="/reports">Executive Report</Link>
          </div>
        </div>

        <div className="card report-filter">
          <label>
            <span>Analysis Scope</span>
            <select value={projectId} onChange={(e) => setProjectId(e.target.value)}>
              <option value="">Portfolio — All Projects</option>
              {projects.map((p) => <option key={p.id} value={p.id}>{p.code} — {p.name}</option>)}
            </select>
          </label>
        </div>

        {error ? <div className="error">{error}</div> : null}
        {loading ? <p className="muted">Running assurance analysis...</p> : null}

        {analysis ? (
          <>
            <div className="executive-grid section-card">
              <div className="card assurance-hero">
                <div className="muted">AI Assurance Index</div>
                <div className="assurance-score">{analysis.assurance_index}</div>
                <div className={`health-pill ${healthClass}`}>{analysis.health_status}</div>
                <div className="score-track"><span style={{ width: `${analysis.assurance_index}%` }} /></div>
              </div>
              <div className="grid dashboard-kpis">
                <Metric label="Critical Findings" value={analysis.severity_counts.CRITICAL || 0} alert={(analysis.severity_counts.CRITICAL || 0) > 0} />
                <Metric label="High Findings" value={analysis.severity_counts.HIGH || 0} alert={(analysis.severity_counts.HIGH || 0) > 0} />
                <Metric label="Medium Findings" value={analysis.severity_counts.MEDIUM || 0} />
                <Metric label="Projects Analyzed" value={analysis.project_count} />
              </div>
            </div>

            <div className="card section-card">
              <div className="toolbar"><div><h2>Priority Findings</h2><p className="muted small">Sorted by severity and confidence. Each finding is traceable to source records and explicit rules.</p></div><strong>{analysis.finding_count} finding(s)</strong></div>
              {!findings.length ? <div className="empty-state">No material assurance findings detected. Continue routine monitoring.</div> : <div className="assurance-findings">{findings.map((finding, index) => <FindingCard key={`${finding.code}-${finding.project_id || index}`} finding={finding} />)}</div>}
            </div>

            <div className="source-banner section-card">Engine v1 is deterministic and auditable. It does not use an LLM yet; every finding is generated from defined assurance rules and current project records.</div>
          </>
        ) : null}
      </Shell>
    </AuthGuard>
  );
}

function Metric({ label, value, alert = false }: { label: string; value: number; alert?: boolean }) {
  return <div className={`card dashboard-metric ${alert ? "metric-alert" : ""}`}><div className="muted">{label}</div><div className="metric">{value}</div></div>;
}

function FindingCard({ finding }: { finding: Finding }) {
  const severityClass = finding.severity === "CRITICAL" ? "severity-critical" : finding.severity === "HIGH" ? "severity-high" : finding.severity === "MEDIUM" ? "severity-medium" : "severity-low";
  return <article className="finding-card">
    <div className="finding-head">
      <div><div className="finding-meta"><span className={`severity ${severityClass}`}>{finding.severity}</span><span className="workflow workflow-open">{finding.workstream.replace("_", " ")}</span>{finding.project_code ? <span className="project-code">{finding.project_code}</span> : null}</div><h3>{finding.title}</h3></div>
      <div className="confidence-badge">{Math.round(finding.confidence * 100)}% confidence</div>
    </div>
    <div className="finding-body">
      <div><span className="muted small">WHY THIS WAS FLAGGED</span><p>{finding.rationale}</p></div>
      <div className="recommended-action"><span className="muted small">RECOMMENDED ACTION</span><p>{finding.recommended_action}</p></div>
    </div>
    <div className="muted small">Rule: {finding.code}</div>
  </article>;
}
