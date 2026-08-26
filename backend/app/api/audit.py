from fastapi import APIRouter,Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import AuditLog,Role,User
from ..schemas import AuditOut
from ..security import require_roles
router=APIRouter(prefix='/audit',tags=['Audit'])
@router.get('',response_model=list[AuditOut])
def logs(entity_type:str|None=None,entity_id:str|None=None,db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN,Role.QA_MANAGER))):
 q=select(AuditLog).where(AuditLog.organization_id==user.organization_id)
 if entity_type:q=q.where(AuditLog.entity_type==entity_type)
 if entity_id:q=q.where(AuditLog.entity_id==entity_id)
 return db.scalars(q.order_by(AuditLog.created_at.desc()).limit(200)).all()
