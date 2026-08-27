"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type Vendor={id:string;project_id:string;vendor_code:string;vendor_name:string;category:string;status:string;overall_score:number;ncr_count:number;updated_at:string};
type Project={id:string;code:string;name:string};

export default function VendorsPage(){
 const [items,setItems]=useState<Vendor[]>([]); const [projects,setProjects]=useState<Project[]>([]); const [projectId,setProjectId]=useState(""); const [status,setStatus]=useState(""); const [search,setSearch]=useState(""); const [error,setError]=useState("");
 useEffect(()=>{const q=new URLSearchParams(window.location.search);setProjectId(q.get("project_id")||"");api<Project[]>("/projects").then(setProjects).catch(()=>{})},[]);
 useEffect(()=>{const q=new URLSearchParams();if(projectId)q.set("project_id",projectId);if(status)q.set("status",status);api<Vendor[]>(`/vendors${q.toString()?`?${q}`:""}`).then(setItems).catch(e=>setError(e instanceof Error?e.message:"Failed to load vendors"))},[projectId,status]);
 const visible=useMemo(()=>items.filter(x=>`${x.vendor_code} ${x.vendor_name} ${x.category}`.toLowerCase().includes(search.toLowerCase())),[items,search]);
 const approved=items.filter(x=>x.status==="APPROVED").length, watch=items.filter(x=>x.status==="WATCHLIST").length, suspended=items.filter(x=>x.status==="SUSPENDED").length, low=items.filter(x=>x.overall_score<70).length;
 const selected=projects.find(p=>p.id===projectId);
 return <AuthGuard><Shell>
  <div className="page-head"><div><p className="eyebrow">Vendor Assurance</p><h1>Vendor Quality</h1><p className="muted">{selected?`${selected.code} · ${selected.name}`:"Monitor supplier quality performance and approval status."}</p></div><div className="head-actions">{selected?<Link className="secondary-btn" href={`/projects/${selected.id}`}>← Project Workspace</Link>:null}<Link className="btn-link" href={`/vendors/new${projectId?`?project_id=${encodeURIComponent(projectId)}`:""}`}>+ Add Vendor</Link></div></div>
  {error?<div className="error">{error}</div>:null}
  <div className="grid inspection-metrics"><Metric label="Approved" value={approved}/><Metric label="Watchlist" value={watch}/><Metric label="Suspended" value={suspended}/><Metric label="Score < 70" value={low}/></div>
  <div className="card section-card"><div className="filter-bar"><input className="search-input" placeholder="Search vendor code, name, category..." value={search} onChange={e=>setSearch(e.target.value)}/><select value={projectId} onChange={e=>setProjectId(e.target.value)}><option value="">All projects</option>{projects.map(p=><option key={p.id} value={p.id}>{p.code} — {p.name}</option>)}</select><select value={status} onChange={e=>setStatus(e.target.value)}><option value="">All status</option><option>APPROVED</option><option>WATCHLIST</option><option>SUSPENDED</option></select></div>
  {!visible.length?<div className="empty-state">No vendor quality records found.</div>:<div className="table-wrap"><table className="data-table"><thead><tr><th>Vendor</th><th>Category</th><th>Status</th><th>Score</th><th>NCR</th><th></th></tr></thead><tbody>{visible.map(v=><tr key={v.id}><td><strong>{v.vendor_code}</strong><div className="muted small">{v.vendor_name}</div></td><td>{v.category}</td><td><span className={`vendor-status vendor-${v.status.toLowerCase()}`}>{v.status}</span></td><td><span className={`risk-score ${v.overall_score>=85?"risk-score-low":v.overall_score>=70?"risk-score-medium":"risk-score-high"}`}>{v.overall_score.toFixed(1)}</span></td><td>{v.ncr_count}</td><td><Link className="text-link" href={`/vendors/${v.id}`}>View →</Link></td></tr>)}</tbody></table></div>}</div>
 </Shell></AuthGuard>
}
function Metric({label,value}:{label:string;value:number}){return <div className="card"><div className="muted">{label}</div><div className="metric">{value}</div></div>}
