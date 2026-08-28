from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session

from .assurance_engine import analyze_portfolio
from .scoped_assurance import analyze_visible_projects

SUGGESTED_QUESTIONS = [
    "What are the biggest assurance risks?",
    "Why is the assurance score low?",
    "Which issues should we prioritize?",
    "What should be discussed in the weekly assurance meeting?",
    "Prepare an executive management summary.",
    "Which vendor or workstream needs attention?",
]

def _top_findings(analysis: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]: return list(analysis.get("findings", []))[:limit]
def _finding_lines(findings: list[dict[str, Any]], limit: int = 5) -> list[str]: return [f"{i+1}. [{f['severity']}] {f['title']} — {f['rationale']}" for i,f in enumerate(findings[:limit])]
def _action_lines(findings: list[dict[str, Any]], limit: int = 5) -> list[str]:
    seen:set[str]=set(); actions:list[str]=[]
    for f in findings:
        action=f.get("recommended_action","").strip()
        if action and action not in seen: seen.add(action); actions.append(action)
        if len(actions)>=limit: break
    return [f"{i+1}. {a}" for i,a in enumerate(actions)]
def _workstream_summary(findings:list[dict[str,Any]])->str:
    counts:dict[str,int]={}
    for f in findings:
        w=f.get("workstream","OTHER"); counts[w]=counts.get(w,0)+1
    if not counts:return "No assurance workstream currently has an active rule-based finding."
    return ", ".join(f"{n}: {c}" for n,c in sorted(counts.items(),key=lambda x:(-x[1],x[0])))

def answer_question(db:Session, organization_id:str, question:str, project_id:str|None=None, visible_project_ids:list[str]|None=None)->dict[str,Any]:
    if project_id:
        analysis=analyze_portfolio(db,organization_id,project_id)
    elif visible_project_ids is None:
        analysis=analyze_portfolio(db,organization_id)
    else:
        analysis=analyze_visible_projects(db,organization_id,visible_project_ids)
    findings=_top_findings(analysis,8); q=(question or "").strip().lower() or "what are the biggest assurance risks?"
    if not findings:
        answer=f"The current {analysis['scope'].lower()} assurance index is {analysis['assurance_index']} ({analysis['health_status']}). No active rule-based assurance findings are present in the available records. Continue routine surveillance and verify that project records are complete and current."
        actions=["Maintain routine assurance surveillance and data completeness checks."]
    elif any(k in q for k in ["why","score","low","turun","rendah"]):
        s=analysis["severity_counts"]
        answer=f"The assurance index is {analysis['assurance_index']} ({analysis['health_status']}). It is being reduced by {s.get('CRITICAL',0)} critical, {s.get('HIGH',0)} high, and {s.get('MEDIUM',0)} medium findings. The strongest current drivers are:\n"+"\n".join(_finding_lines(findings,4)); actions=[f["recommended_action"] for f in findings[:4]]
    elif any(k in q for k in ["prior","action","tindakan","dulu","focus","fokus"]):
        answer="Prioritize the highest-severity exposures first, then address dependencies that can block construction, completion, or handover. Recommended sequence:\n"+"\n".join(_action_lines(findings,5)); actions=[f["recommended_action"] for f in findings[:5]]
    elif any(k in q for k in ["weekly","meeting","rapat","bahas"]):
        answer="For the next assurance meeting, focus the agenda on the following evidence-backed items:\n"+"\n".join(_finding_lines(findings,5))+"\nConfirm owner, target date, blocking dependency, and verification evidence for each item before closing the meeting."; actions=["Assign a single accountable owner to each priority finding.","Confirm dated recovery commitments and dependencies.","Require objective verification evidence before closure."]
    elif any(k in q for k in ["executive","management","summary","ringkas","manajemen"]):
        top=findings[0]; answer=f"Executive assurance status is {analysis['health_status']} with an index of {analysis['assurance_index']}. There are {analysis['finding_count']} active findings across {analysis['project_count']} project(s). The leading exposure is {top['title'].lower()} ({top['severity']}) in {top['workstream']}. Current workstream concentration: {_workstream_summary(findings)}. Management attention should remain on high-severity closure discipline, overdue dependencies, and verification of recovery actions."; actions=[f["recommended_action"] for f in findings[:3]]
    elif any(k in q for k in ["vendor","supplier","workstream","discipline"]):
        vendor=[f for f in findings if f["workstream"]=="VENDOR"]; selected=vendor or findings; answer=f"Current assurance finding concentration is {_workstream_summary(findings)}. "+("Vendor-specific exposure is present.\n" if vendor else "No vendor-specific finding ranks above the current leading exposures.\n")+"\n".join(_finding_lines(selected,4)); actions=[f["recommended_action"] for f in selected[:4]]
    else:
        answer=f"The current {analysis['scope'].lower()} assurance status is {analysis['health_status']} with an index of {analysis['assurance_index']}. The most important evidence-backed findings are:\n"+"\n".join(_finding_lines(findings,5)); actions=[f["recommended_action"] for f in findings[:5]]
    citations=[{"finding_code":f["code"],"severity":f["severity"],"workstream":f["workstream"],"project_id":f.get("project_id"),"project_code":f.get("project_code"),"evidence":f.get("evidence") or {}} for f in findings[:5]]
    return {"mode":"GROUNDED_RULE_BASED","scope":analysis["scope"],"project_id":project_id,"question":question,"answer":answer,"assurance_index":analysis["assurance_index"],"health_status":analysis["health_status"],"finding_count":analysis["finding_count"],"recommended_actions":actions,"citations":citations,"suggested_questions":SUGGESTED_QUESTIONS,"disclaimer":"Answer generated from current QualiCore records and deterministic assurance findings; no external facts were inferred."}
