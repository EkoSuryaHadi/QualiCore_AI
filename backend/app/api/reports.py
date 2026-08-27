from datetime import date, datetime, timezone
import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
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
    User,
    WorkflowStatus,
)
from ..security import get_current_user
from ..vendor_models import VendorQuality, VendorStatus

router = APIRouter(prefix="/reports", tags=["Reports"])


def scalar(db: Session, stmt):
    return db.scalar(stmt) or 0


def build_report(db: Session, org: str, project_id: str | None = None):
    project = None
    if project_id:
        project = db.scalar(
            select(Project).where(Project.id == project_id, Project.organization_id == org)
        )
        if not project:
            raise HTTPException(404, "Project not found")

    def scoped(model, *extra):
        conditions = [model.organization_id == org, *extra]
        if project_id:
            conditions.append(model.project_id == project_id)
        return conditions

    project_count = 1 if project else scalar(
        db,
        select(func.count()).select_from(Project).where(Project.organization_id == org),
    )
    active_projects = 1 if project and project.status.value == "ACTIVE" else scalar(
        db,
        select(func.count()).select_from(Project).where(
            Project.organization_id == org, Project.status == "ACTIVE"
        ),
    ) if not project else 0

    total_inspections = scalar(
        db, select(func.count()).select_from(Inspection).where(*scoped(Inspection))
    )
    failed_inspections = scalar(
        db,
        select(func.count()).select_from(Inspection).where(
            *scoped(Inspection, Inspection.result == InspectionResult.FAIL)
        ),
    )
    pass_rate = round(((total_inspections - failed_inspections) / total_inspections) * 100, 1) if total_inspections else 100.0

    open_ncr = scalar(
        db,
        select(func.count()).select_from(NCR).where(
            *scoped(NCR, NCR.status != WorkflowStatus.CLOSED)
        ),
    )
    critical_ncr = scalar(
        db,
        select(func.count()).select_from(NCR).where(
            *scoped(
                NCR,
                NCR.status != WorkflowStatus.CLOSED,
                NCR.severity.in_([Severity.HIGH, Severity.CRITICAL]),
            )
        ),
    )
    open_punch = scalar(
        db,
        select(func.count()).select_from(PunchItem).where(
            *scoped(PunchItem, PunchItem.status != WorkflowStatus.CLOSED)
        ),
    )
    overdue_punch = scalar(
        db,
        select(func.count()).select_from(PunchItem).where(
            *scoped(
                PunchItem,
                PunchItem.status != WorkflowStatus.CLOSED,
                PunchItem.due_date < date.today(),
            )
        ),
    )
    open_documents = scalar(
        db,
        select(func.count()).select_from(Document).where(
            *scoped(Document, Document.status != DocumentStatus.APPROVED)
        ),
    )
    documents_in_review = scalar(
        db,
        select(func.count()).select_from(Document).where(
            *scoped(Document, Document.status == DocumentStatus.IN_REVIEW)
        ),
    )
    open_risks = scalar(
        db,
        select(func.count()).select_from(Risk).where(
            *scoped(Risk, Risk.status != RiskStatus.CLOSED)
        ),
    )
    high_risks = scalar(
        db,
        select(func.count()).select_from(Risk).where(
            *scoped(Risk, Risk.status != RiskStatus.CLOSED, Risk.score >= 15)
        ),
    )
    vendor_count = scalar(
        db,
        select(func.count()).select_from(VendorQuality).where(*scoped(VendorQuality)),
    )
    vendor_watchlist = scalar(
        db,
        select(func.count()).select_from(VendorQuality).where(
            *scoped(VendorQuality, VendorQuality.status == VendorStatus.WATCHLIST)
        ),
    )
    vendor_suspended = scalar(
        db,
        select(func.count()).select_from(VendorQuality).where(
            *scoped(VendorQuality, VendorQuality.status == VendorStatus.SUSPENDED)
        ),
    )
    avg_vendor_score = db.scalar(
        select(func.avg(VendorQuality.overall_score)).where(*scoped(VendorQuality))
    )
    average_vendor_score = round(float(avg_vendor_score), 1) if avg_vendor_score is not None else 100.0

    penalty = (
        failed_inspections * 2
        + open_ncr * 3
        + critical_ncr * 3
        + open_punch
        + overdue_punch * 2
        + high_risks * 3
        + open_documents * 0.5
        + vendor_watchlist * 3
        + vendor_suspended * 6
    )
    assurance_score = round(max(0.0, 100.0 - float(penalty)), 1)
    health_status = "GOOD" if assurance_score >= 85 else "ATTENTION" if assurance_score >= 70 else "CRITICAL"

    priorities: list[str] = []
    if critical_ncr:
        priorities.append(f"Resolve {critical_ncr} high/critical open NCR")
    if high_risks:
        priorities.append(f"Mitigate {high_risks} high project risks")
    if overdue_punch:
        priorities.append(f"Close {overdue_punch} overdue punch items")
    if vendor_watchlist or vendor_suspended:
        priorities.append(f"Review {vendor_watchlist + vendor_suspended} vendor quality alerts")
    if documents_in_review:
        priorities.append(f"Progress {documents_in_review} documents currently in review")
    if not priorities:
        priorities.append("No critical assurance exposure identified in the current snapshot")

    scope_name = f"{project.code} — {project.name}" if project else "Portfolio"
    narrative = (
        f"{scope_name} assurance is {health_status.lower()} with a composite score of {assurance_score}. "
        f"Inspection pass rate is {pass_rate}%, with {open_ncr} open NCR, {open_punch} open punch items, "
        f"{open_documents} open documents, {high_risks} high risks, and {vendor_watchlist + vendor_suspended} vendor alerts."
    )

    return {
        "generated_at": datetime.now(timezone.utc),
        "scope": "PROJECT" if project else "PORTFOLIO",
        "project_id": project.id if project else None,
        "project_code": project.code if project else None,
        "project_name": project.name if project else None,
        "project_count": project_count,
        "active_projects": active_projects,
        "assurance_score": assurance_score,
        "health_status": health_status,
        "total_inspections": total_inspections,
        "failed_inspections": failed_inspections,
        "pass_rate": pass_rate,
        "open_ncr": open_ncr,
        "critical_ncr": critical_ncr,
        "open_punch": open_punch,
        "overdue_punch": overdue_punch,
        "open_documents": open_documents,
        "documents_in_review": documents_in_review,
        "open_risks": open_risks,
        "high_risks": high_risks,
        "vendor_count": vendor_count,
        "vendor_watchlist": vendor_watchlist,
        "vendor_suspended": vendor_suspended,
        "average_vendor_score": average_vendor_score,
        "narrative": narrative,
        "priorities": priorities,
    }


@router.get("/executive")
def executive(
    project_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return build_report(db, user.organization_id, project_id)


@router.get("/executive.csv")
def executive_csv(
    project_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    report = build_report(db, user.organization_id, project_id)
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["QualiCore Executive Assurance Report"])
    writer.writerow(["Generated At", report["generated_at"].isoformat()])
    writer.writerow(["Scope", report["scope"]])
    if report["project_code"]:
        writer.writerow(["Project", f'{report["project_code"]} - {report["project_name"]}'])
    writer.writerow([])
    writer.writerow(["Metric", "Value"])
    for key in (
        "assurance_score", "health_status", "project_count", "active_projects",
        "total_inspections", "failed_inspections", "pass_rate", "open_ncr",
        "critical_ncr", "open_punch", "overdue_punch", "open_documents",
        "documents_in_review", "open_risks", "high_risks", "vendor_count",
        "vendor_watchlist", "vendor_suspended", "average_vendor_score",
    ):
        writer.writerow([key, report[key]])
    writer.writerow([])
    writer.writerow(["Executive Narrative", report["narrative"]])
    writer.writerow([])
    writer.writerow(["Priority Actions"])
    for priority in report["priorities"]:
        writer.writerow([priority])

    filename = f'qualicore-{report["project_code"] or "portfolio"}-assurance-report.csv'.lower()
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
