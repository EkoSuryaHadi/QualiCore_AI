"use client";

import Link from "next/link";
import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
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
  closed_at?: string | null;
};
type Project = { id: string; code: string; name: string };
type Evidence = { id: string; file_name: string; content_type?: string | null; size_bytes: number; created_at: string };

export default function PunchDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [item, setItem] = useState<Punch | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [saving, setSaving] = useState(false);
  const [closing, setClosing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  function load() {
    if (!id) return;
    setError("");
    api<Punch>(`/punch/${id}`)
      .then(async (data) => {
        setItem(data);
        const [projects, files] = await Promise.all([
          api<Project[]>("/projects"),
          api<Evidence[]>(`/evidence/PUNCH/${id}`),
        ]);
        setProject(projects.find((p) => p.id === data.project_id) || null);
        setEvidence(files);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load punch item"));
  }

  useEffect(load, [id]);

  function setField(name: keyof Punch, value: string) {
    setItem((prev) => prev ? { ...prev, [name]: value } : prev);
  }

  async function save(e?: FormEvent) {
    e?.preventDefault();
    if (!item) return null;
    setSaving(true);
    setError("");
    try {
      const updated = await api<Punch>(`/punch/${id}`, {
        method: "PATCH",
        body: JSON.stringify({
          description: item.description,
          category: item.category,
          severity: item.severity,
          status: item.status,
          owner_name: item.owner_name || null,
          due_date: item.due_date || null,
        }),
      });
      setItem(updated);
      return updated;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update punch item");
      return null;
    } finally {
      setSaving(false);
    }
  }

  async function closePunch() {
    if (!item || !confirm("Close this punch item? The latest changes will be saved first.")) return;
    setClosing(true);
    setError("");
    try {
      const saved = await save();
      if (!saved) return;
      const closed = await api<Punch>(`/punch/${id}/close`, { method: "POST", body: JSON.stringify({}) });
      setItem(closed);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to close punch item");
    } finally {
      setClosing(false);
    }
  }

  async function remove() {
    if (!item || !confirm("Delete this punch item?")) return;
    setError("");
    try {
      await api<void>(`/punch/${id}`, { method: "DELETE" });
      router.push(`/punchlist?project_id=${encodeURIComponent(item.project_id)}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete punch item");
    }
  }

  async function upload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      const body = new FormData();
      body.append("file", file);
      await api<Evidence>(`/evidence/PUNCH/${id}`, { method: "POST", body });
      setEvidence(await api<Evidence[]>(`/evidence/PUNCH/${id}`));
      e.target.value = "";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload evidence");
    } finally {
      setUploading(false);
    }
  }

  const overdue = !!(item && item.status !== "CLOSED" && item.due_date && new Date(`${item.due_date}T23:59:59`).getTime() < Date.now());

  return (
    <AuthGuard>
      <Shell>
        <div className="page-head">
          <div>
            <p className="eyebrow">Completion Assurance</p>
            <h1>{item ? `Punch ${item.id.slice(0, 8)}` : "Punch Item"}</h1>
            <p className="muted">{item?.description || "Loading punch item..."}</p>
          </div>
          <div className="head-actions">
            {project ? <Link className="secondary-btn" href={`/projects/${project.id}`}>Project Workspace</Link> : null}
            <Link className="secondary-btn" href={`/punchlist${item ? `?project_id=${encodeURIComponent(item.project_id)}` : ""}`}>← Punch List Register</Link>
          </div>
        </div>

        {error ? <div className="error">{error}</div> : null}
        {!item ? <p className="muted">Loading punch item...</p> : (
          <>
            <div className="grid inspection-summary">
              <div className="card"><div className="muted">Status</div><div className="metric metric-small"><span className={`workflow workflow-${item.status.toLowerCase()}`}>{item.status.replace("_", " ")}</span></div></div>
              <div className="card"><div className="muted">Severity</div><div className="metric metric-small"><span className={`severity severity-${item.severity.toLowerCase()}`}>{item.severity}</span></div></div>
              <div className="card"><div className="muted">Due Date</div><div className="metric metric-small">{item.due_date || "—"}{overdue ? <span className="overdue-text"> Overdue</span> : null}</div></div>
              <div className="card"><div className="muted">Evidence</div><div className="metric">{evidence.length}</div></div>
            </div>

            <form className="card form-card section-card" onSubmit={save}>
              <div className="toolbar"><div><h2>Punch Item</h2><p className="muted small">Update responsibility, status and completion details.</p></div></div>
              <div className="form-grid">
                <label><span>Category</span><select disabled={item.status === "CLOSED"} value={item.category} onChange={(e) => setField("category", e.target.value)}><option>General</option><option>Mechanical</option><option>Piping</option><option>Civil</option><option>Electrical</option><option>Instrumentation</option><option>Structural</option><option>Coating</option><option>Housekeeping</option><option>Documentation</option><option>Other</option></select></label>
                <label><span>Severity</span><select disabled={item.status === "CLOSED"} value={item.severity} onChange={(e) => setField("severity", e.target.value)}><option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>CRITICAL</option></select></label>
                <label><span>Status</span><select disabled={item.status === "CLOSED"} value={item.status} onChange={(e) => setField("status", e.target.value)}><option>OPEN</option><option>IN_PROGRESS</option></select></label>
                <label><span>Owner / Responsible Person</span><input disabled={item.status === "CLOSED"} value={item.owner_name || ""} onChange={(e) => setField("owner_name", e.target.value)} /></label>
                <label><span>Due Date</span><input disabled={item.status === "CLOSED"} type="date" value={item.due_date || ""} onChange={(e) => setField("due_date", e.target.value)} /></label>
                <label className="full-field"><span>Description *</span><textarea disabled={item.status === "CLOSED"} rows={7} required value={item.description} onChange={(e) => setField("description", e.target.value)} /></label>
              </div>
              {item.status !== "CLOSED" ? (
                <div className="form-actions split-actions">
                  <button type="button" className="danger-btn" onClick={remove}>Delete Punch</button>
                  <div className="head-actions"><button type="button" className="secondary-btn" onClick={closePunch} disabled={closing || saving}>{closing ? "Closing..." : "Close Punch"}</button><button className="btn-action" disabled={saving || closing}>{saving ? "Saving..." : "Save Changes"}</button></div>
                </div>
              ) : <div className="source-banner">Punch item closed {item.closed_at ? new Date(item.closed_at).toLocaleString() : ""}</div>}
            </form>

            <div className="card section-card">
              <div className="toolbar">
                <div><h2>Evidence</h2><p className="muted small">Attach JPG, PNG, or PDF evidence up to 10 MB.</p></div>
                {item.status !== "CLOSED" ? <label className="secondary-btn upload-btn">{uploading ? "Uploading..." : "+ Upload Evidence"}<input type="file" accept="image/jpeg,image/png,application/pdf" disabled={uploading} onChange={upload} /></label> : null}
              </div>
              {!evidence.length ? <div className="empty-state">No punch evidence uploaded yet.</div> : <div className="evidence-list">{evidence.map((f) => <div key={f.id} className="evidence-row"><div><strong>{f.file_name}</strong><div className="muted small">{f.content_type || "file"} · {(f.size_bytes / 1024).toFixed(1)} KB</div></div><span className="muted small">{new Date(f.created_at).toLocaleString()}</span></div>)}</div>}
            </div>
          </>
        )}
      </Shell>
    </AuthGuard>
  );
}
