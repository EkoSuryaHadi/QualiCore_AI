"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type Punch = {
  id: string;
  project_id: string;
  description: string;
  category: string;
  severity: string;
  status: string;
  owner_name?: string | null;
  due_date?: string | null;
  created_at: string;
};
type Project = { id: string; code: string; name: string };

export default function PunchRegisterPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [items, setItems] = useState<Punch[]>([]);
  const [projectId, setProjectId] = useState("");
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    setProjectId(query.get("project_id") || "");
    api<Project[]>("/projects").then(setProjects).catch((e) => setError(e instanceof Error ? e.message : "Failed to load projects"));
  }, []);

  useEffect(() => {
    setLoading(true);
    setError("");
    const qs = new URLSearchParams();
    if (projectId) qs.set("project_id", projectId);
    if (status) qs.set("status", status);
    api<Punch[]>(`/punch${qs.toString() ? `?${qs}` : ""}`)
      .then(setItems)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load punch items"))
      .finally(() => setLoading(false));
  }, [projectId, status]);

  const visible = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return items;
    return items.filter((x) => `${x.description} ${x.category} ${x.owner_name || ""}`.toLowerCase().includes(q));
  }, [items, search]);

  const open = items.filter((x) => x.status !== "CLOSED").length;
  const high = items.filter((x) => x.status !== "CLOSED" && (x.severity === "HIGH" || x.severity === "CRITICAL")).length;
  const overdue = items.filter((x) => x.status !== "CLOSED" && x.due_date && new Date(`${x.due_date}T23:59:59`).getTime() < Date.now()).length;
  const closed = items.filter((x) => x.status === "CLOSED").length;
  const selectedProject = projects.find((p) => p.id === projectId);
  const newHref = projectId ? `/punchlist/new?project_id=${encodeURIComponent(projectId)}` : "/punchlist/new";

  return (
    <AuthGuard>
      <Shell>
        <div className="page-head">
          <div>
            <p className="eyebrow">Completion Assurance</p>
            <h1>Punch List Register</h1>
            <p className="muted">{selectedProject ? `${selectedProject.code} · ${selectedProject.name}` : "Track outstanding completion items, ownership and closure."}</p>
          </div>
          <div className="head-actions">
            {selectedProject ? <Link className="secondary-btn" href={`/projects/${selectedProject.id}`}>← Project Workspace</Link> : null}
            <Link className="btn-link" href={newHref}>+ New Punch Item</Link>
          </div>
        </div>

        <div className="grid inspection-metrics">
          <Metric label="Open Punch" value={open} />
          <Metric label="High / Critical" value={high} />
          <Metric label="Overdue" value={overdue} />
          <Metric label="Closed" value={closed} />
        </div>

        <div className="card section-card">
          <div className="filter-bar">
            <input className="search-input" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search description, category, owner..." />
            <select value={projectId} onChange={(e) => setProjectId(e.target.value)}>
              <option value="">All projects</option>
              {projects.map((p) => <option key={p.id} value={p.id}>{p.code} — {p.name}</option>)}
            </select>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">All status</option>
              <option>OPEN</option>
              <option>IN_PROGRESS</option>
              <option>CLOSED</option>
            </select>
          </div>

          {error ? <div className="error">{error}</div> : null}
          {loading ? <p className="muted">Loading punch items...</p> : null}
          {!loading && !visible.length ? <div className="empty-state">No punch items found.</div> : null}
          {!loading && visible.length ? (
            <div className="table-wrap">
              <table className="data-table">
                <thead><tr><th>Item</th><th>Category</th><th>Severity</th><th>Status</th><th>Owner</th><th>Due</th><th></th></tr></thead>
                <tbody>
                  {visible.map((x) => {
                    const isOverdue = x.status !== "CLOSED" && x.due_date && new Date(`${x.due_date}T23:59:59`).getTime() < Date.now();
                    return <tr key={x.id}>
                      <td><strong>{x.description}</strong></td>
                      <td>{x.category}</td>
                      <td><span className={`severity severity-${x.severity.toLowerCase()}`}>{x.severity}</span></td>
                      <td><span className={`workflow workflow-${x.status.toLowerCase()}`}>{x.status.replace("_", " ")}</span></td>
                      <td>{x.owner_name || "—"}</td>
                      <td>{x.due_date || "—"}{isOverdue ? <span className="overdue-text"> Overdue</span> : null}</td>
                      <td><Link className="text-link" href={`/punchlist/${x.id}`}>View →</Link></td>
                    </tr>;
                  })}
                </tbody>
              </table>
            </div>
          ) : null}
        </div>
      </Shell>
    </AuthGuard>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return <div className="card"><div className="muted">{label}</div><div className="metric">{value}</div></div>;
}
