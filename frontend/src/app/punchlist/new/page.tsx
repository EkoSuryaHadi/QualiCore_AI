"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type Project = { id: string; code: string; name: string };
type Punch = { id: string; project_id: string };

export default function NewPunchPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    project_id: "",
    description: "",
    category: "General",
    severity: "MEDIUM",
    owner_name: "",
    due_date: "",
  });

  useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    const projectId = query.get("project_id") || "";
    setForm((prev) => ({ ...prev, project_id: projectId }));
    api<Project[]>("/projects").then(setProjects).catch(() => {});
  }, []);

  function setField(name: string, value: string) {
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const created = await api<Punch>("/punch", {
        method: "POST",
        body: JSON.stringify({
          project_id: form.project_id,
          description: form.description,
          category: form.category || "General",
          severity: form.severity,
          owner_name: form.owner_name || null,
          due_date: form.due_date || null,
        }),
      });
      router.push(`/punchlist/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create punch item");
    } finally {
      setSaving(false);
    }
  }

  return (
    <AuthGuard>
      <Shell>
        <div className="page-head">
          <div>
            <p className="eyebrow">Completion Assurance</p>
            <h1>Create Punch Item</h1>
            <p className="muted">Record an outstanding completion item and assign responsibility.</p>
          </div>
          <Link className="text-link" href={`/punchlist${form.project_id ? `?project_id=${encodeURIComponent(form.project_id)}` : ""}`}>← Punch List Register</Link>
        </div>

        <form className="card form-card" onSubmit={submit}>
          {error ? <div className="error">{error}</div> : null}
          <div className="form-grid">
            <label><span>Project *</span><select required value={form.project_id} onChange={(e) => setField("project_id", e.target.value)}><option value="">Select project</option>{projects.map((p) => <option key={p.id} value={p.id}>{p.code} — {p.name}</option>)}</select></label>
            <label><span>Category *</span><select value={form.category} onChange={(e) => setField("category", e.target.value)}><option>General</option><option>Mechanical</option><option>Piping</option><option>Civil</option><option>Electrical</option><option>Instrumentation</option><option>Structural</option><option>Coating</option><option>Housekeeping</option><option>Documentation</option><option>Other</option></select></label>
            <label><span>Severity *</span><select value={form.severity} onChange={(e) => setField("severity", e.target.value)}><option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>CRITICAL</option></select></label>
            <label><span>Owner / Responsible Person</span><input value={form.owner_name} onChange={(e) => setField("owner_name", e.target.value)} placeholder="Name / company / discipline" /></label>
            <label><span>Due Date</span><input type="date" value={form.due_date} onChange={(e) => setField("due_date", e.target.value)} /></label>
            <label className="full-field"><span>Description *</span><textarea rows={6} required value={form.description} onChange={(e) => setField("description", e.target.value)} placeholder="Describe the outstanding item and required completion..." /></label>
          </div>
          <div className="form-actions">
            <Link className="secondary-btn" href="/punchlist">Cancel</Link>
            <button className="btn-action" disabled={saving}>{saving ? "Creating..." : "Create Punch Item"}</button>
          </div>
        </form>
      </Shell>
    </AuthGuard>
  );
}
