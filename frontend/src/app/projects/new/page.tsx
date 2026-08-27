"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type Project = { id: string };

export default function NewProjectPage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    code: "",
    name: "",
    client_name: "",
    location: "",
    start_date: "",
    finish_date: "",
    status: "ACTIVE",
    progress: 0,
  });

  function setField(name: string, value: string | number) {
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      const payload = {
        ...form,
        client_name: form.client_name || null,
        location: form.location || null,
        start_date: form.start_date || null,
        finish_date: form.finish_date || null,
        progress: Number(form.progress),
      };
      const created = await api<Project>("/projects", { method: "POST", body: JSON.stringify(payload) });
      router.push(`/projects/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    } finally {
      setSaving(false);
    }
  }

  return (
    <AuthGuard>
      <Shell>
        <div className="page-head">
          <div>
            <p className="eyebrow">Project Management</p>
            <h1>Create Project</h1>
            <p className="muted">Create the project master before adding assurance records.</p>
          </div>
          <Link className="text-link" href="/projects">← Back to projects</Link>
        </div>

        <form className="card form-card" onSubmit={submit}>
          {error ? <div className="error">{error}</div> : null}
          <div className="form-grid">
            <label><span>Project Code *</span><input required value={form.code} onChange={(e) => setField("code", e.target.value)} placeholder="EPC-001" /></label>
            <label><span>Project Name *</span><input required value={form.name} onChange={(e) => setField("name", e.target.value)} placeholder="Project name" /></label>
            <label><span>Client</span><input value={form.client_name} onChange={(e) => setField("client_name", e.target.value)} placeholder="Client / Owner" /></label>
            <label><span>Location</span><input value={form.location} onChange={(e) => setField("location", e.target.value)} placeholder="Project location" /></label>
            <label><span>Start Date</span><input type="date" value={form.start_date} onChange={(e) => setField("start_date", e.target.value)} /></label>
            <label><span>Finish Date</span><input type="date" value={form.finish_date} onChange={(e) => setField("finish_date", e.target.value)} /></label>
            <label><span>Status</span><select value={form.status} onChange={(e) => setField("status", e.target.value)}><option>ACTIVE</option><option>HOLD</option><option>COMPLETED</option></select></label>
            <label><span>Progress (%)</span><input type="number" min="0" max="100" value={form.progress} onChange={(e) => setField("progress", Number(e.target.value))} /></label>
          </div>
          <div className="form-actions">
            <Link className="secondary-btn" href="/projects">Cancel</Link>
            <button className="btn-action" disabled={saving}>{saving ? "Creating..." : "Create Project"}</button>
          </div>
        </form>
      </Shell>
    </AuthGuard>
  );
}
