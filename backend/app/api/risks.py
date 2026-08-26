from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..activity import audit, notify
from ..database import get_db
from ..models import Project, Risk, RiskStatus, Role, User, WorkflowEntity, WorkflowEvent
from ..schemas import RiskCreate,RiskHeatmapCell,RiskOut,RiskUpdate,WorkflowAction
from ..security import get_current_user,require_roles
router=APIRouter(prefix='/risks',tags=['Risks'])
def get_item(db,id,org):
 x=db.scalar(select(Risk).where(Risk.id==id,Risk.organization_id==org));
 if not x:raise HTTPException(404,'Risk not found')
 return x
@router.get('',response_model=list[RiskOut])
def list_items(project_id:str|None=None,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
 q=select(Risk).where(Risk.organization_id==user.organization_id)
 if project_id:q=q.where(Risk.project_id==project_id)
 return db.scalars(q.order_by(Risk.score.desc(),Risk.created_at.desc())).all()
@router.post('',response_model=RiskOut,status_code=201)
def create(b:RiskCreate,db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN,Role.QA_MANAGER,Role.QA_ENGINEER))):
 if not db.scalar(select(Project).where(Project.id==b.project_id,Project.organization_id==user.organization_id)):raise HTTPException(404,'Project not found')
 x=Risk(**b.model_dump(),score=b.probability*b.impact,organization_id=user.organization_id,created_by=user.id);db.add(x);db.flush();audit(db,user,'CREATE','RISK',x.id,f'Created risk: {x.title}');
 if x.score>=15:notify(db,user,'High project risk',f'{x.title} score {x.score}','RISK',x.id)
 db.commit();db.refresh(x);return x
@router.patch('/{id}',response_model=RiskOut)
def update(id:str,b:RiskUpdate,db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN,Role.QA_MANAGER,Role.QA_ENGINEER))):
 x=get_item(db,id,user.organization_id);d=b.model_dump(exclude_unset=True)
 for k,v in d.items():setattr(x,k,v)
 x.score=x.probability*x.impact;audit(db,user,'UPDATE','RISK',x.id,f'Updated risk: {x.title}');db.commit();db.refresh(x);return x
@router.post('/{id}/close',response_model=RiskOut)
def close(id:str,b:WorkflowAction,db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN,Role.QA_MANAGER))):
 x=get_item(db,id,user.organization_id)
 if not x.mitigation:raise HTTPException(400,'Mitigation required before closure')
 old=x.status.value;x.status=RiskStatus.CLOSED;x.closed_at=datetime.now(timezone.utc);db.add(WorkflowEvent(organization_id=user.organization_id,entity_type=WorkflowEntity.RISK,entity_id=x.id,from_status=old,to_status='CLOSED',comment=b.comment,actor_id=user.id));audit(db,user,'CLOSE','RISK',x.id,f'Closed risk: {x.title}');db.commit();db.refresh(x);return x
@router.get('/heatmap',response_model=list[RiskHeatmapCell])
def heatmap(project_id:str|None=None,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
 q=select(Risk.probability,Risk.impact,func.count(Risk.id)).where(Risk.organization_id==user.organization_id,Risk.status!=RiskStatus.CLOSED)
 if project_id:q=q.where(Risk.project_id==project_id)
 rows=db.execute(q.group_by(Risk.probability,Risk.impact)).all();return [dict(probability=p,impact=i,count=c) for p,i,c in rows]
