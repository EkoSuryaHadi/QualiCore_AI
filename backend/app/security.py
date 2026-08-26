import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import Role, User

oauth2_scheme=OAuth2PasswordBearer(tokenUrl="v1/auth/login-form")

def _b64(data:bytes)->str: return base64.urlsafe_b64encode(data).rstrip(b"=").decode()
def _unb64(text:str)->bytes: return base64.urlsafe_b64decode(text + "="*((4-len(text)%4)%4))

def hash_password(password:str)->str:
    salt=os.urandom(16); digest=hashlib.pbkdf2_hmac("sha256",password.encode(),salt,310000)
    return f"pbkdf2_sha256$310000${_b64(salt)}${_b64(digest)}"

def verify_password(password:str, encoded:str)->bool:
    try:
        scheme,iterations,salt,digest=encoded.split("$",3)
        if scheme!="pbkdf2_sha256": return False
        check=hashlib.pbkdf2_hmac("sha256",password.encode(),_unb64(salt),int(iterations))
        return hmac.compare_digest(check,_unb64(digest))
    except Exception: return False

def create_access_token(user:User)->str:
    header={"alg":"HS256","typ":"JWT"}
    exp=int((datetime.now(timezone.utc)+timedelta(minutes=settings.access_token_minutes)).timestamp())
    payload={"sub":user.id,"org":user.organization_id,"role":user.role.value,"exp":exp}
    signing=f"{_b64(json.dumps(header,separators=(",",":")).encode())}.{_b64(json.dumps(payload,separators=(",",":")).encode())}"
    sig=hmac.new(settings.jwt_secret.encode(),signing.encode(),hashlib.sha256).digest()
    return f"{signing}.{_b64(sig)}"

def _decode_token(token:str)->dict:
    try:
        h,p,s=token.split(".")
        signing=f"{h}.{p}"
        expected=hmac.new(settings.jwt_secret.encode(),signing.encode(),hashlib.sha256).digest()
        if not hmac.compare_digest(expected,_unb64(s)): raise ValueError("signature")
        payload=json.loads(_unb64(p))
        if int(payload.get("exp",0))<int(datetime.now(timezone.utc).timestamp()): raise ValueError("expired")
        return payload
    except Exception as exc: raise ValueError("invalid token") from exc

def get_current_user(token:str=Depends(oauth2_scheme), db:Session=Depends(get_db))->User:
    exc=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid authentication credentials",headers={"WWW-Authenticate":"Bearer"})
    try:
        uid=_decode_token(token).get("sub")
        if not uid: raise exc
    except Exception: raise exc
    user=db.get(User,uid)
    if not user or not user.is_active: raise exc
    return user

def require_roles(*allowed:Role):
    def dep(user:User=Depends(get_current_user)):
        if user.role not in allowed: raise HTTPException(status_code=403,detail="Insufficient permission")
        return user
    return dep
