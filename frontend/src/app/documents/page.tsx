"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type DocumentItem={id:string;project_id:string;document_no:string;title:string;discipline:string;revision:string;status:string;owner_name?:string|null;due_date?:string|null;updated_at:string};
type Project={id:string;code:string;name:string};

export default function DocumentsPage(){
 const [items,setItems]=useState<DocumentItem[]>([]); const [projects,setProjects]=useState<Project[]>([]); const [projectId,setProjectId]=useState(""); const [status,setStatus]=useState(""); const [search,setSearch]=useState(""); const [loading,setLoading]=useState(true); const [error,setError]=useState("");
 useEffect(()=>{const q=new URLSearchParams(window.location.search);setProjectId(q.get("project_id")||"");api<Project[]>("/projects").then(setProjects).catch(()=>{})},[]);
 useEffect(()=>{setLoading(true);const q=new URLSearchParams();if(projectId)q.set("project_id",projectId);if(status)q.set("status",status);api<DocumentItem[]>(`/documents${q.toString()?`?${q}`:""}`).then(setItems).catch(e=>setError(e instanceof Error?e.message:"Failed to load documents")).finally(()=>setLoading(false))},[projectId,status]);
 const visible=useMemo(()=>items.filter(x=>`${x.document_no} ${x.title} ${x.discipline} ${x.owner_name||""}`.toLowerCase().includes(search.toLowerCase())),[items,search]);
 const selected=projects.find(p=>p.id===projectId); const draft=items.filter(x=>x.status==="DRAFT").length; const review=items.filter(x=>x.status==="IN_REVIEW").length; const approved=items.filter(x=>x.status==="APPROVED").length; const overdue=items.filter(x=>x.status!=="APPROVED"&&x.due_date&&new Date(`${x.due_date}T23:59:59`).getTime()<Date.now()).length;
 return <AuthGuard><Shell>
  <div className="page-head"><div><p className="eyebrow">Document Control</p><h1>Document Register</h1><p className="muted">{selected?`${selected.code} · ${selected.name}`:"Manage revisions, review and approval status."}</p></div><div className="head-actions">{selected?<Link className="secondary-btn" href={`/projects/${selected.id}`}>← Project Workspace</Link>:null}<Link className="btn-link" href={`/documents/new${projectId?`?project_id=${encodeURIComponent(projectId)}`:""}`}>+ New Document</Link></div></div>
  <div className="grid inspection-metrics"><Metric label="Draft" value={draft}/><Metric label="In Review" value={review}/><Metric label="Approved" value={approved}/><Metric label="Overdue" value={overdue}/></div>
  <div className="card section-card"><div className="filter-bar"><input className="search-input" value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search document no, title, discipline..."/><select value={projectId} onChange={e=>setProjectId(e.target.value)}><option value="">All projects</option>{projects.map(p=><option key={p.id} value={p.id}>{p.code} — {p.name}</option>)}</select><select value={status} onChange={e=>setStatus(e.target.value)}><option value="">All status</option><option>DRAFT</option><option>IN_REVIEW</option><option>APPROVED</option><option>REJECTED</option></select></div>{error?<div className="error">{error}</div>:null}{loading?<p className="muted">Loading documents...</p>:null}{!loading&&!visible.length?<div className="empty-state">No documents found.</div>:null}{!loading&&visible.length?<div className="table-wrap"><table className="data-table"><thead><tr><th>Document No</th><th>Title</th><th>Discipline</th><th>Rev</th><th>Status</th><th>Owner</th><th>Due</th><th></th></tr></thead><tbody>{visible.map(x=><tr key={x.id}><td><strong>{x.document_no}</strong></td><td>{x.title}</td><td>{x.discipline}</td><td>{x.revision}</td><td><span className={`workflow workflow-${x.status.toLowerCase()}`}>{x.status.replace("_"," ")}</span></td><td>{x.owner_name||"—"}</td><td>{x.due_date||"—"}</td><td><Link className="text-link" href={`/documents/${x.id}`}>View →</Link></td></tr>)}</tbody></table></div>:null}</div>
 </Shell></AuthGuard>
}
function Metric({label,value}:{label:string;value:number}){return <div className="card"><div className="muted">{label}</div><div className="metric">{value}</div></div>}
