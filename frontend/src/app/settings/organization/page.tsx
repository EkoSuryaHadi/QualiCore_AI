"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import AuthGuard from "@/components/AuthGuard";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";

type Organization = { id:string; name:string; slug:string; country?:string|null; is_active:boolean; created_at:string };

export default function OrganizationSettingsPage(){
  const [org,setOrg]=useState<Organization|null>(null);
  const [name,setName]=useState("");
  const [country,setCountry]=useState("");
  const [error,setError]=useState("");
  const [notice,setNotice]=useState("");
  const [saving,setSaving]=useState(false);
  useEffect(()=>{api<Organization>("/identity/organization").then(data=>{setOrg(data);setName(data.name);setCountry(data.country||"")}).catch(err=>setError(err instanceof Error?err.message:"Failed to load organization"))},[]);
  async function save(e:FormEvent){e.preventDefault();setSaving(true);setError("");setNotice("");try{const data=await api<Organization>("/identity/organization",{method:"PATCH",body:JSON.stringify({name,country:country||null})});setOrg(data);setNotice("Organization settings saved.")}catch(err){setError(err instanceof Error?err.message:"Could not save organization")}finally{setSaving(false)}}
  return <AuthGuard><Shell>
    <div className="page-head"><div><p className="eyebrow">Administration</p><h1>Organization Settings</h1><p className="muted">Manage the company workspace that owns your QualiCore projects and users.</p></div>{org?<div className="org-chip"><strong>{org.name}</strong><span>{org.slug}</span></div>:null}</div>
    <div className="admin-tabs"><Link href="/settings/organization">Organization</Link><Link href="/settings/users">Users & Access</Link></div>
    {error?<div className="error">{error}</div>:null}{notice?<div className="source-banner">{notice}</div>:null}
    <form className="card settings-form" onSubmit={save}>
      <h2>Company Profile</h2><p className="muted small">This information identifies the tenant/workspace across QualiCore.</p>
      <label>Organization Name<input required minLength={2} value={name} onChange={e=>setName(e.target.value)}/></label>
      <label>Country<input value={country} onChange={e=>setCountry(e.target.value)}/></label>
      {org?<><label>Workspace Slug<input disabled value={org.slug}/></label><label>Organization ID<input disabled value={org.id}/></label></>:null}
      <div className="form-actions"><button className="btn-action" disabled={saving}>{saving?"Saving...":"Save Organization"}</button></div>
    </form>
  </Shell></AuthGuard>
}
