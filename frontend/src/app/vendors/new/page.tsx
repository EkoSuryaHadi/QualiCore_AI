"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type Project={id:string;code:string;name:string}; type Vendor={id:string};

export default function NewVendorPage(){
 const router=useRouter(); const [projects,setProjects]=useState<Project[]>([]); const [saving,setSaving]=useState(false); const [error,setError]=useState("");
 const [form,setForm]=useState({project_id:"",vendor_code:"",vendor_name:"",category:"General",contact_name:"",contact_email:"",status:"APPROVED",quality_score:100,delivery_score:100,documentation_score:100,inspection_score:100,ncr_count:0,notes:""});
 useEffect(()=>{const q=new URLSearchParams(window.location.search);setForm(p=>({...p,project_id:q.get("project_id")||""}));api<Project[]>("/projects").then(setProjects).catch(()=>{})},[]);
 function setField(name:string,value:string|number){setForm(p=>({...p,[name]:value}))}
 const overall=Math.max(0,Math.min(100,form.quality_score*.35+form.delivery_score*.20+form.documentation_score*.20+form.inspection_score*.25-Math.min(form.ncr_count*2,20)));
 async function submit(e:FormEvent){e.preventDefault();setSaving(true);setError("");try{const created=await api<Vendor>("/vendors",{method:"POST",body:JSON.stringify({...form,contact_name:form.contact_name||null,contact_email:form.contact_email||null,notes:form.notes||null})});router.push(`/vendors/${created.id}`)}catch(e){setError(e instanceof Error?e.message:"Failed to create vendor")}finally{setSaving(false)}}
 return <AuthGuard><Shell><div className="page-head"><div><p className="eyebrow">Vendor Assurance</p><h1>Add Vendor</h1><p className="muted">Create a project vendor quality record and baseline score.</p></div><Link className="text-link" href={`/vendors${form.project_id?`?project_id=${encodeURIComponent(form.project_id)}`:""}`}>← Vendor Quality</Link></div>
 <form className="card form-card" onSubmit={submit}>{error?<div className="error">{error}</div>:null}<div className="source-banner">Calculated Overall Score: {overall.toFixed(1)}</div><div className="form-grid">
 <label><span>Project *</span><select required value={form.project_id} onChange={e=>setField("project_id",e.target.value)}><option value="">Select project</option>{projects.map(p=><option key={p.id} value={p.id}>{p.code} — {p.name}</option>)}</select></label>
 <label><span>Vendor Code *</span><input required value={form.vendor_code} onChange={e=>setField("vendor_code",e.target.value)} placeholder="VND-001"/></label>
 <label className="full-field"><span>Vendor Name *</span><input required value={form.vendor_name} onChange={e=>setField("vendor_name",e.target.value)} placeholder="Vendor / Supplier name"/></label>
 <label><span>Category</span><select value={form.category} onChange={e=>setField("category",e.target.value)}><option>General</option><option>Mechanical</option><option>Piping</option><option>Electrical</option><option>Instrumentation</option><option>Civil</option><option>Structural</option><option>Equipment</option><option>Material</option><option>Service</option></select></label>
 <label><span>Status</span><select value={form.status} onChange={e=>setField("status",e.target.value)}><option>APPROVED</option><option>WATCHLIST</option><option>SUSPENDED</option></select></label>
 <label><span>Contact Name</span><input value={form.contact_name} onChange={e=>setField("contact_name",e.target.value)}/></label><label><span>Contact Email</span><input type="email" value={form.contact_email} onChange={e=>setField("contact_email",e.target.value)}/></label>
 <Score label="Quality Score" value={form.quality_score} set={v=>setField("quality_score",v)}/><Score label="Delivery Score" value={form.delivery_score} set={v=>setField("delivery_score",v)}/><Score label="Documentation Score" value={form.documentation_score} set={v=>setField("documentation_score",v)}/><Score label="Inspection Score" value={form.inspection_score} set={v=>setField("inspection_score",v)}/>
 <label><span>NCR Count</span><input type="number" min="0" value={form.ncr_count} onChange={e=>setField("ncr_count",Number(e.target.value))}/></label>
 <label className="full-field"><span>Notes</span><textarea rows={5} value={form.notes} onChange={e=>setField("notes",e.target.value)}/></label>
 </div><div className="form-actions"><Link className="secondary-btn" href="/vendors">Cancel</Link><button className="btn-action" disabled={saving}>{saving?"Creating...":"Create Vendor"}</button></div></form></Shell></AuthGuard>
}
function Score({label,value,set}:{label:string;value:number;set:(v:number)=>void}){return <label><span>{label}</span><input type="number" min="0" max="100" value={value} onChange={e=>set(Number(e.target.value))}/></label>}
