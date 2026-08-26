from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..activity import audit,notify
from ..database import get_db
from ..models import Document,DocumentStatus,Project,Role,User,WorkflowEntity,WorkflowEvent
from ..schemas import DocumentCreate,DocumentOut,DocumentUpdate,WorkflowAction,WorkflowEventOut
from ..security import get_current_user,require_roles
router=APIRouter(prefix='/documents',tags=['Documents'])
def get_item(db,id,org):
 x=db.scalar(select(Document).where(Document.id==id,Document.organization_id==org));
 if not x:raise HTTPException(404,'Document not found')
 return x
@router.get('',response_model=list[DocumentOut])
def list_docs(project_id:str|None=None,status:DocumentStatus|None=None,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
 q=select(Document).where(Document.organization_id==user.organization_id)
 if project_id:q=q.where(Document.project_id==project_id)
 if status:q=q.where(Document.status==status)
 return db.scalars(q.order_by(Document.updated_at.desc())).all()
@router.post('',response_model=DocumentOut,status_code=201)
def create(b:DocumentCreate,db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN,Role.QA_MANAGER,Role.QA_ENGINEER))):
 if not db.scalar(select(Project).where(Project.id==b.project_id,Project.organization_id==user.organization_id)):raise HTTPException(404,'Project not found')
 x=Document(**b.model_dump(),organization_id=user.organization_id,created_by=user.id);db.add(x);db.flush();audit(db,user,'CREATE','DOCUMENT',x.id,f'Created {x.document_no} Rev {x.revision}');db.commit();db.refresh(x);return x
@router.patch('/{id}',response_model=DocumentOut)
def update(id:str,b:DocumentUpdate,db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN,Role.QA_MANAGER,Role.QA_ENGINEER))):
 x=get_item(db,id,user.organization_id)
 if x.status not in [DocumentStatus.DRAFT,DocumentStatus.REJECTED]:raise HTTPException(400,'Only draft/rejected documents can be edited')
 for k,v in b.model_dump(exclude_unset=True).items():setattr(x,k,v)
 audit(db,user,'UPDATE','DOCUMENT',x.id,f'Updated {x.document_no}');db.commit();db.refresh(x);return x

def transition(db,user,x,to,comment):
 old=x.status.value;x.status=to;db.add(WorkflowEvent(organization_id=user.organization_id,entity_type=WorkflowEntity.DOCUMENT,entity_id=x.id,from_status=old,to_status=to.value,comment=comment,actor_id=user.id));audit(db,user,'WORKFLOW','DOCUMENT',x.id,f'{old} -> {to.value}')
@router.post('/{id}/submit',response_model=DocumentOut)
def submit(id:str,b:WorkflowAction,db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN,Role.QA_MANAGER,Role.QA_ENGINEER))):
 x=get_item(db,id,user.organization_id)
 if x.status not in [DocumentStatus.DRAFT,DocumentStatus.REJECTED]:raise HTTPException(400,'Document cannot be submitted from current status')
 transition(db,user,x,DocumentStatus.IN_REVIEW,b.comment);db.commit();db.refresh(x);return x
@router.post('/{id}/approve',response_model=DocumentOut)
def approve(id:str,b:WorkflowAction,db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN,Role.QA_MANAGER))):
 x=get_item(db,id,user.organization_id)
 if x.status!=DocumentStatus.IN_REVIEW:raise HTTPException(400,'Only documents in review can be approved')
 transition(db,user,x,DocumentStatus.APPROVED,b.comment);notify(db,user,'Document approved',f'{x.document_no} Rev {x.revision} approved','DOCUMENT',x.id);db.commit();db.refresh(x);return x
@router.post('/{id}/reject',response_model=DocumentOut)
def reject(id:str,b:WorkflowAction,db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN,Role.QA_MANAGER))):
 x=get_item(db,id,user.organization_id)
 if x.status!=DocumentStatus.IN_REVIEW:raise HTTPException(400,'Only documents in review can be rejected')
 transition(db,user,x,DocumentStatus.REJECTED,b.comment);notify(db,user,'Document rejected',f'{x.document_no} requires revision','DOCUMENT',x.id);db.commit();db.refresh(x);return x
@router.get('/{id}/history',response_model=list[WorkflowEventOut])
def history(id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
 get_item(db,id,user.organization_id);return db.scalars(select(WorkflowEvent).where(WorkflowEvent.organization_id==user.organization_id,WorkflowEvent.entity_type==WorkflowEntity.DOCUMENT,WorkflowEvent.entity_id==id).order_by(WorkflowEvent.created_at)).all()
