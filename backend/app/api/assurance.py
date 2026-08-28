from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..access_control import project_ids_for_user, require_project_access
from ..assurance_engine import analyze_portfolio
from ..database import get_db
from ..models import Project, User
from ..scoped_assurance import analyze_visible_projects
from ..security import get_current_user

router = APIRouter(prefix="/assurance", tags=["AI Assurance"])


@router.get("/analyze")
def analyze(project_id: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if project_id:
        project = db.get(Project, project_id)
        if not project or project.organization_id != user.organization_id:
            raise HTTPException(404, "Project not found")
        require_project_access(db, user, project_id)
        return analyze_portfolio(db, user.organization_id, project_id)

    allowed = project_ids_for_user(db, user)
    if allowed is None:
        return analyze_portfolio(db, user.organization_id)
    return analyze_visible_projects(db, user.organization_id, allowed)
