"use client";

import Link from "next/link";
import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
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
  created_by: string;
  created_at: string;
};

type Project = { id: string; code: string; name: string };
type Evidence = { id: string; file_name: string; content_type?: string | null; size_bytes: number; created_at: string };

export default function InspectionDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const router = useRouter();
  const [item, setItem] = useState<Inspection | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  function load() {
    if (!id) return;
    setError("");
    api<Inspection>(`/inspections/${id}`)
      .then(async (data) => {
        setItem(data);
        const [projects, files] = await Promise.all([
          api<Project[]>("/projects"),
          api<Evidence[]>(`/evidence/INSPECTION/${id}`),
        ]);
        setProject(projects.find((p) => p.id === data.project_id) || null);
        setEvidence(files);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load inspection"));
  }

  useEffect(load, [id]);

  function setField(name: keyof Inspection, value: string) {
    setItem((prev) => prev ? { ...prev, [name]: value } : prev);
  }

  async function save(e: FormEvent) {
    e.preventDefault();
    if (!item) return;
    setSaving(true);
    setError("");
    try {
      const updated = await api<Inspection>(`/inspections/${id}`, {
        method: "PATCH",
        body: JSON.stringify({
          discipline: item.discipline,
          inspection_type: item.inspection_type,
          location: item.location || null,
          inspection_date: item.inspection_date,
          result: item.result,
          remarks: item.remarks || null,
        }),
      });
      setItem(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update inspection");
    } finally {
      setSaving(false);
    }
  }

  async function remove() {
    if (!item || !confirm("Delete this inspection record?")) return;
    setError("");
    try {
      await api<void>(`/inspections/${id}`, { method: "DELETE" });
      router.push(`/inspections?project_id=${encodeURIComponent(item.project_id)}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete inspection");
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
      await api<Evidence>(`/evidence/INSPECTION/${id}`, { method: "POST", body });
      const files = await api<Evidence[]>(`/evidence/INSPECTION/${id}`);
      setEvidence(files);
      e.target.value = "";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload evidence");
    } finally {
      setUploading(false);
    }
  }

  const backHref = item ? `/inspections?project_id=${encodeURIComponent(item.project_id)}` : "/inspections";

  return (
    <AuthGuard>
      <Shell>
        <div className="page-head">
          <div>
            <p className="eyebrow">Inspection / ITP</p>
            <h1>{item?.inspection_type || "Inspection Detail"}</h1>
            <p className="muted">{project ? `${project.code} · ${project.name}` : "Inspection record"}</p>
          </div>
          <div className="head-actions">
            {project ? <Link className="secondary-btn" href={`/projects/${project.id}`}>Project Workspace</Link> : null}
            <Link className="secondary-btn" href={backHref}>← Inspection Register</Link>
          </div>
        </div>

        {error ? <div className="error">{error}</div> : null}
        {!item ? <p className="muted">Loading inspection...</p> : (
          <>
            <div className="grid inspection-summary">
              <div className="card"><div className="muted">Result</div><div className="metric metric-small"><span className={`result result-${item.result.toLowerCase()}`}>{item.result}</span></div></div>
              <div className="card"><div className="muted">Discipline</div><div className="metric metric-small">{item.discipline}</div></div>
              <div className="card"><div className="muted">Date</div><div className="metric metric-small">{item.inspection_date}</div></div>
              <div className="card"><div className="muted">Evidence</div><div className="metric">{evidence.length}</div></div>
            </div>

            <form className="card form-card section-card" onSubmit={save}>
              <div className="toolbar"><div><h2>Inspection Record</h2><p className="muted small">Update the inspection result and field notes.</p></div></div>
              <div className="form-grid">
                <label><span>Inspection Type *</span><input required value={item.inspection_type} onChange={(e) => setField("inspection_type", e.target.value)} /></label>
                <label><span>Discipline *</span><select value={item.discipline} onChange={(e) => setField("discipline", e.target.value)}><option>Mechanical</option><option>Piping</option><option>Civil</option><option>Electrical</option><option>Instrumentation</option><option>Process</option><option>Structural</option><option>Coating</option><option>Welding</option><option>Other</option></select></label>
                <label><span>Inspection Date *</span><input type="date" required value={item.inspection_date} onChange={(e) => setField("inspection_date", e.target.value)} /></label>
                <label><span>Location</span><input value={item.location || ""} onChange={(e) => setField("location", e.target.value)} /></label>
                <label><span>Result *</span><select value={item.result} onChange={(e) => setField("result", e.target.value)}><option>PASS</option><option>FAIL</option><option>CONDITIONAL</option></select></label>
                <label className="full-field"><span>Remarks</span><textarea rows={5} value={item.remarks || ""} onChange={(e) => setField("remarks", e.target.value)} /></label>
              </div>
              <div className="form-actions split-actions">
                <button type="button" className="danger-btn" onClick={remove}>Delete Inspection</button>
                <button className="btn-action" disabled={saving}>{saving ? "Saving..." : "Save Changes"}</button>
              </div>
            </form>

            <div className="card section-card">
              <div className="toolbar">
                <div><h2>Evidence</h2><p className="muted small">Attach JPG, PNG, or PDF evidence up to 10 MB.</p></div>
                <label className="secondary-btn upload-btn">{uploading ? "Uploading..." : "+ Upload Evidence"}<input type="file" accept="image/jpeg,image/png,application/pdf" disabled={uploading} onChange={upload} /></label>
              </div>
              {!evidence.length ? <div className="empty-state">No evidence uploaded yet.</div> : (
                <div className="evidence-list">
                  {evidence.map((file) => <div key={file.id} className="evidence-row"><div><strong>{file.file_name}</strong><div className="muted small">{file.content_type || "file"} · {(file.size_bytes / 1024).toFixed(1)} KB</div></div><span className="muted small">{new Date(file.created_at).toLocaleString()}</span></div>)}
                </div>
              )}
            </div>
          </>
        )}
      </Shell>
    </AuthGuard>
  );
}
