from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..activity import audit, notify
from ..database import get_db
from ..models import Project, PunchItem, Role, User, WorkflowStatus
from ..schemas import PunchCreate, PunchOut, PunchUpdate
from ..security import get_current_user, require_roles

router = APIRouter(prefix="/punch", tags=["Punchlist"])


def get_item(db: Session, item_id: str, org: str) -> PunchItem:
    item = db.scalar(
        select(PunchItem).where(
            PunchItem.id == item_id,
            PunchItem.organization_id == org,
        )
    )
    if not item:
        raise HTTPException(404, "Punch item not found")
    return item


def label(item: PunchItem) -> str:
    return f"Punch {item.id[:8]}"


@router.get("", response_model=list[PunchOut])
def list_items(
    project_id: str | None = None,
    status: WorkflowStatus | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(PunchItem).where(PunchItem.organization_id == user.organization_id)
    if project_id:
        query = query.where(PunchItem.project_id == project_id)
    if status:
        query = query.where(PunchItem.status == status)
    return db.scalars(query.order_by(PunchItem.created_at.desc())).all()


@router.get("/{item_id}", response_model=PunchOut)
def detail(
    item_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_item(db, item_id, user.organization_id)


@router.post("", response_model=PunchOut, status_code=201)
def create(
    body: PunchCreate,
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

    item = PunchItem(
        **body.model_dump(),
        organization_id=user.organization_id,
        created_by=user.id,
    )
    db.add(item)
    db.flush()
    audit(db, user, "CREATE", "PUNCH", item.id, f"Created {label(item)}")
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=PunchOut)
def update(
    item_id: str,
    body: PunchUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.QA_MANAGER, Role.QA_ENGINEER)),
):
    item = get_item(db, item_id, user.organization_id)
    if item.status == WorkflowStatus.CLOSED:
        raise HTTPException(400, "Closed punch item cannot be edited")

    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(item, key, value)

    audit(db, user, "UPDATE", "PUNCH", item.id, f"Updated {label(item)}")
    db.commit()
    db.refresh(item)
    return item


@router.post("/{item_id}/close", response_model=PunchOut)
def close(
    item_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.QA_MANAGER)),
):
    item = get_item(db, item_id, user.organization_id)
    if item.status == WorkflowStatus.CLOSED:
        return item

    item.status = WorkflowStatus.CLOSED
    item.closed_at = datetime.now(timezone.utc)
    audit(db, user, "CLOSE", "PUNCH", item.id, f"Closed {label(item)}")
    notify(db, user, "Punch item closed", f"{label(item)} closed", "PUNCH", item.id)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def delete(
    item_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.QA_MANAGER)),
):
    item = get_item(db, item_id, user.organization_id)
    audit(db, user, "DELETE", "PUNCH", item.id, f"Deleted {label(item)}")
    db.delete(item)
    db.commit()
    return Response(status_code=204)
