from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..activity import audit,notify
from ..database import get_db
from ..models import NCR,NCRSeverity,Project,Role,User,WorkflowStatus
from ..schemas import NCRClose,NCRCreate,NCROut,NCRUpdate
from ..security import get_current_user,require_roles
router=APIRouter(prefix='/ncrs',tags=['NCR'])
def get_item(db,id,org):
 x=db.scalar(select(NCR).where(NCR.id==id,NCR.organization_id==org));
 if not x:raise HTTPException(404,'NCR not found')
 return x
@router.get('',response_model=list[NCROut])
def list_items(project_id:str|None=None,status:WorkflowStatus|None=None,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
 q=select(NCR).where(NCR.organization_id==user.organization_id)
 if project_id:q=q.where(NCR.project_id==project_id)
 if status:q=q.where(NCR.status==status)
 return db.scalars(q.order_by(NCR.created_at.desc())).all()
@router.get('/{id}',response_model=NCROut)
def detail(id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):return get_item(db,id,user.organization_id)
@router.post('',response_model=NCROut,status_code=201)
def create(b:NCRCreate,db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN,Role.QA_MANAGER,Role.QA_ENGINEER))):
 if not db.scalar(select(Project).where(Project.id==b.project_id,Project.organization_id==user.organization_id)):raise HTTPException(404,'Project not found')
 x=NCR(**b.model_dump(),organization_id=user.organization_id,raised_by=user.id);db.add(x);db.flush();audit(db,user,'CREATE','NCR',x.id,f'Created {x.ncr_no}');
 if x.severity in [NCRSeverity.HIGH,NCRSeverity.CRITICAL]:notify(db,user,'Priority NCR created',f'{x.ncr_no}: {x.title}','NCR',x.id)
 db.commit();db.refresh(x);return x
@router.patch('/{id}',response_model=NCROut)
def update(id:str,b:NCRUpdate,db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN,Role.QA_MANAGER,Role.QA_ENGINEER))):
 x=get_item(db,id,user.organization_id)
 if x.status==WorkflowStatus.CLOSED:raise HTTPException(400,'Closed NCR cannot be edited')
 for k,v in b.model_dump(exclude_unset=True).items():setattr(x,k,v)
 if x.root_cause or x.corrective_action:x.status=WorkflowStatus.IN_PROGRESS
 audit(db,user,'UPDATE','NCR',x.id,f'Updated {x.ncr_no}');db.commit();db.refresh(x);return x
@router.post('/{id}/close',response_model=NCROut)
def close(id:str,b:NCRClose,db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN,Role.QA_MANAGER))):
 x=get_item(db,id,user.organization_id)
 if not (x.root_cause and x.corrective_action):raise HTTPException(400,'Root cause and corrective action are required before closure')
 x.status=WorkflowStatus.CLOSED;x.closed_at=datetime.now(timezone.utc);audit(db,user,'CLOSE','NCR',x.id,f'Closed {x.ncr_no}');notify(db,user,'NCR closed',f'{x.ncr_no} has been closed','NCR',x.id);db.commit();db.refresh(x);return x
