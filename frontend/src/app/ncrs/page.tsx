"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type NCR = { id:string; project_id:string; number:string; title:string; discipline:string; severity:string; status:string; due_date?:string|null; created_at:string };
type Project = { id:string; code:string; name:string };

export default function NCRRegisterPage(){
  const params=useSearchParams();
  const initialProject=params.get("project_id")||"";
  const [projects,setProjects]=useState<Project[]>([]);
  const [items,setItems]=useState<NCR[]>([]);
  const [projectId,setProjectId]=useState(initialProject);
  const [status,setStatus]=useState("");
  const [search,setSearch]=useState("");
  const [error,setError]=useState("");

  useEffect(()=>{api<Project[]>("/projects").then(setProjects).catch(e=>setError(e instanceof Error?e.message:"Failed to load projects"))},[]);
  useEffect(()=>{
    const qs=new URLSearchParams(); if(projectId)qs.set("project_id",projectId); if(status)qs.set("status",status);
    api<NCR[]>(`/ncrs${qs.toString()?`?${qs}`:""}`).then(setItems).catch(e=>setError(e instanceof Error?e.message:"Failed to load NCRs"));
  },[projectId,status]);

  const visible=useMemo(()=>items.filter(x=>`${x.number} ${x.title} ${x.discipline}`.toLowerCase().includes(search.toLowerCase())),[items,search]);
  const open=items.filter(x=>x.status!=="CLOSED").length;
  const critical=items.filter(x=>x.status!=="CLOSED"&&(x.severity==="HIGH"||x.severity==="CRITICAL")).length;
  const overdue=items.filter(x=>x.status!=="CLOSED"&&x.due_date&&new Date(`${x.due_date}T23:59:59`).getTime()<Date.now()).length;

  return <AuthGuard><Shell>
    <div className="page-head"><div><p className="eyebrow">Non-Conformance</p><h1>NCR Register</h1><p className="muted">Track non-conformance, corrective action, verification and closure.</p></div><Link className="btn-link" href={`/ncrs/new${projectId?`?project_id=${encodeURIComponent(projectId)}`:""}`}>+ New NCR</Link></div>
    {error?<div className="error">{error}</div>:null}
    <div className="grid inspection-metrics"><Metric label="Total NCR" value={items.length}/><Metric label="Open NCR" value={open}/><Metric label="High / Critical" value={critical}/><Metric label="Overdue" value={overdue}/></div>
    <div className="card section-card">
      <div className="filter-bar">
        <input className="search-input" placeholder="Search NCR number, title, discipline..." value={search} onChange={e=>setSearch(e.target.value)}/>
        <select value={projectId} onChange={e=>setProjectId(e.target.value)}><option value="">All projects</option>{projects.map(p=><option key={p.id} value={p.id}>{p.code} — {p.name}</option>)}</select>
        <select value={status} onChange={e=>setStatus(e.target.value)}><option value="">All status</option><option>OPEN</option><option>IN_PROGRESS</option><option>CLOSED</option></select>
      </div>
      {!visible.length?<div className="empty-state">No NCR records found.</div>:<div className="table-wrap"><table className="data-table"><thead><tr><th>NCR</th><th>Title</th><th>Discipline</th><th>Severity</th><th>Status</th><th>Due</th><th></th></tr></thead><tbody>{visible.map(x=><tr key={x.id}><td><strong>{x.number}</strong></td><td>{x.title}</td><td>{x.discipline}</td><td><span className={`severity severity-${x.severity.toLowerCase()}`}>{x.severity}</span></td><td><span className={`workflow workflow-${x.status.toLowerCase()}`}>{x.status.replace("_"," ")}</span></td><td>{x.due_date||"—"}</td><td><Link className="text-link" href={`/ncrs/${x.id}`}>View</Link></td></tr>)}</tbody></table></div>}
    </div>
  </Shell></AuthGuard>
}
function Metric({label,value}:{label:string;value:number}){return <div className="card"><div className="muted">{label}</div><div className="metric">{value}</div></div>}
