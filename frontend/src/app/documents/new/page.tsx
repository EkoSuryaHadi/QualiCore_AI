"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type Project={id:string;code:string;name:string}; type DocumentItem={id:string};
export default function NewDocumentPage(){
 const router=useRouter(); const [projects,setProjects]=useState<Project[]>([]); const [saving,setSaving]=useState(false); const [error,setError]=useState(""); const [form,setForm]=useState({project_id:"",document_no:"",title:"",discipline:"Mechanical",revision:"A",owner_name:"",due_date:""});
 useEffect(()=>{const q=new URLSearchParams(window.location.search);setForm(p=>({...p,project_id:q.get("project_id")||""}));api<Project[]>("/projects").then(setProjects).catch(()=>{})},[]);
 function setField(name:string,value:string){setForm(p=>({...p,[name]:value}))}
 async function submit(e:FormEvent){e.preventDefault();setSaving(true);setError("");try{const created=await api<DocumentItem>("/documents",{method:"POST",body:JSON.stringify({...form,owner_name:form.owner_name||null,due_date:form.due_date||null})});router.push(`/documents/${created.id}`)}catch(e){setError(e instanceof Error?e.message:"Failed to create document")}finally{setSaving(false)}}
 return <AuthGuard><Shell><div className="page-head"><div><p className="eyebrow">Document Control</p><h1>Create Document</h1><p className="muted">Register a controlled document before review and approval.</p></div><Link className="text-link" href="/documents">← Document Register</Link></div><form className="card form-card" onSubmit={submit}>{error?<div className="error">{error}</div>:null}<div className="form-grid"><label><span>Project *</span><select required value={form.project_id} onChange={e=>setField("project_id",e.target.value)}><option value="">Select project</option>{projects.map(p=><option key={p.id} value={p.id}>{p.code} — {p.name}</option>)}</select></label><label><span>Document No *</span><input required value={form.document_no} onChange={e=>setField("document_no",e.target.value)} placeholder="QC-MEC-001"/></label><label className="full-field"><span>Title *</span><input required value={form.title} onChange={e=>setField("title",e.target.value)} placeholder="Document title"/></label><label><span>Discipline *</span><select value={form.discipline} onChange={e=>setField("discipline",e.target.value)}><option>Mechanical</option><option>Piping</option><option>Civil</option><option>Electrical</option><option>Instrumentation</option><option>Process</option><option>Structural</option><option>Coating</option><option>Other</option></select></label><label><span>Revision</span><input value={form.revision} onChange={e=>setField("revision",e.target.value)}/></label><label><span>Owner / Responsible</span><input value={form.owner_name} onChange={e=>setField("owner_name",e.target.value)}/></label><label><span>Due Date</span><input type="date" value={form.due_date} onChange={e=>setField("due_date",e.target.value)}/></label></div><div className="form-actions"><Link className="secondary-btn" href="/documents">Cancel</Link><button className="btn-action" disabled={saving}>{saving?"Creating...":"Create Document"}</button></div></form></Shell></AuthGuard>
}
