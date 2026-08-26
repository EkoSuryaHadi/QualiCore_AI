from fastapi import APIRouter,Depends,HTTPException,Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..activity import audit
from ..database import get_db
from ..models import Inspection,Project,Role,User
from ..schemas import InspectionCreate,InspectionOut,InspectionUpdate
from ..security import get_current_user,require_roles
router=APIRouter(prefix='/inspections',tags=['Inspections'])
def get_item(db,id,org):
 x=db.scalar(select(Inspection).where(Inspection.id==id,Inspection.organization_id==org));
 if not x:raise HTTPException(404,'Inspection not found')
 return x
@router.get('',response_model=list[InspectionOut])
def list_items(project_id:str|None=None,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
 q=select(Inspection).where(Inspection.organization_id==user.organization_id)
 if project_id:q=q.where(Inspection.project_id==project_id)
 return db.scalars(q.order_by(Inspection.inspection_date.desc())).all()
@router.get('/{item_id}',response_model=InspectionOut)
def detail(item_id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):return get_item(db,item_id,user.organization_id)
@router.post('',response_model=InspectionOut,status_code=201)
def create(b:InspectionCreate,db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN,Role.QA_MANAGER,Role.QA_ENGINEER))):
 if not db.scalar(select(Project).where(Project.id==b.project_id,Project.organization_id==user.organization_id)):raise HTTPException(404,'Project not found')
 x=Inspection(**b.model_dump(),organization_id=user.organization_id,inspector_id=user.id);db.add(x);db.flush();audit(db,user,'CREATE','INSPECTION',x.id,f'Created inspection: {x.title}');db.commit();db.refresh(x);return x
@router.patch('/{item_id}',response_model=InspectionOut)
def update(item_id:str,b:InspectionUpdate,db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN,Role.QA_MANAGER,Role.QA_ENGINEER))):
 x=get_item(db,item_id,user.organization_id)
 for k,v in b.model_dump(exclude_unset=True).items():setattr(x,k,v)
 audit(db,user,'UPDATE','INSPECTION',x.id,f'Updated inspection: {x.title}');db.commit();db.refresh(x);return x
@router.delete('/{item_id}',status_code=204)
def delete(item_id:str,db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN,Role.QA_MANAGER))):
 x=get_item(db,item_id,user.organization_id);audit(db,user,'DELETE','INSPECTION',x.id,f'Deleted inspection: {x.title}');db.delete(x);db.commit();return Response(status_code=204)
