from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException,Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..activity import audit,notify
from ..database import get_db
from ..models import Project,PunchItem,Role,User,WorkflowStatus
from ..schemas import PunchCreate,PunchOut,PunchUpdate
from ..security import get_current_user,require_roles
router=APIRouter(prefix='/punch',tags=['Punchlist'])
def get_item(db,id,org):
 x=db.scalar(select(PunchItem).where(PunchItem.id==id,PunchItem.organization_id==org));
 if not x:raise HTTPException(404,'Punch item not found')
 return x
@router.get('',response_model=list[PunchOut])
def list_items(project_id:str|None=None,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
 q=select(PunchItem).where(PunchItem.organization_id==user.organization_id)
 if project_id:q=q.where(PunchItem.project_id==project_id)
 return db.scalars(q.order_by(PunchItem.created_at.desc())).all()
@router.post('',response_model=PunchOut,status_code=201)
def create(b:PunchCreate,db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN,Role.QA_MANAGER,Role.QA_ENGINEER))):
 if not db.scalar(select(Project).where(Project.id==b.project_id,Project.organization_id==user.organization_id)):raise HTTPException(404,'Project not found')
 x=PunchItem(**b.model_dump(),organization_id=user.organization_id,created_by=user.id);db.add(x);db.flush();audit(db,user,'CREATE','PUNCH',x.id,f'Created {x.punch_no}');db.commit();db.refresh(x);return x
@router.patch('/{item_id}',response_model=PunchOut)
def update(item_id:str,b:PunchUpdate,db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN,Role.QA_MANAGER,Role.QA_ENGINEER))):
 x=get_item(db,item_id,user.organization_id)
 if x.status==WorkflowStatus.CLOSED:raise HTTPException(400,'Closed punch item cannot be edited')
 for k,v in b.model_dump(exclude_unset=True).items():setattr(x,k,v)
 audit(db,user,'UPDATE','PUNCH',x.id,f'Updated {x.punch_no}');db.commit();db.refresh(x);return x
@router.post('/{item_id}/close',response_model=PunchOut)
def close(item_id:str,db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN,Role.QA_MANAGER))):
 x=get_item(db,item_id,user.organization_id);x.status=WorkflowStatus.CLOSED;x.closed_at=datetime.now(timezone.utc);audit(db,user,'CLOSE','PUNCH',x.id,f'Closed {x.punch_no}');notify(db,user,'Punch item closed',f'{x.punch_no} closed','PUNCH',x.id);db.commit();db.refresh(x);return x
@router.delete('/{item_id}',status_code=204)
def delete(item_id:str,db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN,Role.QA_MANAGER))):
 x=get_item(db,item_id,user.organization_id);audit(db,user,'DELETE','PUNCH',x.id,f'Deleted {x.punch_no}');db.delete(x);db.commit();return Response(status_code=204)
