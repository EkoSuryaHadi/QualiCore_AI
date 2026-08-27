from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..activity import audit
from ..database import get_db
from ..models import Inspection, InspectionResult, Project, Role, User
from ..schemas import InspectionCreate, InspectionOut, InspectionUpdate
from ..security import get_current_user, require_roles

router = APIRouter(prefix="/inspections", tags=["Inspections"])


def get_item(db: Session, item_id: str, organization_id: str) -> Inspection:
    item = db.scalar(
        select(Inspection).where(
            Inspection.id == item_id,
            Inspection.organization_id == organization_id,
        )
    )
    if not item:
        raise HTTPException(404, "Inspection not found")
    return item


@router.get("", response_model=list[InspectionOut])
def list_items(
    project_id: str | None = None,
    result: InspectionResult | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Inspection).where(Inspection.organization_id == user.organization_id)
    if project_id:
        query = query.where(Inspection.project_id == project_id)
    if result:
        query = query.where(Inspection.result == result)
    return db.scalars(query.order_by(Inspection.inspection_date.desc(), Inspection.created_at.desc())).all()


@router.get("/{item_id}", response_model=InspectionOut)
def detail(
    item_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_item(db, item_id, user.organization_id)


@router.post("", response_model=InspectionOut, status_code=201)
def create(
    body: InspectionCreate,
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

    item = Inspection(
        **body.model_dump(),
        organization_id=user.organization_id,
        created_by=user.id,
    )
    db.add(item)
    db.flush()
    audit(
        db,
        user,
        "CREATE",
        "INSPECTION",
        item.id,
        f"Created inspection: {item.inspection_type} ({item.result.value})",
    )
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=InspectionOut)
def update(
    item_id: str,
    body: InspectionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.QA_MANAGER, Role.QA_ENGINEER)),
):
    item = get_item(db, item_id, user.organization_id)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    audit(
        db,
        user,
        "UPDATE",
        "INSPECTION",
        item.id,
        f"Updated inspection: {item.inspection_type} ({item.result.value})",
    )
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
    audit(
        db,
        user,
        "DELETE",
        "INSPECTION",
        item.id,
        f"Deleted inspection: {item.inspection_type}",
    )
    db.delete(item)
    db.commit()
    return Response(status_code=204)
