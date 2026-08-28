from typing import Any
from sqlalchemy.orm import Session

from .assurance_engine import analyze_project


def analyze_visible_projects(db: Session, organization_id: str, project_ids: list[str], project_id: str | None = None) -> dict[str, Any]:
    ids = [project_id] if project_id else project_ids
    findings: list[dict[str, Any]] = []
    for pid in ids:
        findings.extend(analyze_project(db, organization_id, pid))

    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for finding in findings:
        severity = finding.get("severity", "LOW")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

    assurance_index = max(0, round(
        100
        - severity_counts["CRITICAL"] * 12
        - severity_counts["HIGH"] * 6
        - severity_counts["MEDIUM"] * 2.5,
        1,
    ))
    health = "GOOD" if assurance_index >= 85 else "ATTENTION" if assurance_index >= 70 else "CRITICAL"
    return {
        "scope": "PROJECT" if project_id else "PORTFOLIO",
        "project_id": project_id,
        "project_count": len(ids),
        "assurance_index": assurance_index,
        "health_status": health,
        "finding_count": len(findings),
        "severity_counts": severity_counts,
        "findings": findings,
    }
