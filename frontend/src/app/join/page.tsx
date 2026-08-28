"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

type AcceptResponse = { access_token: string };

export default function JoinPage() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [fullName, setFullName] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => { setToken(new URLSearchParams(window.location.search).get("token") || ""); }, []);

  async function submit(e: FormEvent) {
    e.preventDefault(); setLoading(true); setError("");
    try {
      const data = await api<AcceptResponse>("/identity/invitations/accept", { method: "POST", body: JSON.stringify({ token, full_name: fullName, password, job_title: jobTitle || null }) });
      localStorage.setItem("qc_token", data.access_token);
      router.push("/");
    } catch (err) { setError(err instanceof Error ? err.message : "Could not accept invitation"); }
    finally { setLoading(false); }
  }

  return <div className="login-wrap auth-page"><form className="login" onSubmit={submit}>
    <div className="login-brand"><img src="/qualicore-logo.svg" alt="QualiCore AI" /></div>
    <div className="auth-heading"><h1>Join your organization</h1><p className="muted">Complete your account to accept the QualiCore invitation.</p></div>
    {error ? <div className="error">{error}</div> : null}
    {!token ? <div className="error">Invitation token is missing.</div> : null}
    <label>Full Name<input required value={fullName} onChange={(e) => setFullName(e.target.value)} /></label>
    <label>Job Title<input value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} /></label>
    <label>Password<input required minLength={8} type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></label>
    <button className="btn" disabled={loading || !token}>{loading ? "Joining..." : "Accept Invitation"}</button>
  </form></div>;
}
