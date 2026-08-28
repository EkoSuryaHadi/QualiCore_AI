from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..access_control import project_ids_for_user, require_project_access
from ..copilot_engine import SUGGESTED_QUESTIONS, answer_question
from ..database import get_db
from ..models import Project, User
from ..security import get_current_user

router = APIRouter(prefix="/copilot", tags=["QualiCore Copilot"])

class CopilotRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1200)
    project_id: str | None = None

@router.get("/suggestions")
def suggestions(user: User = Depends(get_current_user)):
    return {"suggested_questions": SUGGESTED_QUESTIONS}

@router.post("/ask")
def ask(payload: CopilotRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if payload.project_id:
        project = db.get(Project, payload.project_id)
        if not project or project.organization_id != user.organization_id:
            raise HTTPException(404, "Project not found")
        require_project_access(db, user, payload.project_id)
        return answer_question(db, user.organization_id, payload.question, payload.project_id)
    visible = project_ids_for_user(db, user)
    return answer_question(db, user.organization_id, payload.question, None, visible)
