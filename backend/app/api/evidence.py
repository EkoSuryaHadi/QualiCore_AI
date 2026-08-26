from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter,Depends,File,HTTPException,UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..activity import audit
from ..config import settings
from ..database import get_db
from ..models import Evidence,EvidenceEntity,Inspection,NCR,PunchItem,Role,User
from ..schemas import EvidenceOut
from ..security import get_current_user,require_roles
router=APIRouter(prefix='/evidence',tags=['Evidence'])
MAX=10*1024*1024; ALLOWED={'image/jpeg','image/png','application/pdf'}
def entity(db,t,id,org):
 model={'INSPECTION':Inspection,'NCR':NCR,'PUNCH':PunchItem}[t.value]
 x=db.scalar(select(model).where(model.id==id,model.organization_id==org))
 if not x: raise HTTPException(404,'Entity not found')
 return x
@router.get('/{entity_type}/{entity_id}',response_model=list[EvidenceOut])
def list_e(entity_type:EvidenceEntity,entity_id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
 entity(db,entity_type,entity_id,user.organization_id);return db.scalars(select(Evidence).where(Evidence.organization_id==user.organization_id,Evidence.entity_type==entity_type,Evidence.entity_id==entity_id).order_by(Evidence.created_at.desc())).all()
@router.post('/{entity_type}/{entity_id}',response_model=EvidenceOut,status_code=201)
async def upload(entity_type:EvidenceEntity,entity_id:str,file:UploadFile=File(...),db:Session=Depends(get_db),user:User=Depends(require_roles(Role.ADMIN,Role.QA_MANAGER,Role.QA_ENGINEER))):
 x=entity(db,entity_type,entity_id,user.organization_id);data=await file.read(MAX+1)
 if len(data)>MAX:raise HTTPException(413,'File too large')
 if file.content_type not in ALLOWED:raise HTTPException(415,'Only JPG, PNG and PDF evidence is allowed')
 d=Path(settings.upload_dir);d.mkdir(parents=True,exist_ok=True);ext=Path(file.filename or '').suffix.lower();name=f'{uuid4()}{ext}';(d/name).write_bytes(data)
 e=Evidence(organization_id=user.organization_id,project_id=x.project_id,entity_type=entity_type,entity_id=entity_id,file_name=file.filename or name,stored_name=name,content_type=file.content_type,size_bytes=len(data),uploaded_by=user.id);db.add(e);db.flush();audit(db,user,'UPLOAD_EVIDENCE',entity_type.value,entity_id,f'Uploaded {e.file_name}');db.commit();db.refresh(e);return e
