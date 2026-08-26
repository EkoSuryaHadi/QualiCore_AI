from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import LoginIn, TokenOut, UserOut
from ..security import create_access_token, get_current_user, verify_password
router=APIRouter(prefix="/auth",tags=["Auth"])

def authenticate(db,email,password):
    user=db.scalar(select(User).where(User.email==email.lower()))
    if not user or not verify_password(password,user.password_hash): raise HTTPException(status_code=401,detail="Invalid email or password")
    return user

@router.post("/login",response_model=TokenOut)
def login(body:LoginIn,db:Session=Depends(get_db)):
    user=authenticate(db,body.email,body.password); token=create_access_token(user)
    return {"access_token":token,"user":UserOut.model_validate(user).model_dump(mode="json")}

@router.post("/login-form",response_model=TokenOut)
def login_form(form:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(get_db)):
    user=authenticate(db,form.username,form.password); token=create_access_token(user)
    return {"access_token":token,"user":UserOut.model_validate(user).model_dump(mode="json")}

@router.get("/me",response_model=UserOut)
def me(user:User=Depends(get_current_user)): return user
