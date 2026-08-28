from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..access_control import apply_project_scope, require_project_access
from ..activity import audit, notify
from ..database import get_db
from ..models import Project, Risk, RiskStatus, Role, User, WorkflowEntity, WorkflowEvent
from ..schemas import RiskCreate, RiskHeatmapCell, RiskOut, RiskUpdate, WorkflowAction
from ..security import get_current_user, require_roles

router = APIRouter(prefix="/risks", tags=["Risks"])

def get_item(db, id, user):
    item = db.scalar(select(Risk).where(Risk.id == id, Risk.organization_id == user.organization_id))
    if not item: raise HTTPException(404, "Risk not found")
    require_project_access(db, user, item.project_id)
    return item

@router.get("", response_model=list[RiskOut])
def list_items(project_id: str | None = None, status: RiskStatus | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = apply_project_scope(select(Risk), Risk, db, user)
    if project_id:
        require_project_access(db, user, project_id); query = query.where(Risk.project_id == project_id)
    if status: query = query.where(Risk.status == status)
    return db.scalars(query.order_by(Risk.score.desc(), Risk.created_at.desc())).all()

@router.get("/heatmap", response_model=list[RiskHeatmapCell])
def heatmap(project_id: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = apply_project_scope(select(Risk.probability, Risk.impact, func.count(Risk.id)), Risk, db, user).where(Risk.status != RiskStatus.CLOSED)
    if project_id:
        require_project_access(db, user, project_id); query = query.where(Risk.project_id == project_id)
    rows = db.execute(query.group_by(Risk.probability, Risk.impact)).all()
    return [dict(probability=p, impact=i, count=c) for p, i, c in rows]

@router.get("/{id}", response_model=RiskOut)
def detail(id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)): return get_item(db, id, user)

@router.post("", response_model=RiskOut, status_code=201)
def create(body: RiskCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN, Role.QA_MANAGER, Role.QA_ENGINEER))):
    require_project_access(db, user, body.project_id)
    if not db.scalar(select(Project).where(Project.id == body.project_id, Project.organization_id == user.organization_id)): raise HTTPException(404, "Project not found")
    item = Risk(**body.model_dump(), score=body.probability * body.impact, organization_id=user.organization_id, created_by=user.id)
    db.add(item); db.flush(); audit(db, user, "CREATE", "RISK", item.id, f"Created risk: {item.title}")
    if item.score >= 15: notify(db, user, "High project risk", f"{item.title} score {item.score}", "RISK", item.id)
    db.commit(); db.refresh(item); return item

@router.patch("/{id}", response_model=RiskOut)
def update(id: str, body: RiskUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN, Role.QA_MANAGER, Role.QA_ENGINEER))):
    item = get_item(db, id, user)
    if item.status == RiskStatus.CLOSED: raise HTTPException(400, "Closed risk cannot be edited")
    for key, value in body.model_dump(exclude_unset=True).items(): setattr(item, key, value)
    item.score = item.probability * item.impact
    if item.mitigation and item.status == RiskStatus.OPEN: item.status = RiskStatus.MITIGATING
    audit(db, user, "UPDATE", "RISK", item.id, f"Updated risk: {item.title}")
    db.commit(); db.refresh(item); return item

@router.post("/{id}/close", response_model=RiskOut)
def close(id: str, body: WorkflowAction, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN, Role.QA_MANAGER))):
    item = get_item(db, id, user)
    if item.status == RiskStatus.CLOSED: return item
    if not item.mitigation: raise HTTPException(400, "Mitigation required before closure")
    old = item.status.value; item.status = RiskStatus.CLOSED; item.closed_at = datetime.now(timezone.utc)
    db.add(WorkflowEvent(organization_id=user.organization_id, entity_type=WorkflowEntity.RISK, entity_id=item.id, from_status=old, to_status="CLOSED", comment=body.comment, actor_id=user.id))
    audit(db, user, "CLOSE", "RISK", item.id, f"Closed risk: {item.title}")
    db.commit(); db.refresh(item); return item
