"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type Risk={id:string;project_id:string;title:string;category:string;probability:number;impact:number;score:number;mitigation?:string|null;owner_name?:string|null;status:string;due_date?:string|null;created_at:string;closed_at?:string|null};
type Project={id:string;code:string;name:string};

export default function RiskDetailPage(){
 const {id}=useParams<{id:string}>();const router=useRouter();const [item,setItem]=useState<Risk|null>(null);const [project,setProject]=useState<Project|null>(null);const [saving,setSaving]=useState(false);const [closing,setClosing]=useState(false);const [error,setError]=useState("");
 function load(){if(!id)return;setError("");api<Risk>(`/risks/${id}`).then(async r=>{setItem(r);const projects=await api<Project[]>("/projects");setProject(projects.find(p=>p.id===r.project_id)||null)}).catch(e=>setError(e instanceof Error?e.message:"Failed to load risk"))}
 useEffect(load,[id]);
 function setField(name:keyof Risk,value:string|number){setItem(p=>p?{...p,[name]:value}:p)}
 async function save(e?:FormEvent){e?.preventDefault();if(!item)return null;setSaving(true);setError("");try{const updated=await api<Risk>(`/risks/${id}`,{method:"PATCH",body:JSON.stringify({title:item.title,category:item.category,probability:Number(item.probability),impact:Number(item.impact),mitigation:item.mitigation||null,owner_name:item.owner_name||null,due_date:item.due_date||null,status:item.status})});setItem(updated);return updated}catch(e){setError(e instanceof Error?e.message:"Failed to update risk");return null}finally{setSaving(false)}}
 async function closeRisk(){if(!item||!item.mitigation?.trim()||!confirm("Close this risk? Latest changes will be saved first."))return;setClosing(true);setError("");try{const saved=await save();if(!saved)return;await api<Risk>(`/risks/${id}/close`,{method:"POST",body:JSON.stringify({comment:"Risk mitigation completed and verified"})});router.push(`/projects/${item.project_id}`)}catch(e){setError(e instanceof Error?e.message:"Failed to close risk")}finally{setClosing(false)}}
 if(!item)return <AuthGuard><Shell>{error?<div className="error">{error}</div>:<p className="muted">Loading risk...</p>}</Shell></AuthGuard>;
 const overdue=item.status!=="CLOSED"&&!!item.due_date&&new Date(`${item.due_date}T23:59:59`).getTime()<Date.now();const score=Number(item.probability)*Number(item.impact);const canClose=!!item.mitigation?.trim();
 return <AuthGuard><Shell>
  <div className="page-head"><div><p className="eyebrow">Project Assurance Risk</p><h1>{item.title}</h1><p className="muted">{project?`${project.code} · ${project.name}`:"Risk detail"}</p></div><div className="head-actions">{project?<Link className="secondary-btn" href={`/projects/${project.id}`}>Project Workspace</Link>:null}<Link className="secondary-btn" href={`/risks?project_id=${encodeURIComponent(item.project_id)}`}>← Risk Register</Link></div></div>
  {error?<div className="error">{error}</div>:null}
  <div className="grid inspection-summary"><div className="card"><div className="muted">Status</div><div className="metric metric-small"><span className={`workflow workflow-${item.status.toLowerCase()}`}>{item.status}</span></div></div><div className="card"><div className="muted">Risk Score</div><div className="metric"><span className={`risk-score risk-score-${score>=15?"high":score>=8?"medium":"low"}`}>{score}</span></div></div><div className="card"><div className="muted">Probability × Impact</div><div className="metric metric-small">{item.probability} × {item.impact}</div></div><div className="card"><div className="muted">Due Date</div><div className="metric metric-small">{item.due_date||"—"}{overdue?<span className="overdue-text"> Overdue</span>:null}</div></div></div>
  <form className="card form-card section-card" onSubmit={save}><div className="toolbar"><div><h2>Risk & Mitigation</h2><p className="muted small">Update scoring, ownership and mitigation before closure.</p></div></div><div className="form-grid">
   <label className="full-field"><span>Risk Title *</span><input disabled={item.status==="CLOSED"} required value={item.title} onChange={e=>setField("title",e.target.value)}/></label>
   <label><span>Category</span><select disabled={item.status==="CLOSED"} value={item.category} onChange={e=>setField("category",e.target.value)}><option>Quality</option><option>Technical</option><option>Schedule</option><option>Vendor</option><option>Construction</option><option>HSE</option><option>Commercial</option><option>Interface</option><option>Other</option></select></label>
   <label><span>Owner</span><input disabled={item.status==="CLOSED"} value={item.owner_name||""} onChange={e=>setField("owner_name",e.target.value)}/></label>
   <label><span>Probability (1–5)</span><input disabled={item.status==="CLOSED"} type="number" min="1" max="5" value={item.probability} onChange={e=>setField("probability",Number(e.target.value))}/></label>
   <label><span>Impact (1–5)</span><input disabled={item.status==="CLOSED"} type="number" min="1" max="5" value={item.impact} onChange={e=>setField("impact",Number(e.target.value))}/></label>
   <label><span>Status</span><select disabled={item.status==="CLOSED"} value={item.status} onChange={e=>setField("status",e.target.value)}><option>OPEN</option><option>MITIGATING</option></select></label>
   <label><span>Due Date</span><input disabled={item.status==="CLOSED"} type="date" value={item.due_date||""} onChange={e=>setField("due_date",e.target.value)}/></label>
   <label className="full-field"><span>Mitigation</span><textarea disabled={item.status==="CLOSED"} rows={7} value={item.mitigation||""} onChange={e=>setField("mitigation",e.target.value)} placeholder="Define mitigation and verification evidence..."/></label>
  </div>{item.status!=="CLOSED"?<><div className={canClose?"source-banner":"closure-note"}>{canClose?"Ready for closure. Close Risk will save the latest changes automatically.":"Mitigation is required before closure."}</div><div className="form-actions split-actions"><Link className="secondary-btn" href={`/risks?project_id=${encodeURIComponent(item.project_id)}`}>Back to Register</Link><div className="head-actions"><button type="button" className="secondary-btn" onClick={closeRisk} disabled={!canClose||closing||saving}>{closing?"Closing...":"Close Risk"}</button><button className="btn-action" disabled={saving||closing}>{saving?"Saving...":"Save Changes"}</button></div></div></>:<div className="source-banner">Risk closed {item.closed_at?new Date(item.closed_at).toLocaleString():""}</div>}</form>
 </Shell></AuthGuard>
}
