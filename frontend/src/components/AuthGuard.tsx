"use client";
import {ReactNode,useEffect,useState} from "react";import {useRouter} from "next/navigation";
export default function AuthGuard({children}:{children:ReactNode}){const router=useRouter();const[ok,setOk]=useState(false);useEffect(()=>{if(!localStorage.getItem("qc_token"))router.replace("/login");else setOk(true)},[router]);return ok?children:<div className="center">Checking session…</div>}
