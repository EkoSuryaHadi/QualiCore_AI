"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type Project={id:string;code:string;name:string};
type Inspection={id:string;project_id:string;discipline:string;inspection_type:string;location?:string|null;inspection_date:string;result:string;remarks?:string|null};
type NCR={id:string};

export default function NewNCRPage(){
 const router=useRouter();
 const [projects,setProjects]=useState<Project[]>([]); const [saving,setSaving]=useState(false); const [error,setError]=useState(""); const [inspectionId,setInspectionId]=useState("");
 const [form,setForm]=useState({project_id:"",number:`NCR-${new Date().toISOString().slice(0,10).replaceAll("-","")}-${String(Date.now()).slice(-4)}`,title:"",description:"",discipline:"Mechanical",severity:"MEDIUM",due_date:""});
 useEffect(()=>{
   const query=new URLSearchParams(window.location.search); const projectId=query.get("project_id")||""; const sourceId=query.get("inspection_id")||""; setInspectionId(sourceId); setForm(p=>({...p,project_id:projectId}));
   api<Project[]>("/projects").then(setProjects).catch(()=>{});
   if(sourceId)api<Inspection>(`/inspections/${sourceId}`).then(i=>setForm(p=>({...p,project_id:i.project_id,discipline:i.discipline,title:`Non-conformance from ${i.inspection_type}`,description:`Source Inspection: ${i.inspection_type}\nInspection Date: ${i.inspection_date}\nLocation: ${i.location||"—"}\nResult: ${i.result}\nRemarks: ${i.remarks||"—"}`}))).catch(e=>setError(e instanceof Error?e.message:"Failed to load source inspection"));
 },[]);
 function setField(name:string,value:string){setForm(p=>({...p,[name]:value}))}
 async function submit(e:FormEvent){e.preventDefault();setSaving(true);setError("");try{const created=await api<NCR>("/ncrs",{method:"POST",body:JSON.stringify({...form,due_date:form.due_date||null})});router.push(`/ncrs/${created.id}`)}catch(e){setError(e instanceof Error?e.message:"Failed to create NCR")}finally{setSaving(false)}}
 return <AuthGuard><Shell>
  <div className="page-head"><div><p className="eyebrow">Non-Conformance</p><h1>Create NCR</h1><p className="muted">Raise a non-conformance and assign its severity and due date.</p></div><Link className="text-link" href={`/ncrs${form.project_id?`?project_id=${encodeURIComponent(form.project_id)}`:""}`}>← NCR Register</Link></div>
  <form className="card form-card" onSubmit={submit}>{error?<div className="error">{error}</div>:null}{inspectionId?<div className="source-banner">Created from failed inspection · {inspectionId.slice(0,8)}</div>:null}
   <div className="form-grid">
    <label><span>Project *</span><select required value={form.project_id} onChange={e=>setField("project_id",e.target.value)}><option value="">Select project</option>{projects.map(p=><option key={p.id} value={p.id}>{p.code} — {p.name}</option>)}</select></label>
    <label><span>NCR Number *</span><input required value={form.number} onChange={e=>setField("number",e.target.value)}/></label>
    <label className="full-field"><span>Title *</span><input required value={form.title} onChange={e=>setField("title",e.target.value)} placeholder="Describe the non-conformance briefly"/></label>
    <label><span>Discipline *</span><select value={form.discipline} onChange={e=>setField("discipline",e.target.value)}><option>Mechanical</option><option>Piping</option><option>Civil</option><option>Electrical</option><option>Instrumentation</option><option>Process</option><option>Structural</option><option>Coating</option><option>Welding</option><option>Other</option></select></label>
    <label><span>Severity *</span><select value={form.severity} onChange={e=>setField("severity",e.target.value)}><option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>CRITICAL</option></select></label>
    <label><span>Due Date</span><input type="date" value={form.due_date} onChange={e=>setField("due_date",e.target.value)}/></label>
    <label className="full-field"><span>Description *</span><textarea rows={7} required value={form.description} onChange={e=>setField("description",e.target.value)}/></label>
   </div>
   <div className="form-actions"><Link className="secondary-btn" href="/ncrs">Cancel</Link><button className="btn-action" disabled={saving}>{saving?"Creating...":"Create NCR"}</button></div>
  </form>
 </Shell></AuthGuard>
}
