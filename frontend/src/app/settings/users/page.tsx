"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type Project = { id: string; code: string; name: string };
type Member = { id: string; user_id: string; email: string; full_name: string; role: string; status: string; job_title?: string | null; project_ids: string[] };
type Invitation = { id: string; email: string; role: string; project_id?: string | null; token: string; accepted_at?: string | null; expires_at: string; created_at: string };
type Organization = { id: string; name: string; slug: string; country?: string | null };

const roles = ["ORGANIZATION_ADMIN","QA_MANAGER","QA_ENGINEER","PROJECT_MANAGER","DOCUMENT_CONTROLLER","VIEWER"];

export default function UsersSettingsPage() {
  const [org, setOrg] = useState<Organization | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("VIEWER");
  const [projectId, setProjectId] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true); setError("");
    try {
      const [organization, memberRows, inviteRows, projectRows] = await Promise.all([
        api<Organization>("/identity/organization"),
        api<Member[]>("/identity/members"),
        api<Invitation[]>("/identity/invitations"),
        api<Project[]>("/projects"),
      ]);
      setOrg(organization); setMembers(memberRows); setInvitations(inviteRows); setProjects(projectRows);
    } catch (err) { setError(err instanceof Error ? err.message : "Failed to load administration"); }
    finally { setLoading(false); }
  }

  useEffect(() => { void load(); }, []);

  async function invite(e: FormEvent) {
    e.preventDefault(); setError(""); setNotice("");
    try {
      await api("/identity/invitations", { method: "POST", body: JSON.stringify({ email, role, project_id: projectId || null }) });
      setEmail(""); setRole("VIEWER"); setProjectId(""); setNotice("Invitation created. Copy the invitation link below and send it to the user.");
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Could not create invitation"); }
  }

  async function changeRole(userId: string, nextRole: string) {
    try { await api(`/identity/members/${userId}/role`, { method: "PATCH", body: JSON.stringify({ role: nextRole }) }); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not change role"); }
  }

  async function toggleStatus(member: Member) {
    const next = member.status === "ACTIVE" ? "SUSPENDED" : "ACTIVE";
    try { await api(`/identity/members/${member.user_id}/status`, { method: "PATCH", body: JSON.stringify({ status: next }) }); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not update status"); }
  }

  async function assignProject(userId: string, nextProject: string) {
    if (!nextProject) return;
    try { await api(`/identity/members/${userId}/projects`, { method: "POST", body: JSON.stringify({ project_id: nextProject }) }); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not assign project"); }
  }

  async function removeProject(userId: string, pid: string) {
    try { await api(`/identity/members/${userId}/projects/${pid}`, { method: "DELETE" }); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not remove project"); }
  }

  async function copyInvite(token: string) {
    const url = `${window.location.origin}/join?token=${encodeURIComponent(token)}`;
    await navigator.clipboard.writeText(url);
    setNotice("Invitation link copied.");
  }

  const projectMap = useMemo(() => Object.fromEntries(projects.map((p) => [p.id, p])), [projects]);

  return <AuthGuard><Shell>
    <div className="page-head"><div><p className="eyebrow">Administration</p><h1>Users & Access</h1><p className="muted">Manage organization membership, roles, invitations and project access.</p></div>{org ? <div className="org-chip"><strong>{org.name}</strong><span>{org.country || org.slug}</span></div> : null}</div>
    {error ? <div className="error">{error}</div> : null}{notice ? <div className="source-banner">{notice}</div> : null}

    <div className="card section-card"><div className="toolbar"><div><h2>Invite User</h2><p className="muted small">New users join only through a secure invitation link.</p></div></div>
      <form className="invite-grid" onSubmit={invite}>
        <label>Email<input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="engineer@company.com" /></label>
        <label>Role<select value={role} onChange={(e) => setRole(e.target.value)}>{roles.map((r) => <option key={r}>{r}</option>)}</select></label>
        <label>Initial Project<select value={projectId} onChange={(e) => setProjectId(e.target.value)}><option value="">No project yet</option>{projects.map((p) => <option key={p.id} value={p.id}>{p.code} — {p.name}</option>)}</select></label>
        <button className="btn-action" type="submit">Create Invitation</button>
      </form>
    </div>

    <div className="card section-card"><div className="toolbar"><div><h2>Organization Members</h2><p className="muted small">{members.length} registered users</p></div></div>
      {loading ? <p className="muted">Loading users...</p> : <div className="table-wrap"><table className="data-table access-table"><thead><tr><th>User</th><th>Role</th><th>Status</th><th>Project Access</th><th>Assign Project</th><th>Action</th></tr></thead><tbody>
        {members.map((m) => <tr key={m.user_id}><td><strong>{m.full_name}</strong><div className="muted small">{m.email}</div>{m.job_title ? <div className="muted small">{m.job_title}</div> : null}</td>
          <td><select value={m.role} onChange={(e) => void changeRole(m.user_id, e.target.value)}>{roles.map((r) => <option key={r}>{r}</option>)}</select></td>
          <td><span className={`status ${m.status === "ACTIVE" ? "status-active" : "status-hold"}`}>{m.status}</span></td>
          <td><div className="access-projects">{m.project_ids.length ? m.project_ids.map((pid) => <button title="Remove project access" className="project-access-chip" key={pid} onClick={() => void removeProject(m.user_id, pid)}>{projectMap[pid]?.code || pid} ×</button>) : <span className="muted small">No explicit project assignment</span>}</div></td>
          <td><select defaultValue="" onChange={(e) => { void assignProject(m.user_id, e.target.value); e.currentTarget.value = ""; }}><option value="">Assign…</option>{projects.filter((p) => !m.project_ids.includes(p.id)).map((p) => <option key={p.id} value={p.id}>{p.code}</option>)}</select></td>
          <td><button className="secondary-btn" onClick={() => void toggleStatus(m)}>{m.status === "ACTIVE" ? "Suspend" : "Activate"}</button></td></tr>)}
      </tbody></table></div>}
    </div>

    <div className="card section-card"><div className="toolbar"><div><h2>Invitations</h2><p className="muted small">Pending and accepted invitation history.</p></div></div>
      {!invitations.length ? <div className="empty-state">No invitations yet.</div> : <div className="table-wrap"><table className="data-table"><thead><tr><th>Email</th><th>Role</th><th>Project</th><th>Status</th><th>Expires</th><th></th></tr></thead><tbody>{invitations.map((i) => <tr key={i.id}><td>{i.email}</td><td>{i.role}</td><td>{i.project_id ? projectMap[i.project_id]?.code || "Assigned" : "—"}</td><td>{i.accepted_at ? <span className="status status-active">ACCEPTED</span> : <span className="status status-hold">PENDING</span>}</td><td>{new Date(i.expires_at).toLocaleDateString()}</td><td>{!i.accepted_at ? <button className="secondary-btn" onClick={() => void copyInvite(i.token)}>Copy Invite Link</button> : null}</td></tr>)}</tbody></table></div>}
    </div>
  </Shell></AuthGuard>;
}
