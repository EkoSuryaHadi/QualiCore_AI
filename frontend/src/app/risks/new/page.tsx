"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type Project={id:string;code:string;name:string};type Risk={id:string};

export default function NewRiskPage(){
 const router=useRouter();const [projects,setProjects]=useState<Project[]>([]);const [saving,setSaving]=useState(false);const [error,setError]=useState("");const [form,setForm]=useState({project_id:"",title:"",category:"Quality",probability:3,impact:3,mitigation:"",owner_name:"",due_date:""});
 useEffect(()=>{const q=new URLSearchParams(window.location.search);const p=q.get("project_id")||"";setForm(f=>({...f,project_id:p}));api<Project[]>("/projects").then(setProjects).catch(()=>{})},[]);
 function setField(name:string,value:string|number){setForm(f=>({...f,[name]:value}))}
 async function submit(e:FormEvent){e.preventDefault();setSaving(true);setError("");try{const created=await api<Risk>("/risks",{method:"POST",body:JSON.stringify({...form,probability:Number(form.probability),impact:Number(form.impact),mitigation:form.mitigation||null,owner_name:form.owner_name||null,due_date:form.due_date||null})});router.push(`/risks/${created.id}`)}catch(e){setError(e instanceof Error?e.message:"Failed to create risk")}finally{setSaving(false)}}
 const score=Number(form.probability)*Number(form.impact);
 return <AuthGuard><Shell>
  <div className="page-head"><div><p className="eyebrow">Project Assurance Risk</p><h1>Create Risk</h1><p className="muted">Register a project assurance risk and calculate its initial score.</p></div><Link className="text-link" href={`/risks${form.project_id?`?project_id=${encodeURIComponent(form.project_id)}`:""}`}>← Risk Register</Link></div>
  <form className="card form-card" onSubmit={submit}>{error?<div className="error">{error}</div>:null}<div className="form-grid">
   <label><span>Project *</span><select required value={form.project_id} onChange={e=>setField("project_id",e.target.value)}><option value="">Select project</option>{projects.map(p=><option key={p.id} value={p.id}>{p.code} — {p.name}</option>)}</select></label>
   <label><span>Category *</span><select value={form.category} onChange={e=>setField("category",e.target.value)}><option>Quality</option><option>Technical</option><option>Schedule</option><option>Vendor</option><option>Construction</option><option>HSE</option><option>Commercial</option><option>Interface</option><option>Other</option></select></label>
   <label className="full-field"><span>Risk Title *</span><input required value={form.title} onChange={e=>setField("title",e.target.value)} placeholder="Describe the risk event"/></label>
   <label><span>Probability (1–5)</span><input type="number" min="1" max="5" value={form.probability} onChange={e=>setField("probability",Number(e.target.value))}/></label>
   <label><span>Impact (1–5)</span><input type="number" min="1" max="5" value={form.impact} onChange={e=>setField("impact",Number(e.target.value))}/></label>
   <label><span>Risk Score</span><div className="score-preview"><span className={`risk-score risk-score-${score>=15?"high":score>=8?"medium":"low"}`}>{score}</span><span className="muted small">P × I</span></div></label>
   <label><span>Owner</span><input value={form.owner_name} onChange={e=>setField("owner_name",e.target.value)} placeholder="Responsible person / team"/></label>
   <label><span>Due Date</span><input type="date" value={form.due_date} onChange={e=>setField("due_date",e.target.value)}/></label>
   <label className="full-field"><span>Mitigation</span><textarea rows={6} value={form.mitigation} onChange={e=>setField("mitigation",e.target.value)} placeholder="Initial mitigation plan..."/></label>
  </div><div className="form-actions"><Link className="secondary-btn" href="/risks">Cancel</Link><button className="btn-action" disabled={saving}>{saving?"Creating...":"Create Risk"}</button></div></form>
 </Shell></AuthGuard>
}
