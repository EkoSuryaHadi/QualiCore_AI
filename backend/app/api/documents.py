from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..access_control import can_access_project, project_ids_for_user, require_membership_roles
from ..activity import audit,notify
from ..database import get_db
from ..identity_models import MembershipRole
from ..models import Document,DocumentStatus,Project,User,WorkflowEntity,WorkflowEvent
from ..schemas import DocumentCreate,DocumentOut,DocumentUpdate,WorkflowAction,WorkflowEventOut
from ..security import get_current_user
router=APIRouter(prefix='/documents',tags=['Documents'])
def get_item(db,id,org,user=None):
 x=db.scalar(select(Document).where(Document.id==id,Document.organization_id==org));
 if not x:raise HTTPException(404,'Document not found')
 if user is not None and not can_access_project(db,user,x.project_id):raise HTTPException(403,'Project access not assigned')
 return x
@router.get('',response_model=list[DocumentOut])
def list_docs(project_id:str|None=None,status:DocumentStatus|None=None,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
 q=select(Document).where(Document.organization_id==user.organization_id)
 allowed=project_ids_for_user(db,user)
 if project_id:
  if not can_access_project(db,user,project_id):raise HTTPException(403,'Project access not assigned')
  q=q.where(Document.project_id==project_id)
 elif allowed is not None:q=q.where(Document.project_id.in_(allowed)) if allowed else q.where(False)
 if status:q=q.where(Document.status==status)
 return db.scalars(q.order_by(Document.updated_at.desc())).all()
@router.get('/{id}',response_model=DocumentOut)
def detail(id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
 return get_item(db,id,user.organization_id,user)
@router.post('',response_model=DocumentOut,status_code=201)
def create(b:DocumentCreate,db:Session=Depends(get_db),user:User=Depends(require_membership_roles(MembershipRole.ORGANIZATION_ADMIN,MembershipRole.QA_MANAGER,MembershipRole.QA_ENGINEER,MembershipRole.DOCUMENT_CONTROLLER))):
 if not db.scalar(select(Project).where(Project.id==b.project_id,Project.organization_id==user.organization_id)):raise HTTPException(404,'Project not found')
 if not can_access_project(db,user,b.project_id):raise HTTPException(403,'Project access not assigned')
 if db.scalar(select(Document).where(Document.organization_id==user.organization_id,Document.document_no==b.document_no)):raise HTTPException(409,'Document number already exists')
 x=Document(**b.model_dump(),organization_id=user.organization_id,created_by=user.id);db.add(x)
 try:
  db.flush();audit(db,user,'CREATE','DOCUMENT',x.id,f'Created {x.document_no} Rev {x.revision}');db.commit();db.refresh(x);return x
 except IntegrityError:
  db.rollback();raise HTTPException(409,'Document number already exists')
@router.patch('/{id}',response_model=DocumentOut)
def update(id:str,b:DocumentUpdate,db:Session=Depends(get_db),user:User=Depends(require_membership_roles(MembershipRole.ORGANIZATION_ADMIN,MembershipRole.QA_MANAGER,MembershipRole.QA_ENGINEER,MembershipRole.DOCUMENT_CONTROLLER))):
 x=get_item(db,id,user.organization_id,user)
 if x.status not in [DocumentStatus.DRAFT,DocumentStatus.REJECTED]:raise HTTPException(400,'Only draft/rejected documents can be edited')
 for k,v in b.model_dump(exclude_unset=True).items():setattr(x,k,v)
 audit(db,user,'UPDATE','DOCUMENT',x.id,f'Updated {x.document_no}');db.commit();db.refresh(x);return x

def transition(db,user,x,to,comment):
 old=x.status.value;x.status=to;db.add(WorkflowEvent(organization_id=user.organization_id,entity_type=WorkflowEntity.DOCUMENT,entity_id=x.id,from_status=old,to_status=to.value,comment=comment,actor_id=user.id));audit(db,user,'WORKFLOW','DOCUMENT',x.id,f'{old} -> {to.value}')
@router.post('/{id}/submit',response_model=DocumentOut)
def submit(id:str,b:WorkflowAction,db:Session=Depends(get_db),user:User=Depends(require_membership_roles(MembershipRole.ORGANIZATION_ADMIN,MembershipRole.QA_MANAGER,MembershipRole.QA_ENGINEER,MembershipRole.DOCUMENT_CONTROLLER))):
 x=get_item(db,id,user.organization_id,user)
 if x.status not in [DocumentStatus.DRAFT,DocumentStatus.REJECTED]:raise HTTPException(400,'Document cannot be submitted from current status')
 transition(db,user,x,DocumentStatus.IN_REVIEW,b.comment);db.commit();db.refresh(x);return x
@router.post('/{id}/approve',response_model=DocumentOut)
def approve(id:str,b:WorkflowAction,db:Session=Depends(get_db),user:User=Depends(require_membership_roles(MembershipRole.ORGANIZATION_ADMIN,MembershipRole.QA_MANAGER))):
 x=get_item(db,id,user.organization_id,user)
 if x.status!=DocumentStatus.IN_REVIEW:raise HTTPException(400,'Only documents in review can be approved')
 transition(db,user,x,DocumentStatus.APPROVED,b.comment);notify(db,user,'Document approved',f'{x.document_no} Rev {x.revision} approved','DOCUMENT',x.id);db.commit();db.refresh(x);return x
@router.post('/{id}/reject',response_model=DocumentOut)
def reject(id:str,b:WorkflowAction,db:Session=Depends(get_db),user:User=Depends(require_membership_roles(MembershipRole.ORGANIZATION_ADMIN,MembershipRole.QA_MANAGER))):
 x=get_item(db,id,user.organization_id,user)
 if x.status!=DocumentStatus.IN_REVIEW:raise HTTPException(400,'Only documents in review can be rejected')
 transition(db,user,x,DocumentStatus.REJECTED,b.comment);notify(db,user,'Document rejected',f'{x.document_no} requires revision','DOCUMENT',x.id);db.commit();db.refresh(x);return x
@router.get('/{id}/history',response_model=list[WorkflowEventOut])
def history(id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
 get_item(db,id,user.organization_id,user);return db.scalars(select(WorkflowEvent).where(WorkflowEvent.organization_id==user.organization_id,WorkflowEvent.entity_type==WorkflowEntity.DOCUMENT,WorkflowEvent.entity_id==id).order_by(WorkflowEvent.created_at)).all()
