from datetime import datetime, timezone
from fastapi import APIRouter,Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import func,select
from sqlalchemy.orm import Session
import csv,io
from ..database import get_db
from ..models import Document,DocumentStatus,Inspection,InspectionResult,NCR,Project,PunchItem,Risk,RiskStatus,User,WorkflowStatus
from ..security import get_current_user
from ..services import dashboard
router=APIRouter(prefix='/reports',tags=['Reports'])
@router.get('/executive')
def executive(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
 d=dashboard(db,user.organization_id);scalar=lambda q:db.scalar(q) or 0
 return {**d,'open_documents':scalar(select(func.count()).select_from(Document).where(Document.organization_id==user.organization_id,Document.status!=DocumentStatus.APPROVED)),'high_risks':scalar(select(func.count()).select_from(Risk).where(Risk.organization_id==user.organization_id,Risk.status!=RiskStatus.CLOSED,Risk.score>=15)),'generated_at':datetime.now(timezone.utc)}
@router.get('/executive.csv')
def executive_csv(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
 d=executive(db,user);s=io.StringIO();w=csv.writer(s);w.writerow(['Metric','Value']);[w.writerow([k,v]) for k,v in d.items()];return StreamingResponse(iter([s.getvalue()]),media_type='text/csv',headers={'Content-Disposition':'attachment; filename=qualicore-executive-report.csv'})
