"use client";

import Link from "next/link";
import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type NCR={id:string;project_id:string;number:string;title:string;description:string;discipline:string;severity:string;status:string;root_cause?:string|null;corrective_action?:string|null;due_date?:string|null;created_at:string;closed_at?:string|null};
type Project={id:string;code:string;name:string};
type Evidence={id:string;file_name:string;content_type?:string|null;size_bytes:number;created_at:string};

export default function NCRDetailPage(){
 const {id}=useParams<{id:string}>(); const [item,setItem]=useState<NCR|null>(null); const [project,setProject]=useState<Project|null>(null); const [evidence,setEvidence]=useState<Evidence[]>([]); const [saving,setSaving]=useState(false); const [closing,setClosing]=useState(false); const [uploading,setUploading]=useState(false); const [error,setError]=useState("");
 function load(){if(!id)return;setError("");api<NCR>(`/ncrs/${id}`).then(async n=>{setItem(n);const [projects,files]=await Promise.all([api<Project[]>("/projects"),api<Evidence[]>(`/evidence/NCR/${id}`)]);setProject(projects.find(p=>p.id===n.project_id)||null);setEvidence(files)}).catch(e=>setError(e instanceof Error?e.message:"Failed to load NCR"))}
 useEffect(load,[id]);
 function setField(name:keyof NCR,value:string){setItem(p=>p?{...p,[name]:value}:p)}
 async function save(e:FormEvent){e.preventDefault();if(!item)return;setSaving(true);setError("");try{const updated=await api<NCR>(`/ncrs/${id}`,{method:"PATCH",body:JSON.stringify({title:item.title,description:item.description,severity:item.severity,root_cause:item.root_cause||null,corrective_action:item.corrective_action||null,due_date:item.due_date||null})});setItem(updated)}catch(e){setError(e instanceof Error?e.message:"Failed to update NCR")}finally{setSaving(false)}}
 async function closeNCR(){if(!item||!confirm("Close this NCR? Root cause and corrective action must be complete."))return;setClosing(true);setError("");try{const closed=await api<NCR>(`/ncrs/${id}/close`,{method:"POST",body:JSON.stringify({})});setItem(closed)}catch(e){setError(e instanceof Error?e.message:"Failed to close NCR")}finally{setClosing(false)}}
 async function upload(e:ChangeEvent<HTMLInputElement>){const file=e.target.files?.[0];if(!file)return;setUploading(true);setError("");try{const body=new FormData();body.append("file",file);await api<Evidence>(`/evidence/NCR/${id}`,{method:"POST",body});setEvidence(await api<Evidence[]>(`/evidence/NCR/${id}`));e.target.value=""}catch(e){setError(e instanceof Error?e.message:"Failed to upload evidence")}finally{setUploading(false)}}
 const overdue=!!(item&&item.status!=="CLOSED"&&item.due_date&&new Date(`${item.due_date}T23:59:59`).getTime()<Date.now());
 return <AuthGuard><Shell>
  <div className="page-head"><div><p className="eyebrow">Non-Conformance</p><h1>{item?.number||"NCR Detail"}</h1><p className="muted">{item?.title||"Loading NCR..."}</p></div><div className="head-actions">{project?<Link className="secondary-btn" href={`/projects/${project.id}`}>Project Workspace</Link>:null}<Link className="secondary-btn" href={`/ncrs${item?`?project_id=${encodeURIComponent(item.project_id)}`:""}`}>← NCR Register</Link></div></div>
  {error?<div className="error">{error}</div>:null}
  {!item?<p className="muted">Loading NCR...</p>:<>
   <div className="grid inspection-summary"><div className="card"><div className="muted">Status</div><div className="metric metric-small"><span className={`workflow workflow-${item.status.toLowerCase()}`}>{item.status.replace("_"," ")}</span></div></div><div className="card"><div className="muted">Severity</div><div className="metric metric-small"><span className={`severity severity-${item.severity.toLowerCase()}`}>{item.severity}</span></div></div><div className="card"><div className="muted">Due Date</div><div className="metric metric-small">{item.due_date||"—"}{overdue?<span className="overdue-text"> Overdue</span>:null}</div></div><div className="card"><div className="muted">Evidence</div><div className="metric">{evidence.length}</div></div></div>
   <form className="card form-card section-card" onSubmit={save}><div className="toolbar"><div><h2>NCR & Corrective Action</h2><p className="muted small">Complete root cause and corrective action before closure.</p></div></div><div className="form-grid">
    <label className="full-field"><span>Title *</span><input disabled={item.status==="CLOSED"} required value={item.title} onChange={e=>setField("title",e.target.value)}/></label>
    <label><span>Discipline</span><input disabled value={item.discipline}/></label><label><span>Severity</span><select disabled={item.status==="CLOSED"} value={item.severity} onChange={e=>setField("severity",e.target.value)}><option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>CRITICAL</option></select></label>
    <label><span>Due Date</span><input disabled={item.status==="CLOSED"} type="date" value={item.due_date||""} onChange={e=>setField("due_date",e.target.value)}/></label>
    <label className="full-field"><span>Description</span><textarea disabled={item.status==="CLOSED"} rows={5} value={item.description} onChange={e=>setField("description",e.target.value)}/></label>
    <label className="full-field"><span>Root Cause</span><textarea disabled={item.status==="CLOSED"} rows={5} value={item.root_cause||""} onChange={e=>setField("root_cause",e.target.value)} placeholder="Document verified root cause..."/></label>
    <label className="full-field"><span>Corrective Action</span><textarea disabled={item.status==="CLOSED"} rows={5} value={item.corrective_action||""} onChange={e=>setField("corrective_action",e.target.value)} placeholder="Define corrective action and verification..."/></label>
   </div>{item.status!=="CLOSED"?<div className="form-actions split-actions"><button type="button" className="secondary-btn" onClick={closeNCR} disabled={closing}>{closing?"Closing...":"Close NCR"}</button><button className="btn-action" disabled={saving}>{saving?"Saving...":"Save Changes"}</button></div>:<div className="source-banner">NCR closed {item.closed_at?new Date(item.closed_at).toLocaleString():""}</div>}</form>
   <div className="card section-card"><div className="toolbar"><div><h2>Evidence</h2><p className="muted small">Attach JPG, PNG, or PDF evidence up to 10 MB.</p></div>{item.status!=="CLOSED"?<label className="secondary-btn upload-btn">{uploading?"Uploading...":"+ Upload Evidence"}<input type="file" accept="image/jpeg,image/png,application/pdf" disabled={uploading} onChange={upload}/></label>:null}</div>{!evidence.length?<div className="empty-state">No NCR evidence uploaded yet.</div>:<div className="evidence-list">{evidence.map(f=><div key={f.id} className="evidence-row"><div><strong>{f.file_name}</strong><div className="muted small">{f.content_type||"file"} · {(f.size_bytes/1024).toFixed(1)} KB</div></div><span className="muted small">{new Date(f.created_at).toLocaleString()}</span></div>)}</div>}</div>
  </>}
 </Shell></AuthGuard>
}
