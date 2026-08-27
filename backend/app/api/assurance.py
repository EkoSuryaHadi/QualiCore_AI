from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..assurance_engine import analyze_portfolio
from ..database import get_db
from ..models import Project, User
from ..security import get_current_user

router = APIRouter(prefix="/assurance", tags=["AI Assurance"])


@router.get("/analyze")
def analyze(
    project_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if project_id:
        project = db.get(Project, project_id)
        if not project or project.organization_id != user.organization_id:
            raise HTTPException(404, "Project not found")
    return analyze_portfolio(db, user.organization_id, project_id)
