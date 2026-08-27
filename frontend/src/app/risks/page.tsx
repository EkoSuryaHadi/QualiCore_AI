"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type Risk={id:string;project_id:string;title:string;category:string;probability:number;impact:number;score:number;mitigation?:string|null;owner_name?:string|null;status:string;due_date?:string|null;created_at:string;closed_at?:string|null};
type Project={id:string;code:string;name:string};

export default function RiskRegisterPage(){
 const [projects,setProjects]=useState<Project[]>([]);const [items,setItems]=useState<Risk[]>([]);const [projectId,setProjectId]=useState("");const [status,setStatus]=useState("");const [search,setSearch]=useState("");const [error,setError]=useState("");const [loading,setLoading]=useState(true);
 useEffect(()=>{const q=new URLSearchParams(window.location.search);setProjectId(q.get("project_id")||"");api<Project[]>("/projects").then(setProjects).catch(()=>{})},[]);
 useEffect(()=>{setLoading(true);const q=new URLSearchParams();if(projectId)q.set("project_id",projectId);if(status)q.set("status",status);api<Risk[]>(`/risks${q.toString()?`?${q}`:""}`).then(setItems).catch(e=>setError(e instanceof Error?e.message:"Failed to load risks")).finally(()=>setLoading(false))},[projectId,status]);
 const visible=useMemo(()=>items.filter(x=>`${x.title} ${x.category} ${x.owner_name||""} ${x.mitigation||""}`.toLowerCase().includes(search.toLowerCase())),[items,search]);
 const high=items.filter(x=>x.status!=="CLOSED"&&x.score>=15).length;const mitigating=items.filter(x=>x.status==="MITIGATING").length;const overdue=items.filter(x=>x.status!=="CLOSED"&&x.due_date&&new Date(`${x.due_date}T23:59:59`).getTime()<Date.now()).length;const selectedProject=projects.find(p=>p.id===projectId);
 return <AuthGuard><Shell>
  <div className="page-head"><div><p className="eyebrow">Project Assurance Risk</p><h1>Risk Register</h1><p className="muted">{selectedProject?`${selectedProject.code} · ${selectedProject.name}`:"Identify, score, mitigate and close project assurance risks."}</p></div><div className="head-actions">{selectedProject?<Link className="secondary-btn" href={`/projects/${selectedProject.id}`}>← Project Workspace</Link>:null}<Link className="btn-link" href={`/risks/new${projectId?`?project_id=${encodeURIComponent(projectId)}`:""}`}>+ New Risk</Link></div></div>
  <div className="grid inspection-metrics"><Metric label="Open Risks" value={items.filter(x=>x.status!=="CLOSED").length}/><Metric label="High Risks" value={high}/><Metric label="Mitigating" value={mitigating}/><Metric label="Overdue" value={overdue}/></div>
  <div className="card section-card"><div className="filter-bar"><input className="search-input" placeholder="Search title, category, owner, mitigation..." value={search} onChange={e=>setSearch(e.target.value)}/><select value={projectId} onChange={e=>setProjectId(e.target.value)}><option value="">All projects</option>{projects.map(p=><option key={p.id} value={p.id}>{p.code} — {p.name}</option>)}</select><select value={status} onChange={e=>setStatus(e.target.value)}><option value="">All status</option><option>OPEN</option><option>MITIGATING</option><option>CLOSED</option></select></div>
   {error?<div className="error">{error}</div>:null}{loading?<p className="muted">Loading risks...</p>:null}{!loading&&!visible.length?<div className="empty-state">No risks found.</div>:null}
   {!loading&&visible.length?<div className="table-wrap"><table className="data-table"><thead><tr><th>Risk</th><th>Category</th><th>P</th><th>I</th><th>Score</th><th>Status</th><th>Owner</th><th>Due</th><th></th></tr></thead><tbody>{visible.map(x=><tr key={x.id}><td><strong>{x.title}</strong></td><td>{x.category}</td><td>{x.probability}</td><td>{x.impact}</td><td><span className={`risk-score risk-score-${level(x.score)}`}>{x.score}</span></td><td><span className={`workflow workflow-${x.status.toLowerCase()}`}>{x.status}</span></td><td>{x.owner_name||"—"}</td><td>{x.due_date||"—"}</td><td><Link className="text-link" href={`/risks/${x.id}`}>View →</Link></td></tr>)}</tbody></table></div>:null}
  </div>
 </Shell></AuthGuard>
}
function Metric({label,value}:{label:string;value:number}){return <div className="card"><div className="muted">{label}</div><div className="metric">{value}</div></div>}
function level(score:number){return score>=15?"high":score>=8?"medium":"low"}
