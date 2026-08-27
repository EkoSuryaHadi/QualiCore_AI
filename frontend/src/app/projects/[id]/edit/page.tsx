"use client";

import { FormEvent, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
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
  status: "ACTIVE" | "HOLD" | "COMPLETED";
  progress: number;
};

export default function EditProjectPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    name: "",
    client_name: "",
    location: "",
    start_date: "",
    finish_date: "",
    status: "ACTIVE",
    progress: 0,
  });
  const [code, setCode] = useState("");

  useEffect(() => {
    if (!id) return;
    api<Project>(`/projects/${id}`)
      .then((p) => {
        setCode(p.code);
        setForm({
          name: p.name,
          client_name: p.client_name || "",
          location: p.location || "",
          start_date: p.start_date || "",
          finish_date: p.finish_date || "",
          status: p.status,
          progress: Number(p.progress || 0),
        });
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load project"))
      .finally(() => setLoading(false));
  }, [id]);

  function setField(name: string, value: string | number) {
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await api<Project>(`/projects/${id}`, {
        method: "PATCH",
        body: JSON.stringify({
          ...form,
          client_name: form.client_name || null,
          location: form.location || null,
          start_date: form.start_date || null,
          finish_date: form.finish_date || null,
          progress: Number(form.progress),
        }),
      });
      router.push(`/projects/${id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update project");
    } finally {
      setSaving(false);
    }
  }

  return (
    <AuthGuard>
      <Shell>
        {loading ? <p className="muted">Loading project...</p> : null}
        {!loading ? (
          <>
            <div className="page-head">
              <div>
                <p className="eyebrow">{code || "Project"}</p>
                <h1>Edit Project</h1>
                <p className="muted">Update the project master and delivery status.</p>
              </div>
              <Link className="text-link" href={`/projects/${id}`}>← Back to workspace</Link>
            </div>

            <form className="card form-card" onSubmit={submit}>
              {error ? <div className="error">{error}</div> : null}
              <div className="form-grid">
                <label><span>Project Code</span><input value={code} disabled /></label>
                <label><span>Project Name *</span><input required value={form.name} onChange={(e) => setField("name", e.target.value)} /></label>
                <label><span>Client</span><input value={form.client_name} onChange={(e) => setField("client_name", e.target.value)} /></label>
                <label><span>Location</span><input value={form.location} onChange={(e) => setField("location", e.target.value)} /></label>
                <label><span>Start Date</span><input type="date" value={form.start_date} onChange={(e) => setField("start_date", e.target.value)} /></label>
                <label><span>Finish Date</span><input type="date" value={form.finish_date} onChange={(e) => setField("finish_date", e.target.value)} /></label>
                <label><span>Status</span><select value={form.status} onChange={(e) => setField("status", e.target.value)}><option>ACTIVE</option><option>HOLD</option><option>COMPLETED</option></select></label>
                <label><span>Progress (%)</span><input type="number" min="0" max="100" value={form.progress} onChange={(e) => setField("progress", Number(e.target.value))} /></label>
              </div>
              <div className="form-actions">
                <Link className="secondary-btn" href={`/projects/${id}`}>Cancel</Link>
                <button className="btn-action" disabled={saving}>{saving ? "Saving..." : "Save Changes"}</button>
              </div>
            </form>
          </>
        ) : null}
      </Shell>
    </AuthGuard>
  );
}
