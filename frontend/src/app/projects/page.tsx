"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type Project = {
  id: string;
  code: string;
  name: string;
  client_name?: string | null;
  location?: string | null;
  status: "ACTIVE" | "HOLD" | "COMPLETED";
  progress: number;
  start_date?: string | null;
  finish_date?: string | null;
};

export default function ProjectsPage() {
  const [items, setItems] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");

  useEffect(() => {
    api<Project[]>("/projects")
      .then(setItems)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load projects"))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter((p) =>
      [p.code, p.name, p.client_name, p.location, p.status]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(q)),
    );
  }, [items, query]);

  const active = items.filter((p) => p.status === "ACTIVE").length;
  const onHold = items.filter((p) => p.status === "HOLD").length;
  const avgProgress = items.length
    ? Math.round(items.reduce((sum, p) => sum + Number(p.progress || 0), 0) / items.length)
    : 0;

  return (
    <AuthGuard>
      <Shell>
        <div className="page-head">
          <div>
            <p className="eyebrow">Module 01</p>
            <h1>Project Management</h1>
            <p className="muted">Manage EPC projects and open each project assurance workspace.</p>
          </div>
          <Link className="btn-link" href="/projects/new">+ New Project</Link>
        </div>

        <div className="grid project-metrics">
          <div className="card"><div className="muted">Total Projects</div><div className="metric">{items.length}</div></div>
          <div className="card"><div className="muted">Active</div><div className="metric">{active}</div></div>
          <div className="card"><div className="muted">On Hold</div><div className="metric">{onHold}</div></div>
          <div className="card"><div className="muted">Average Progress</div><div className="metric">{avgProgress}%</div></div>
        </div>

        <div className="card section-card">
          <div className="toolbar">
            <div>
              <h2>Projects</h2>
              <p className="muted small">Select a project to view its assurance workspace.</p>
            </div>
            <input
              className="search-input"
              placeholder="Search project, client, location..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>

          {error ? <div className="error">{error}</div> : null}
          {loading ? <p className="muted">Loading projects...</p> : null}
          {!loading && !filtered.length ? <div className="empty-state">No projects found.</div> : null}

          {!loading && filtered.length ? (
            <div className="project-list">
              {filtered.map((p) => (
                <Link className="project-row" href={`/projects/${p.id}`} key={p.id}>
                  <div className="project-main">
                    <div className="project-code">{p.code}</div>
                    <div>
                      <strong>{p.name}</strong>
                      <div className="muted small">{p.client_name || "No client"} · {p.location || "No location"}</div>
                    </div>
                  </div>
                  <div className="project-status-wrap">
                    <span className={`status status-${p.status.toLowerCase()}`}>{p.status.replace("_", " ")}</span>
                    <div className="progress-line"><span style={{ width: `${Math.max(0, Math.min(100, p.progress || 0))}%` }} /></div>
                    <span className="small">{p.progress || 0}%</span>
                  </div>
                </Link>
              ))}
            </div>
          ) : null}
        </div>
      </Shell>
    </AuthGuard>
  );
}
