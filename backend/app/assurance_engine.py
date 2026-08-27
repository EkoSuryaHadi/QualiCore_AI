from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import (
    Document,
    DocumentStatus,
    Inspection,
    InspectionResult,
    NCR,
    Project,
    PunchItem,
    Risk,
    RiskStatus,
    Severity,
    WorkflowStatus,
)
from .vendor_models import VendorQuality, VendorStatus


@dataclass
class AssuranceFinding:
    code: str
    severity: str
    confidence: float
    workstream: str
    title: str
    rationale: str
    recommended_action: str
    project_id: str | None = None
    project_code: str | None = None
    evidence: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _count(db: Session, stmt) -> int:
    return int(db.scalar(stmt) or 0)


def _project(db: Session, org: str, project_id: str) -> Project | None:
    return db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == org,
        )
    )


def _project_ids(db: Session, org: str, project_id: str | None) -> list[str]:
    if project_id:
        return [project_id] if _project(db, org, project_id) else []
    return list(db.scalars(select(Project.id).where(Project.organization_id == org)).all())


def analyze_project(db: Session, org: str, project_id: str) -> list[dict[str, Any]]:
    project = _project(db, org, project_id)
    if not project:
        return []

    findings: list[AssuranceFinding] = []

    total_inspections = _count(
        db,
        select(func.count()).select_from(Inspection).where(
            Inspection.organization_id == org,
            Inspection.project_id == project_id,
        ),
    )
    failed_inspections = _count(
        db,
        select(func.count()).select_from(Inspection).where(
            Inspection.organization_id == org,
            Inspection.project_id == project_id,
            Inspection.result == InspectionResult.FAIL,
        ),
    )
    if total_inspections >= 3:
        fail_rate = round(failed_inspections / total_inspections * 100, 1)
        if fail_rate >= 30:
            findings.append(
                AssuranceFinding(
                    code="INSPECTION_FAIL_RATE_HIGH",
                    severity="HIGH" if fail_rate < 50 else "CRITICAL",
                    confidence=0.98,
                    workstream="INSPECTION",
                    title="Inspection failure rate is elevated",
                    rationale=f"{failed_inspections} of {total_inspections} inspections failed ({fail_rate}%).",
                    recommended_action="Run discipline-level failure review and verify corrective actions before releasing the next work front.",
                    project_id=project.id,
                    project_code=project.code,
                    evidence={"failed_inspections": failed_inspections, "total_inspections": total_inspections, "fail_rate": fail_rate},
                )
            )

    critical_ncr = _count(
        db,
        select(func.count()).select_from(NCR).where(
            NCR.organization_id == org,
            NCR.project_id == project_id,
            NCR.status != WorkflowStatus.CLOSED,
            NCR.severity.in_([Severity.HIGH, Severity.CRITICAL]),
        ),
    )
    overdue_ncr = _count(
        db,
        select(func.count()).select_from(NCR).where(
            NCR.organization_id == org,
            NCR.project_id == project_id,
            NCR.status != WorkflowStatus.CLOSED,
            NCR.due_date.is_not(None),
            NCR.due_date < date.today(),
        ),
    )
    if critical_ncr:
        findings.append(
            AssuranceFinding(
                code="NCR_HIGH_CRITICAL_OPEN",
                severity="CRITICAL" if critical_ncr >= 3 else "HIGH",
                confidence=1.0,
                workstream="NCR",
                title="High or critical NCR exposure remains open",
                rationale=f"{critical_ncr} high/critical NCR(s) remain unresolved.",
                recommended_action="Escalate ownership, validate root cause quality, and agree dated corrective-action closure commitments.",
                project_id=project.id,
                project_code=project.code,
                evidence={"high_critical_open_ncr": critical_ncr},
            )
        )
    if overdue_ncr:
        findings.append(
            AssuranceFinding(
                code="NCR_OVERDUE",
                severity="HIGH" if overdue_ncr >= 3 else "MEDIUM",
                confidence=1.0,
                workstream="NCR",
                title="NCR corrective actions are overdue",
                rationale=f"{overdue_ncr} open NCR(s) are past due date.",
                recommended_action="Prioritize overdue NCR closure and review whether schedule or turnover activities depend on these items.",
                project_id=project.id,
                project_code=project.code,
                evidence={"overdue_ncr": overdue_ncr},
            )
        )

    overdue_punch = _count(
        db,
        select(func.count()).select_from(PunchItem).where(
            PunchItem.organization_id == org,
            PunchItem.project_id == project_id,
            PunchItem.status != WorkflowStatus.CLOSED,
            PunchItem.due_date.is_not(None),
            PunchItem.due_date < date.today(),
        ),
    )
    if overdue_punch:
        findings.append(
            AssuranceFinding(
                code="PUNCH_OVERDUE",
                severity="HIGH" if overdue_punch >= 5 else "MEDIUM",
                confidence=1.0,
                workstream="PUNCH",
                title="Completion punch items are overdue",
                rationale=f"{overdue_punch} punch item(s) are overdue.",
                recommended_action="Reconfirm responsible owners and close prerequisite punch items before mechanical completion or handover milestones.",
                project_id=project.id,
                project_code=project.code,
                evidence={"overdue_punch": overdue_punch},
            )
        )

    overdue_docs = _count(
        db,
        select(func.count()).select_from(Document).where(
            Document.organization_id == org,
            Document.project_id == project_id,
            Document.status != DocumentStatus.APPROVED,
            Document.due_date.is_not(None),
            Document.due_date < date.today(),
        ),
    )
    review_docs = _count(
        db,
        select(func.count()).select_from(Document).where(
            Document.organization_id == org,
            Document.project_id == project_id,
            Document.status == DocumentStatus.IN_REVIEW,
        ),
    )
    if overdue_docs:
        findings.append(
            AssuranceFinding(
                code="DOCUMENT_OVERDUE",
                severity="HIGH" if overdue_docs >= 5 else "MEDIUM",
                confidence=1.0,
                workstream="DOCUMENT",
                title="Required documents are overdue",
                rationale=f"{overdue_docs} non-approved document(s) are beyond due date; {review_docs} are currently in review.",
                recommended_action="Prioritize document review/approval where release, fabrication, construction, or turnover depends on approved status.",
                project_id=project.id,
                project_code=project.code,
                evidence={"overdue_documents": overdue_docs, "documents_in_review": review_docs},
            )
        )

    high_risks = list(
        db.scalars(
            select(Risk).where(
                Risk.organization_id == org,
                Risk.project_id == project_id,
                Risk.status != RiskStatus.CLOSED,
                Risk.score >= 15,
            ).order_by(Risk.score.desc())
        ).all()
    )
    if high_risks:
        top = high_risks[0]
        findings.append(
            AssuranceFinding(
                code="HIGH_RISK_EXPOSURE",
                severity="CRITICAL" if top.score >= 20 else "HIGH",
                confidence=1.0,
                workstream="RISK",
                title="High project risk exposure requires management attention",
                rationale=f"{len(high_risks)} high-risk item(s) remain open. Highest score is {top.score}: {top.title}.",
                recommended_action="Confirm mitigation effectiveness, accountable owner, and target date for the highest residual risks.",
                project_id=project.id,
                project_code=project.code,
                evidence={"high_risk_count": len(high_risks), "highest_score": top.score, "highest_risk": top.title},
            )
        )

    vendor_alerts = list(
        db.scalars(
            select(VendorQuality).where(
                VendorQuality.organization_id == org,
                VendorQuality.project_id == project_id,
                VendorQuality.status.in_([VendorStatus.WATCHLIST, VendorStatus.SUSPENDED]),
            ).order_by(VendorQuality.overall_score.asc())
        ).all()
    )
    if vendor_alerts:
        worst = vendor_alerts[0]
        findings.append(
            AssuranceFinding(
                code="VENDOR_QUALITY_ALERT",
                severity="CRITICAL" if worst.status == VendorStatus.SUSPENDED else "HIGH",
                confidence=0.99,
                workstream="VENDOR",
                title="Vendor quality performance is below acceptable threshold",
                rationale=f"{len(vendor_alerts)} vendor(s) are on watchlist/suspended. Lowest score is {worst.overall_score}: {worst.vendor_name}.",
                recommended_action="Review vendor recovery plan, open NCR trend, inspection performance, and whether additional surveillance is required.",
                project_id=project.id,
                project_code=project.code,
                evidence={"vendor_alert_count": len(vendor_alerts), "lowest_vendor_score": worst.overall_score, "vendor": worst.vendor_name},
            )
        )

    open_ncr = _count(
        db,
        select(func.count()).select_from(NCR).where(
            NCR.organization_id == org,
            NCR.project_id == project_id,
            NCR.status != WorkflowStatus.CLOSED,
        ),
    )
    open_punch = _count(
        db,
        select(func.count()).select_from(PunchItem).where(
            PunchItem.organization_id == org,
            PunchItem.project_id == project_id,
            PunchItem.status != WorkflowStatus.CLOSED,
        ),
    )
    if failed_inspections >= 2 and open_ncr >= 1 and open_punch >= 1:
        findings.append(
            AssuranceFinding(
                code="CROSS_WORKSTREAM_QUALITY_CLUSTER",
                severity="HIGH",
                confidence=0.92,
                workstream="CROSS_WORKSTREAM",
                title="Quality issues are clustering across multiple assurance workstreams",
                rationale=f"The project has {failed_inspections} failed inspections, {open_ncr} open NCR(s), and {open_punch} open punch item(s).",
                recommended_action="Conduct an integrated assurance review to determine whether the records share a common discipline, vendor, work package, or systemic root cause.",
                project_id=project.id,
                project_code=project.code,
                evidence={"failed_inspections": failed_inspections, "open_ncr": open_ncr, "open_punch": open_punch},
            )
        )

    order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    findings.sort(key=lambda f: (order.get(f.severity, 9), -f.confidence, f.workstream))
    return [finding.to_dict() for finding in findings]


def analyze_portfolio(db: Session, org: str, project_id: str | None = None) -> dict[str, Any]:
    ids = _project_ids(db, org, project_id)
    findings: list[dict[str, Any]] = []
    for pid in ids:
        findings.extend(analyze_project(db, org, pid))

    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for finding in findings:
        severity_counts[finding["severity"]] = severity_counts.get(finding["severity"], 0) + 1

    assurance_index = max(
        0,
        round(
            100
            - severity_counts["CRITICAL"] * 12
            - severity_counts["HIGH"] * 6
            - severity_counts["MEDIUM"] * 2.5,
            1,
        ),
    )
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
