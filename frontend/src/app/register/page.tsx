"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

type RegisterResponse = { access_token: string };

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", organization_name: "", country: "Indonesia", job_title: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setLoading(true); setError("");
    try {
      const data = await api<RegisterResponse>("/identity/register", { method: "POST", body: JSON.stringify(form) });
      localStorage.setItem("qc_token", data.access_token);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally { setLoading(false); }
  }

  const set = (key: string, value: string) => setForm((old) => ({ ...old, [key]: value }));

  return <div className="login-wrap auth-page"><form className="login register-card" onSubmit={submit}>
    <div className="login-brand"><img src="/qualicore-logo.svg" alt="QualiCore AI" /></div>
    <div className="auth-heading"><h1>Create your workspace</h1><p className="muted">Start a new QualiCore organization. You will become the Organization Admin.</p></div>
    {error ? <div className="error">{error}</div> : null}
    <div className="auth-grid">
      <label>Full Name<input required value={form.full_name} onChange={(e) => set("full_name", e.target.value)} /></label>
      <label>Work Email<input required type="email" value={form.email} onChange={(e) => set("email", e.target.value)} /></label>
      <label>Company / Organization<input required value={form.organization_name} onChange={(e) => set("organization_name", e.target.value)} /></label>
      <label>Job Title<input value={form.job_title} onChange={(e) => set("job_title", e.target.value)} /></label>
      <label>Country<input value={form.country} onChange={(e) => set("country", e.target.value)} /></label>
      <label>Password<input required minLength={8} type="password" value={form.password} onChange={(e) => set("password", e.target.value)} /></label>
    </div>
    <button className="btn" disabled={loading}>{loading ? "Creating workspace..." : "Create Organization"}</button>
    <p className="auth-foot muted">Already have an account? <Link href="/login">Sign in</Link></p>
  </form></div>;
}
