from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..activity import audit, notify
from ..database import get_db
from ..models import Project, Role, User
from ..security import get_current_user, require_roles
from ..vendor_models import VendorQuality, VendorStatus
from ..vendor_schemas import VendorCreate, VendorOut, VendorUpdate

router = APIRouter(prefix="/vendors", tags=["Vendor Quality"])


def get_item(db: Session, vendor_id: str, org: str) -> VendorQuality:
    item = db.scalar(
        select(VendorQuality).where(
            VendorQuality.id == vendor_id,
            VendorQuality.organization_id == org,
        )
    )
    if not item:
        raise HTTPException(404, "Vendor quality record not found")
    return item


def calculate_overall(item: VendorQuality) -> float:
    score = (
        item.quality_score * 0.35
        + item.delivery_score * 0.20
        + item.documentation_score * 0.20
        + item.inspection_score * 0.25
    )
    score -= min(item.ncr_count * 2.0, 20.0)
    return round(max(0.0, min(100.0, score)), 1)


@router.get("", response_model=list[VendorOut])
def list_items(
    project_id: str | None = None,
    status: VendorStatus | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(VendorQuality).where(VendorQuality.organization_id == user.organization_id)
    if project_id:
        query = query.where(VendorQuality.project_id == project_id)
    if status:
        query = query.where(VendorQuality.status == status)
    return db.scalars(query.order_by(VendorQuality.overall_score.asc(), VendorQuality.vendor_name.asc())).all()


@router.get("/{vendor_id}", response_model=VendorOut)
def detail(
    vendor_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_item(db, vendor_id, user.organization_id)


@router.post("", response_model=VendorOut, status_code=201)
def create(
    body: VendorCreate,
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

    item = VendorQuality(
        **body.model_dump(),
        organization_id=user.organization_id,
        created_by=user.id,
    )
    item.overall_score = calculate_overall(item)
    db.add(item)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Vendor code already exists for this project")

    audit(db, user, "CREATE", "VENDOR", item.id, f"Created vendor quality record: {item.vendor_name}")
    if item.overall_score < 70 or item.status in (VendorStatus.WATCHLIST, VendorStatus.SUSPENDED):
        notify(db, user, "Vendor quality attention", f"{item.vendor_name} score {item.overall_score}", "VENDOR", item.id)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{vendor_id}", response_model=VendorOut)
def update(
    vendor_id: str,
    body: VendorUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.QA_MANAGER, Role.QA_ENGINEER)),
):
    item = get_item(db, vendor_id, user.organization_id)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    item.overall_score = calculate_overall(item)
    audit(db, user, "UPDATE", "VENDOR", item.id, f"Updated vendor quality record: {item.vendor_name}")
    if item.overall_score < 70 and item.status == VendorStatus.APPROVED:
        item.status = VendorStatus.WATCHLIST
        notify(db, user, "Vendor moved to watchlist", f"{item.vendor_name} score {item.overall_score}", "VENDOR", item.id)
    db.commit()
    db.refresh(item)
    return item
