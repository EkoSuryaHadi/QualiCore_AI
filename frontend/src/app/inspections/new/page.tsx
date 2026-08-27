"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type Project = { id: string; code: string; name: string };
type Inspection = { id: string };

export default function NewInspectionPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    project_id: "",
    discipline: "Mechanical",
    inspection_type: "",
    location: "",
    inspection_date: new Date().toISOString().slice(0, 10),
    result: "PASS",
    remarks: "",
  });

  useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    const projectId = query.get("project_id") || "";
    setForm((prev) => ({ ...prev, project_id: projectId }));
    api<Project[]>("/projects").then(setProjects).catch((err) => setError(err instanceof Error ? err.message : "Failed to load projects"));
  }, []);

  function setField(name: string, value: string) {
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      const created = await api<Inspection>("/inspections", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          location: form.location || null,
          remarks: form.remarks || null,
        }),
      });
      router.push(`/inspections/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create inspection");
    } finally {
      setSaving(false);
    }
  }

  const backHref = form.project_id ? `/inspections?project_id=${encodeURIComponent(form.project_id)}` : "/inspections";

  return (
    <AuthGuard>
      <Shell>
        <div className="page-head">
          <div>
            <p className="eyebrow">Inspection / ITP</p>
            <h1>New Inspection</h1>
            <p className="muted">Record inspection scope, result, location, and remarks.</p>
          </div>
          <Link className="text-link" href={backHref}>← Back to inspections</Link>
        </div>

        <form className="card form-card" onSubmit={submit}>
          {error ? <div className="error">{error}</div> : null}
          <div className="form-grid">
            <label><span>Project *</span><select required value={form.project_id} onChange={(e) => setField("project_id", e.target.value)}><option value="">Select project</option>{projects.map((p) => <option key={p.id} value={p.id}>{p.code} — {p.name}</option>)}</select></label>
            <label><span>Discipline *</span><select value={form.discipline} onChange={(e) => setField("discipline", e.target.value)}><option>Mechanical</option><option>Piping</option><option>Civil</option><option>Electrical</option><option>Instrumentation</option><option>Process</option><option>Structural</option><option>Coating</option><option>Welding</option><option>Other</option></select></label>
            <label><span>Inspection Type *</span><input required value={form.inspection_type} onChange={(e) => setField("inspection_type", e.target.value)} placeholder="e.g. Welding Visual Inspection" /></label>
            <label><span>Inspection Date *</span><input required type="date" value={form.inspection_date} onChange={(e) => setField("inspection_date", e.target.value)} /></label>
            <label><span>Location</span><input value={form.location} onChange={(e) => setField("location", e.target.value)} placeholder="Area / equipment / line" /></label>
            <label><span>Result *</span><select value={form.result} onChange={(e) => setField("result", e.target.value)}><option>PASS</option><option>FAIL</option><option>CONDITIONAL</option></select></label>
            <label className="full-field"><span>Remarks</span><textarea value={form.remarks} onChange={(e) => setField("remarks", e.target.value)} placeholder="Inspection findings, acceptance notes, pending actions..." rows={5} /></label>
          </div>
          <div className="form-actions">
            <Link className="secondary-btn" href={backHref}>Cancel</Link>
            <button className="btn-action" disabled={saving}>{saving ? "Saving..." : "Create Inspection"}</button>
          </div>
        </form>
      </Shell>
    </AuthGuard>
  );
}
