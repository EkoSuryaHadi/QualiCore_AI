from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..access_control import project_ids_for_user
from ..dashboard_schemas import ExecutiveDashboardOut
from ..dashboard_service import executive_dashboard
from ..database import get_db
from ..models import User
from ..schemas import DashboardOut
from ..security import get_current_user
from ..services import dashboard

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardOut)
def summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return dashboard(db, user.organization_id, project_ids_for_user(db, user))

@router.get("/executive", response_model=ExecutiveDashboardOut)
def executive(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return executive_dashboard(db, user.organization_id, project_ids_for_user(db, user))
