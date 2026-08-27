from datetime import date
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import (
    Document,
    DocumentStatus,
    Inspection,
    InspectionResult,
    NCR,
    Project,
    ProjectStatus,
    PunchItem,
    Risk,
    RiskStatus,
    Severity,
    WorkflowStatus,
)
from .vendor_models import VendorQuality, VendorStatus


def _count(db: Session, stmt) -> int:
    return int(db.scalar(stmt) or 0)


def executive_dashboard(db: Session, org: str) -> dict:
    total_projects = _count(db, select(func.count()).select_from(Project).where(Project.organization_id == org))
    active_projects = _count(db, select(func.count()).select_from(Project).where(Project.organization_id == org, Project.status == ProjectStatus.ACTIVE))
    total_inspections = _count(db, select(func.count()).select_from(Inspection).where(Inspection.organization_id == org))
    failed_inspections = _count(db, select(func.count()).select_from(Inspection).where(Inspection.organization_id == org, Inspection.result == InspectionResult.FAIL))
    passed_inspections = _count(db, select(func.count()).select_from(Inspection).where(Inspection.organization_id == org, Inspection.result == InspectionResult.PASS))
    pass_rate = round((passed_inspections / total_inspections) * 100, 1) if total_inspections else 100.0

    open_ncr = _count(db, select(func.count()).select_from(NCR).where(NCR.organization_id == org, NCR.status != WorkflowStatus.CLOSED))
    critical_ncr = _count(db, select(func.count()).select_from(NCR).where(NCR.organization_id == org, NCR.status != WorkflowStatus.CLOSED, NCR.severity.in_([Severity.HIGH, Severity.CRITICAL])))
    open_punch = _count(db, select(func.count()).select_from(PunchItem).where(PunchItem.organization_id == org, PunchItem.status != WorkflowStatus.CLOSED))
    overdue_punch = _count(db, select(func.count()).select_from(PunchItem).where(PunchItem.organization_id == org, PunchItem.status != WorkflowStatus.CLOSED, PunchItem.due_date < date.today()))

    open_documents = _count(db, select(func.count()).select_from(Document).where(Document.organization_id == org, Document.status != DocumentStatus.APPROVED))
    documents_in_review = _count(db, select(func.count()).select_from(Document).where(Document.organization_id == org, Document.status == DocumentStatus.IN_REVIEW))

    open_risks = _count(db, select(func.count()).select_from(Risk).where(Risk.organization_id == org, Risk.status != RiskStatus.CLOSED))
    high_risks = _count(db, select(func.count()).select_from(Risk).where(Risk.organization_id == org, Risk.status != RiskStatus.CLOSED, Risk.score >= 15))

    vendor_count = _count(db, select(func.count()).select_from(VendorQuality).where(VendorQuality.organization_id == org))
    vendor_watchlist = _count(db, select(func.count()).select_from(VendorQuality).where(VendorQuality.organization_id == org, VendorQuality.status == VendorStatus.WATCHLIST))
    vendor_suspended = _count(db, select(func.count()).select_from(VendorQuality).where(VendorQuality.organization_id == org, VendorQuality.status == VendorStatus.SUSPENDED))
    average_vendor_score = float(db.scalar(select(func.avg(VendorQuality.overall_score)).where(VendorQuality.organization_id == org)) or 100.0)
    average_vendor_score = round(average_vendor_score, 1)

    penalty = (
        failed_inspections * 1.5
        + open_ncr * 2.5
        + critical_ncr * 2.5
        + open_punch * 0.5
        + overdue_punch * 1.5
        + documents_in_review * 0.5
        + high_risks * 3.0
        + vendor_watchlist * 2.0
        + vendor_suspended * 5.0
    )
    assurance_score = round(max(0.0, min(100.0, 100.0 - penalty)), 1)
    health_status = "GOOD" if assurance_score >= 85 else "ATTENTION" if assurance_score >= 70 else "CRITICAL"

    project_rows = db.scalars(select(Project).where(Project.organization_id == org).order_by(Project.code)).all()
    projects = []
    for project in project_rows:
        p_failed = _count(db, select(func.count()).select_from(Inspection).where(Inspection.project_id == project.id, Inspection.organization_id == org, Inspection.result == InspectionResult.FAIL))
        p_ncr = _count(db, select(func.count()).select_from(NCR).where(NCR.project_id == project.id, NCR.organization_id == org, NCR.status != WorkflowStatus.CLOSED))
        p_punch = _count(db, select(func.count()).select_from(PunchItem).where(PunchItem.project_id == project.id, PunchItem.organization_id == org, PunchItem.status != WorkflowStatus.CLOSED))
        p_docs = _count(db, select(func.count()).select_from(Document).where(Document.project_id == project.id, Document.organization_id == org, Document.status != DocumentStatus.APPROVED))
        p_risks = _count(db, select(func.count()).select_from(Risk).where(Risk.project_id == project.id, Risk.organization_id == org, Risk.status != RiskStatus.CLOSED, Risk.score >= 15))
        p_watch = _count(db, select(func.count()).select_from(VendorQuality).where(VendorQuality.project_id == project.id, VendorQuality.organization_id == org, VendorQuality.status.in_([VendorStatus.WATCHLIST, VendorStatus.SUSPENDED])))
        p_penalty = p_failed * 2 + p_ncr * 3 + p_punch + p_docs * 0.5 + p_risks * 4 + p_watch * 3
        p_score = round(max(0.0, 100.0 - p_penalty), 1)
        projects.append({
            "project_id": project.id,
            "code": project.code,
            "name": project.name,
            "progress": float(project.progress or 0),
            "quality_score": p_score,
            "failed_inspections": p_failed,
            "open_ncr": p_ncr,
            "open_punch": p_punch,
            "open_documents": p_docs,
            "high_risks": p_risks,
            "vendor_watchlist": p_watch,
        })

    projects.sort(key=lambda x: x["quality_score"])
    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "total_inspections": total_inspections,
        "failed_inspections": failed_inspections,
        "pass_rate": pass_rate,
        "open_ncr": open_ncr,
        "critical_ncr": critical_ncr,
        "open_punch": open_punch,
        "overdue_punch": overdue_punch,
        "open_documents": open_documents,
        "documents_in_review": documents_in_review,
        "high_risks": high_risks,
        "open_risks": open_risks,
        "vendor_count": vendor_count,
        "vendor_watchlist": vendor_watchlist,
        "vendor_suspended": vendor_suspended,
        "average_vendor_score": average_vendor_score,
        "assurance_score": assurance_score,
        "health_status": health_status,
        "projects": projects,
    }
