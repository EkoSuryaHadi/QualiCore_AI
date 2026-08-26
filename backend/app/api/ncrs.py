from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..activity import audit, notify
from ..database import get_db
from ..models import NCR, Project, Role, Severity, User, WorkflowStatus
from ..schemas import NCRClose, NCRCreate, NCROut, NCRUpdate
from ..security import get_current_user, require_roles

router = APIRouter(prefix="/ncrs", tags=["NCR"])


def get_item(db: Session, id: str, org: str) -> NCR:
    item = db.scalar(select(NCR).where(NCR.id == id, NCR.organization_id == org))
    if not item:
        raise HTTPException(404, "NCR not found")
    return item


@router.get("", response_model=list[NCROut])
def list_items(
    project_id: str | None = None,
    status: WorkflowStatus | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(NCR).where(NCR.organization_id == user.organization_id)
    if project_id:
        query = query.where(NCR.project_id == project_id)
    if status:
        query = query.where(NCR.status == status)
    return db.scalars(query.order_by(NCR.created_at.desc())).all()


@router.get("/{id}", response_model=NCROut)
def detail(
    id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_item(db, id, user.organization_id)


@router.post("", response_model=NCROut, status_code=201)
def create(
    body: NCRCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.QA_MANAGER, Role.QA_ENGINEER)),
):
    project = db.scalar(
        select(Project).where(
            Project.id == body.project_id,
            Project.organization_id == user.organization_id,
        )
    )
    if not project:
        raise HTTPException(404, "Project not found")

    item = NCR(
        **body.model_dump(),
        organization_id=user.organization_id,
        created_by=user.id,
    )
    db.add(item)
    db.flush()
    audit(db, user, "CREATE", "NCR", item.id, f"Created {item.number}")

    if item.severity in (Severity.HIGH, Severity.CRITICAL):
        notify(
            db,
            user,
            "Priority NCR created",
            f"{item.number}: {item.title}",
            "NCR",
            item.id,
        )

    db.commit()
    db.refresh(item)
    return item


@router.patch("/{id}", response_model=NCROut)
def update(
    id: str,
    body: NCRUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.QA_MANAGER, Role.QA_ENGINEER)),
):
    item = get_item(db, id, user.organization_id)
    if item.status == WorkflowStatus.CLOSED:
        raise HTTPException(400, "Closed NCR cannot be edited")

    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(item, key, value)

    if item.root_cause or item.corrective_action:
        item.status = WorkflowStatus.IN_PROGRESS

    audit(db, user, "UPDATE", "NCR", item.id, f"Updated {item.number}")
    db.commit()
    db.refresh(item)
    return item


@router.post("/{id}/close", response_model=NCROut)
def close(
    id: str,
    body: NCRClose,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.QA_MANAGER)),
):
    item = get_item(db, id, user.organization_id)
    if not (item.root_cause and item.corrective_action):
        raise HTTPException(
            400,
            "Root cause and corrective action are required before closure",
        )

    item.status = WorkflowStatus.CLOSED
    item.closed_at = datetime.now(timezone.utc)
    audit(db, user, "CLOSE", "NCR", item.id, f"Closed {item.number}")
    notify(db, user, "NCR closed", f"{item.number} has been closed", "NCR", item.id)
    db.commit()
    db.refresh(item)
    return item
