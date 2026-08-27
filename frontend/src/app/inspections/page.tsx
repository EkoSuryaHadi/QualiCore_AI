"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type Inspection = {
  id: string;
  project_id: string;
  discipline: string;
  inspection_type: string;
  location?: string | null;
  inspection_date: string;
  result: "PASS" | "FAIL" | "CONDITIONAL";
  remarks?: string | null;
};

type Project = { id: string; code: string; name: string };

export default function InspectionsPage() {
  const [items, setItems] = useState<Inspection[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [result, setResult] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    setProjectId(query.get("project_id") || "");
    api<Project[]>("/projects").then(setProjects).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    setError("");
    const params = new URLSearchParams();
    if (projectId) params.set("project_id", projectId);
    if (result) params.set("result", result);
    const suffix = params.toString() ? `?${params.toString()}` : "";
    api<Inspection[]>(`/inspections${suffix}`)
      .then(setItems)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load inspections"))
      .finally(() => setLoading(false));
  }, [projectId, result]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return items;
    return items.filter((item) =>
      [item.discipline, item.inspection_type, item.location || "", item.remarks || ""]
        .join(" ")
        .toLowerCase()
        .includes(q)
    );
  }, [items, search]);

  const pass = items.filter((x) => x.result === "PASS").length;
  const fail = items.filter((x) => x.result === "FAIL").length;
  const conditional = items.filter((x) => x.result === "CONDITIONAL").length;
  const selectedProject = projects.find((p) => p.id === projectId);
  const newHref = projectId ? `/inspections/new?project_id=${encodeURIComponent(projectId)}` : "/inspections/new";

  return (
    <AuthGuard>
      <Shell>
        <div className="page-head">
          <div>
            <p className="eyebrow">Inspection / ITP</p>
            <h1>Inspection Register</h1>
            <p className="muted">{selectedProject ? `${selectedProject.code} · ${selectedProject.name}` : "Manage project quality inspection records."}</p>
          </div>
          <div className="head-actions">
            {selectedProject ? <Link className="secondary-btn" href={`/projects/${selectedProject.id}`}>← Project Workspace</Link> : null}
            <Link className="btn-link" href={newHref}>+ New Inspection</Link>
          </div>
        </div>

        <div className="grid inspection-metrics">
          <Metric label="Total" value={items.length} />
          <Metric label="Pass" value={pass} />
          <Metric label="Fail" value={fail} />
          <Metric label="Conditional" value={conditional} />
        </div>

        <div className="card section-card">
          <div className="filter-bar">
            <input className="search-input" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search inspection type, discipline, location..." />
            <select value={projectId} onChange={(e) => setProjectId(e.target.value)}>
              <option value="">All projects</option>
              {projects.map((project) => <option key={project.id} value={project.id}>{project.code} — {project.name}</option>)}
            </select>
            <select value={result} onChange={(e) => setResult(e.target.value)}>
              <option value="">All results</option>
              <option value="PASS">PASS</option>
              <option value="FAIL">FAIL</option>
              <option value="CONDITIONAL">CONDITIONAL</option>
            </select>
          </div>

          {error ? <div className="error">{error}</div> : null}
          {loading ? <p className="muted">Loading inspections...</p> : null}
          {!loading && !filtered.length ? <div className="empty-state">No inspection records found.</div> : null}
          {!loading && filtered.length ? (
            <div className="table-wrap">
              <table className="data-table">
                <thead><tr><th>Date</th><th>Inspection Type</th><th>Discipline</th><th>Location</th><th>Result</th><th></th></tr></thead>
                <tbody>
                  {filtered.map((item) => (
                    <tr key={item.id}>
                      <td>{item.inspection_date}</td>
                      <td><strong>{item.inspection_type}</strong></td>
                      <td>{item.discipline}</td>
                      <td>{item.location || "—"}</td>
                      <td><span className={`result result-${item.result.toLowerCase()}`}>{item.result}</span></td>
                      <td><Link className="text-link" href={`/inspections/${item.id}`}>View →</Link></td>
                    </tr>
                  ))}
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
