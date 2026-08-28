from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..auth_models import AuthSession, EmailVerificationToken, LoginSecurityState, PasswordResetToken, token_hash, token_value
from ..auth_schemas import ForgotPasswordIn, ResetPasswordIn, VerifyEmailIn
from ..config import settings
from ..database import get_db
from ..mailer import send_email_verification, send_password_reset
from ..models import User
from ..schemas import LoginIn, TokenOut, UserOut
from ..security import create_access_token, create_session, get_current_payload, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])

def _aware(value: datetime) -> datetime: return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
def _login_key(email: str) -> str: return token_hash(email.strip().lower())
def _login_state(db: Session, email: str) -> LoginSecurityState:
    key=_login_key(email); state=db.get(LoginSecurityState,key)
    if not state: state=LoginSecurityState(email_hash=key); db.add(state); db.flush()
    return state

def _record_login_failure(db: Session, state: LoginSecurityState) -> None:
    now=datetime.now(timezone.utc); started=_aware(state.window_started_at)
    if now-started>timedelta(minutes=15): state.failed_count=0; state.window_started_at=now
    state.failed_count+=1
    if state.failed_count>=5: state.blocked_until=now+timedelta(minutes=15)
    db.commit()

def _clear_login_failures(db: Session, state: LoginSecurityState) -> None:
    state.failed_count=0; state.blocked_until=None; state.window_started_at=datetime.now(timezone.utc); db.commit()

def authenticate(db: Session, email: str, password: str) -> User:
    state=_login_state(db,email); now=datetime.now(timezone.utc)
    if state.blocked_until and _aware(state.blocked_until)>now:
        db.commit(); raise HTTPException(status_code=429,detail="Too many sign-in attempts. Try again later.")
    user=db.scalar(select(User).where(User.email==email.lower()))
    if not user or not user.is_active or not verify_password(password,user.password_hash):
        _record_login_failure(db,state); raise HTTPException(status_code=401,detail="Invalid email or password")
    _clear_login_failures(db,state); return user

def issue_token(db: Session, user: User) -> str:
    auth_session=create_session(db,user); token=create_access_token(user,auth_session.id); db.commit(); return token

@router.post("/login",response_model=TokenOut)
def login(body:LoginIn,db:Session=Depends(get_db)):
    user=authenticate(db,body.email,body.password); token=issue_token(db,user)
    return {"access_token":token,"user":UserOut.model_validate(user).model_dump(mode="json")}

@router.post("/login-form",response_model=TokenOut)
def login_form(form:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(get_db)):
    user=authenticate(db,form.username,form.password); token=issue_token(db,user)
    return {"access_token":token,"user":UserOut.model_validate(user).model_dump(mode="json")}

@router.post("/logout")
def logout(payload:dict=Depends(get_current_payload),db:Session=Depends(get_db)):
    sid=payload.get("sid")
    if sid:
        auth_session=db.get(AuthSession,sid)
        if auth_session: auth_session.is_active=False; auth_session.revoked_at=datetime.now(timezone.utc); db.commit()
    return {"status":"ok","message":"Signed out"}

@router.get("/me",response_model=UserOut)
def me(user:User=Depends(get_current_user)): return user

@router.get("/sessions")
def sessions(payload:dict=Depends(get_current_payload),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    current_sid=payload.get("sid"); rows=list(db.scalars(select(AuthSession).where(AuthSession.user_id==user.id).order_by(AuthSession.created_at.desc())).all())
    return [{"id":row.id,"current":row.id==current_sid,"is_active":row.is_active,"expires_at":row.expires_at,"created_at":row.created_at,"last_seen_at":row.last_seen_at} for row in rows[:20]]

@router.delete("/sessions/{session_id}")
def revoke_session(session_id:str,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    row=db.get(AuthSession,session_id)
    if not row or row.user_id!=user.id: raise HTTPException(404,"Session not found")
    row.is_active=False; row.revoked_at=datetime.now(timezone.utc); db.commit(); return {"status":"ok"}

@router.post("/forgot-password")
def forgot_password(body:ForgotPasswordIn,db:Session=Depends(get_db)):
    response={"status":"ok","message":"If the email is registered, password reset instructions will be sent."}
    user=db.scalar(select(User).where(User.email==body.email.lower()))
    if not user or not user.is_active: return response
    prior=list(db.scalars(select(PasswordResetToken).where(PasswordResetToken.user_id==user.id,PasswordResetToken.used_at.is_(None))).all()); now=datetime.now(timezone.utc)
    for item in prior: item.used_at=now
    raw=token_value(); db.add(PasswordResetToken.create(user.id,raw)); db.commit(); send_password_reset(user.email,raw)
    if settings.auth_link_preview: response["preview_url"]=f"{settings.frontend_url.rstrip('/')}/reset-password?token={raw}"
    return response

@router.post("/reset-password")
def reset_password(body:ResetPasswordIn,db:Session=Depends(get_db)):
    item=db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash==token_hash(body.token)))
    if not item or item.used_at is not None: raise HTTPException(400,"Reset link is invalid or already used")
    if _aware(item.expires_at)<datetime.now(timezone.utc): raise HTTPException(400,"Reset link has expired")
    user=db.get(User,item.user_id)
    if not user or not user.is_active: raise HTTPException(400,"Reset link is invalid")
    user.password_hash=hash_password(body.password); item.used_at=datetime.now(timezone.utc)
    db.execute(update(AuthSession).where(AuthSession.user_id==user.id,AuthSession.is_active.is_(True)).values(is_active=False,revoked_at=datetime.now(timezone.utc)))
    state=db.get(LoginSecurityState,_login_key(user.email))
    if state: state.failed_count=0; state.blocked_until=None; state.window_started_at=datetime.now(timezone.utc)
    db.commit(); return {"status":"ok","message":"Password updated. Please sign in again on all devices."}

@router.post("/email-verification/request")
def request_email_verification(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    raw=token_value(); db.add(EmailVerificationToken.create(user.id,raw)); db.commit(); send_email_verification(user.email,raw)
    response={"status":"ok","message":"Verification instructions have been prepared."}
    if settings.auth_link_preview: response["preview_url"]=f"{settings.frontend_url.rstrip('/')}/verify-email?token={raw}"
    return response

@router.post("/email-verification/verify")
def verify_email(body:VerifyEmailIn,db:Session=Depends(get_db)):
    item=db.scalar(select(EmailVerificationToken).where(EmailVerificationToken.token_hash==token_hash(body.token)))
    if not item or item.verified_at is not None: raise HTTPException(400,"Verification link is invalid or already used")
    if _aware(item.expires_at)<datetime.now(timezone.utc): raise HTTPException(400,"Verification link has expired")
    item.verified_at=datetime.now(timezone.utc); db.commit(); return {"status":"ok","message":"Email verified"}

@router.get("/email-verification/status")
def email_verification_status(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    verified=db.scalar(select(EmailVerificationToken.id).where(EmailVerificationToken.user_id==user.id,EmailVerificationToken.verified_at.is_not(None)))
    return {"verified":bool(verified)}
