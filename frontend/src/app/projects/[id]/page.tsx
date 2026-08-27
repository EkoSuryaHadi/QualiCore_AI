"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type Project = {
  id: string;
  code: string;
  name: string;
  client_name?: string | null;
  location?: string | null;
  start_date?: string | null;
  finish_date?: string | null;
  status: string;
  progress: number;
};

type Workspace = {
  project: Project;
  total_inspections: number;
  failed_inspections: number;
  open_ncr: number;
  critical_ncr: number;
  open_punch: number;
  overdue_punch: number;
  evidence_count: number;
  open_documents: number;
  high_risks: number;
  quality_score: number;
};

export default function ProjectWorkspacePage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [data, setData] = useState<Workspace | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    api<Workspace>(`/projects/${id}/workspace`)
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load project workspace"))
      .finally(() => setLoading(false));
  }, [id]);

  const projectHref = (path: string) => `${path}?project_id=${encodeURIComponent(id)}`;

  return (
    <AuthGuard>
      <Shell>
        {loading ? <p className="muted">Loading project workspace...</p> : null}
        {error ? <div className="error">{error}</div> : null}
        {data ? (
          <>
            <div className="page-head">
              <div>
                <p className="eyebrow">{data.project.code}</p>
                <h1>{data.project.name}</h1>
                <p className="muted">{data.project.client_name || "No client"} · {data.project.location || "No location"}</p>
              </div>
              <div className="head-actions">
                <Link className="secondary-btn" href="/projects">← Projects</Link>
                <Link className="btn-link" href={`/projects/${id}/edit`}>Edit Project</Link>
              </div>
            </div>

            <div className="card project-overview">
              <div><span className="muted small">Status</span><strong><span className={`status status-${data.project.status.toLowerCase()}`}>{data.project.status}</span></strong></div>
              <div><span className="muted small">Progress</span><strong>{data.project.progress || 0}%</strong></div>
              <div><span className="muted small">Start</span><strong>{data.project.start_date || "—"}</strong></div>
              <div><span className="muted small">Finish</span><strong>{data.project.finish_date || "—"}</strong></div>
              <div className="overview-progress"><div className="progress-line"><span style={{ width: `${Math.max(0, Math.min(100, data.project.progress || 0))}%` }} /></div></div>
            </div>

            <div className="grid workspace-metrics">
              <Metric label="Quality Score" value={`${data.quality_score}%`} />
              <Metric label="Inspections" value={data.total_inspections} sub={`${data.failed_inspections} failed`} />
              <Metric label="Open NCR" value={data.open_ncr} sub={`${data.critical_ncr} high / critical`} />
              <Metric label="Open Punch" value={data.open_punch} sub={`${data.overdue_punch} overdue`} />
              <Metric label="Open Documents" value={data.open_documents} />
              <Metric label="High Risks" value={data.high_risks} />
              <Metric label="Evidence" value={data.evidence_count} />
            </div>

            <div className="card section-card">
              <div className="toolbar"><div><h2>Assurance Modules</h2><p className="muted small">Open assurance records already scoped to this project.</p></div></div>
              <div className="module-grid">
                <ModuleLink href={projectHref("/inspections")} title="Inspections / ITP" text="Inspection records and quality results" />
                <ModuleLink href={projectHref("/ncrs")} title="NCR" text="Non-conformance and corrective actions" />
                <ModuleLink href={projectHref("/punchlist")} title="Punch List" text="Outstanding completion items" />
                <ModuleLink href={projectHref("/documents")} title="Document Control" text="Revisions, review and approval" />
                <ModuleLink href={projectHref("/risks")} title="Risk Register" text="Quality and assurance risks" />
                <ModuleLink href={projectHref("/audit")} title="Audit Trail" text="Recorded project actions" />
              </div>
            </div>
          </>
        ) : null}
      </Shell>
    </AuthGuard>
  );
}

function Metric({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return <div className="card"><div className="muted">{label}</div><div className="metric">{value}</div>{sub ? <div className="muted small">{sub}</div> : null}</div>;
}

function ModuleLink({ href, title, text }: { href: string; title: string; text: string }) {
  return <Link className="module-card" href={href}><strong>{title}</strong><span className="muted small">{text}</span><span className="module-arrow">→</span></Link>;
}
