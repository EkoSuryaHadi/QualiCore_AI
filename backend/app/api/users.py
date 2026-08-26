from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Role, User
from ..schemas import UserCreate, UserOut
from ..security import hash_password, require_roles
router=APIRouter(prefix="/users",tags=["Users"])

@router.get("",response_model=list[UserOut])
def list_users(db:Session=Depends(get_db),admin:User=Depends(require_roles(Role.ADMIN))):
    return db.scalars(select(User).where(User.organization_id==admin.organization_id).order_by(User.full_name)).all()

@router.post("",response_model=UserOut,status_code=201)
def create_user(body:UserCreate,db:Session=Depends(get_db),admin:User=Depends(require_roles(Role.ADMIN))):
    if db.scalar(select(User).where(User.email==body.email.lower())): raise HTTPException(409,"Email already registered")
    user=User(organization_id=admin.organization_id,email=body.email.lower(),full_name=body.full_name,password_hash=hash_password(body.password),role=body.role)
    db.add(user); db.commit(); db.refresh(user); return user
