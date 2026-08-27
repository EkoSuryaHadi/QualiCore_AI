import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..activity import audit
from ..config import settings
from ..database import get_db
from ..models import Evidence, EvidenceEntity, Inspection, NCR, PunchItem, Role, User
from ..schemas import EvidenceOut
from ..security import get_current_user, require_roles

logger = logging.getLogger("qualicore.evidence")
router = APIRouter(prefix="/evidence", tags=["Evidence"])
MAX = 10 * 1024 * 1024
ALLOWED = {"image/jpeg", "image/png", "application/pdf"}


def entity(db, entity_type, entity_id, org):
    model = {"INSPECTION": Inspection, "NCR": NCR, "PUNCH": PunchItem}[entity_type.value]
    item = db.scalar(select(model).where(model.id == entity_id, model.organization_id == org))
    if not item:
        raise HTTPException(404, "Entity not found")
    return item


@router.get("/{entity_type}/{entity_id}", response_model=list[EvidenceOut])
def list_e(
    entity_type: EvidenceEntity,
    entity_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    entity(db, entity_type, entity_id, user.organization_id)
    return db.scalars(
        select(Evidence)
        .where(
            Evidence.organization_id == user.organization_id,
            Evidence.entity_type == entity_type,
            Evidence.entity_id == entity_id,
        )
        .order_by(Evidence.created_at.desc())
    ).all()


@router.post("/{entity_type}/{entity_id}", response_model=EvidenceOut, status_code=201)
async def upload(
    entity_type: EvidenceEntity,
    entity_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.QA_MANAGER, Role.QA_ENGINEER)),
):
    stored_path: Path | None = None
    try:
        item = entity(db, entity_type, entity_id, user.organization_id)
        data = await file.read(MAX + 1)

        if len(data) > MAX:
            raise HTTPException(413, "File too large. Maximum evidence size is 10 MB")
        if file.content_type not in ALLOWED:
            raise HTTPException(415, "Only JPG, PNG and PDF evidence is allowed")
        if not data:
            raise HTTPException(400, "Uploaded file is empty")

        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        ext = Path(file.filename or "").suffix.lower()
        stored_name = f"{uuid4()}{ext}"
        stored_path = upload_dir / stored_name
        stored_path.write_bytes(data)

        evidence = Evidence(
            organization_id=user.organization_id,
            project_id=item.project_id,
            entity_type=entity_type,
            entity_id=entity_id,
            file_name=file.filename or stored_name,
            stored_name=stored_name,
            content_type=file.content_type,
            size_bytes=len(data),
            uploaded_by=user.id,
        )
        db.add(evidence)
        db.flush()
        audit(
            db,
            user,
            "UPLOAD_EVIDENCE",
            entity_type.value,
            entity_id,
            f"Uploaded {evidence.file_name}",
        )
        db.commit()
        db.refresh(evidence)
        return evidence

    except HTTPException:
        db.rollback()
        if stored_path and stored_path.exists():
            stored_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        db.rollback()
        if stored_path and stored_path.exists():
            stored_path.unlink(missing_ok=True)
        logger.exception("Evidence upload failed")
        raise HTTPException(
            status_code=500,
            detail=f"Evidence upload failed: {type(exc).__name__}: {exc}",
        ) from exc
