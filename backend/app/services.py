from datetime import date
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .models import Inspection, InspectionResult, NCR, Project, ProjectStatus, PunchItem, WorkflowStatus

def dashboard(db:Session, org:str, project_ids:list[str]|None=None):
    scalar=lambda stmt: db.scalar(stmt) or 0
    def project_scope(stmt, column):
        if project_ids is None: return stmt
        return stmt.where(column.in_(project_ids) if project_ids else False)
    total_projects=scalar(project_scope(select(func.count()).select_from(Project).where(Project.organization_id==org),Project.id))
    active_projects=scalar(project_scope(select(func.count()).select_from(Project).where(Project.organization_id==org,Project.status==ProjectStatus.ACTIVE),Project.id))
    total_inspections=scalar(project_scope(select(func.count()).select_from(Inspection).where(Inspection.organization_id==org),Inspection.project_id))
    failed_inspections=scalar(project_scope(select(func.count()).select_from(Inspection).where(Inspection.organization_id==org,Inspection.result==InspectionResult.FAIL),Inspection.project_id))
    open_ncr=scalar(project_scope(select(func.count()).select_from(NCR).where(NCR.organization_id==org,NCR.status!=WorkflowStatus.CLOSED),NCR.project_id))
    open_punch=scalar(project_scope(select(func.count()).select_from(PunchItem).where(PunchItem.organization_id==org,PunchItem.status!=WorkflowStatus.CLOSED),PunchItem.project_id))
    overdue_punch=scalar(project_scope(select(func.count()).select_from(PunchItem).where(PunchItem.organization_id==org,PunchItem.status!=WorkflowStatus.CLOSED,PunchItem.due_date<date.today()),PunchItem.project_id))
    penalty=(failed_inspections*2)+(open_ncr*3)+open_punch+(overdue_punch*2)
    quality_score=max(0.0,round(100-float(penalty),1))
    return dict(total_projects=total_projects,active_projects=active_projects,total_inspections=total_inspections,failed_inspections=failed_inspections,open_ncr=open_ncr,open_punch=open_punch,overdue_punch=overdue_punch,quality_score=quality_score)
