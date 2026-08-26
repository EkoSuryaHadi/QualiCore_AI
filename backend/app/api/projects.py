from fastapi import APIRouter,Depends,HTTPException,Response
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from ..activity import audit
from ..database import get_db
from ..models import Document,DocumentStatus,Evidence,Inspection,InspectionResult,NCR,NCRSeverity,Project,PunchItem,Risk,RiskStatus,Role,User,WorkflowStatus
from ..schemas import ProjectCreate,ProjectOut,ProjectUpdate,ProjectWorkspaceOut
from ..security import get_current_user,require_roles
router=APIRouter(prefix='/projects',tags=['Projects'])
def get_project(db,id,org):
 p=db.scalar(select(Project).where(Project.id==id,Project.organization_id==org));
 if not p:raise HTTPException(404,'Project not found')
 return p
@router.get('',response_model=list[ProjectOut])
def list_projects(db:Session=Depends(get_db),user:User=Depends(get_current_user)):return db.scalars(select(Project).where(Project.organization_id==user.organization_id).order_by(Project.name)).all()
@router.post('',response_model=ProjectOut,status_code=201)
def create_project(b:ProjectCreate,db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN,Role.QA_MANAGER))):
 if db.scalar(select(Project).where(Project.organization_id==user.organization_id,Project.code==b.code)):raise HTTPException(409,'Project code already exists')
 p=Project(**b.model_dump(),organization_id=user.organization_id);db.add(p);db.flush();audit(db,user,'CREATE','PROJECT',p.id,f'Created {p.code}');db.commit();db.refresh(p);return p
@router.get('/{id}',response_model=ProjectOut)
def detail(id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):return get_project(db,id,user.organization_id)
@router.get('/{id}/workspace',response_model=ProjectWorkspaceOut)
def workspace(id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
 p=get_project(db,id,user.organization_id);scalar=lambda q:db.scalar(q) or 0
 inspections=scalar(select(func.count()).select_from(Inspection).where(Inspection.project_id==id));failed=scalar(select(func.count()).select_from(Inspection).where(Inspection.project_id==id,Inspection.result==InspectionResult.FAIL));passed=scalar(select(func.count()).select_from(Inspection).where(Inspection.project_id==id,Inspection.result==InspectionResult.PASS));score=round(passed/inspections*100,1) if inspections else 100.0
 return dict(project=p,quality_score=score,inspection_count=inspections,failed_inspections=failed,open_ncr=scalar(select(func.count()).select_from(NCR).where(NCR.project_id==id,NCR.status!=WorkflowStatus.CLOSED)),critical_ncr=scalar(select(func.count()).select_from(NCR).where(NCR.project_id==id,NCR.status!=WorkflowStatus.CLOSED,NCR.severity.in_([NCRSeverity.HIGH,NCRSeverity.CRITICAL]))),open_punch=scalar(select(func.count()).select_from(PunchItem).where(PunchItem.project_id==id,PunchItem.status!=WorkflowStatus.CLOSED)),overdue_punch=0,evidence_count=scalar(select(func.count()).select_from(Evidence).where(Evidence.project_id==id)),open_documents=scalar(select(func.count()).select_from(Document).where(Document.project_id==id,Document.status!=DocumentStatus.APPROVED)),high_risks=scalar(select(func.count()).select_from(Risk).where(Risk.project_id==id,Risk.status!=RiskStatus.CLOSED,Risk.score>=15)))
@router.patch('/{id}',response_model=ProjectOut)
def update(id:str,b:ProjectUpdate,db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN,Role.QA_MANAGER))):
 p=get_project(db,id,user.organization_id)
 for k,v in b.model_dump(exclude_unset=True).items():setattr(p,k,v)
 audit(db,user,'UPDATE','PROJECT',p.id,f'Updated {p.code}');db.commit();db.refresh(p);return p
@router.delete('/{id}',status_code=204)
def delete(id:str,db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN))):
 p=get_project(db,id,user.organization_id);audit(db,user,'DELETE','PROJECT',p.id,f'Deleted {p.code}');db.delete(p);db.commit();return Response(status_code=204)
