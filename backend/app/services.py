from datetime import date
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .models import Inspection, InspectionResult, NCR, Project, ProjectStatus, PunchItem, WorkflowStatus

def dashboard(db:Session, org:str):
    scalar=lambda stmt: db.scalar(stmt) or 0
    total_projects=scalar(select(func.count()).select_from(Project).where(Project.organization_id==org))
    active_projects=scalar(select(func.count()).select_from(Project).where(Project.organization_id==org,Project.status==ProjectStatus.ACTIVE))
    total_inspections=scalar(select(func.count()).select_from(Inspection).where(Inspection.organization_id==org))
    failed_inspections=scalar(select(func.count()).select_from(Inspection).where(Inspection.organization_id==org,Inspection.result==InspectionResult.FAIL))
    open_ncr=scalar(select(func.count()).select_from(NCR).where(NCR.organization_id==org,NCR.status!=WorkflowStatus.CLOSED))
    open_punch=scalar(select(func.count()).select_from(PunchItem).where(PunchItem.organization_id==org,PunchItem.status!=WorkflowStatus.CLOSED))
    overdue_punch=scalar(select(func.count()).select_from(PunchItem).where(PunchItem.organization_id==org,PunchItem.status!=WorkflowStatus.CLOSED,PunchItem.due_date<date.today()))
    penalty=(failed_inspections*2)+(open_ncr*3)+open_punch+(overdue_punch*2)
    quality_score=max(0.0,round(100-float(penalty),1))
    return dict(total_projects=total_projects,active_projects=active_projects,total_inspections=total_inspections,failed_inspections=failed_inspections,open_ncr=open_ncr,open_punch=open_punch,overdue_punch=overdue_punch,quality_score=quality_score)
