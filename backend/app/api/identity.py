import re
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth_models import EmailVerificationToken, token_value
from ..database import get_db
from ..identity_models import Invitation, MembershipRole, MembershipStatus, Organization, OrganizationMember, ProjectMember
from ..identity_schemas import InvitationAccept, InvitationCreate, InvitationOut, MemberOut, MemberRoleUpdate, MemberStatusUpdate, OrganizationOut, OrganizationUpdate, ProjectAssignmentIn, RegisterOrganizationIn
from ..mailer import send_email_verification, send_invitation
from ..models import Project, Role, User
from ..security import create_access_token, create_session, get_current_user, hash_password, require_roles

router = APIRouter(prefix="/identity", tags=["Identity & Access"])


def _slug(value: str) -> str:
    clean = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "organization"
    return clean[:100]


def _unique_slug(db: Session, name: str) -> str:
    base = _slug(name); candidate = base; index = 2
    while db.scalar(select(Organization.id).where(Organization.slug == candidate)):
        candidate = f"{base}-{index}"; index += 1
    return candidate


def _membership_role(role: Role) -> str:
    return {Role.ADMIN:MembershipRole.ORGANIZATION_ADMIN.value,Role.QA_MANAGER:MembershipRole.QA_MANAGER.value,Role.QA_ENGINEER:MembershipRole.QA_ENGINEER.value,Role.VIEWER:MembershipRole.VIEWER.value}.get(role,MembershipRole.VIEWER.value)


def _legacy_role(role: str) -> Role:
    return {MembershipRole.ORGANIZATION_ADMIN.value:Role.ADMIN,MembershipRole.QA_MANAGER.value:Role.QA_MANAGER,MembershipRole.QA_ENGINEER.value:Role.QA_ENGINEER,MembershipRole.PROJECT_MANAGER.value:Role.VIEWER,MembershipRole.DOCUMENT_CONTROLLER.value:Role.VIEWER,MembershipRole.VIEWER.value:Role.VIEWER}.get(role,Role.VIEWER)


def _ensure_org(db: Session, user: User) -> Organization:
    org = db.get(Organization, user.organization_id)
    if not org:
        org = Organization(id=user.organization_id,name="QualiCore Demo Organization" if user.organization_id=="demo-org" else "Organization",slug=_unique_slug(db,user.organization_id)); db.add(org); db.flush()
    membership = db.scalar(select(OrganizationMember).where(OrganizationMember.organization_id==user.organization_id,OrganizationMember.user_id==user.id))
    if not membership:
        db.add(OrganizationMember(organization_id=user.organization_id,user_id=user.id,role=_membership_role(user.role),status=MembershipStatus.ACTIVE.value)); db.flush()
    return org


def _session_token(db: Session, user: User) -> str:
    session = create_session(db, user)
    return create_access_token(user, session.id)


@router.post("/register", status_code=201)
def register(body: RegisterOrganizationIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.scalar(select(User.id).where(User.email==email)): raise HTTPException(409,"Email already registered")
    org=Organization(name=body.organization_name.strip(),slug=_unique_slug(db,body.organization_name),country=body.country); db.add(org); db.flush()
    user=User(organization_id=org.id,email=email,full_name=body.full_name.strip(),password_hash=hash_password(body.password),role=Role.ADMIN,is_active=True); db.add(user); db.flush()
    db.add(OrganizationMember(organization_id=org.id,user_id=user.id,role=MembershipRole.ORGANIZATION_ADMIN.value,status=MembershipStatus.ACTIVE.value,job_title=body.job_title))
    verify_raw=token_value(); db.add(EmailVerificationToken.create(user.id,verify_raw)); token=_session_token(db,user); db.commit(); db.refresh(user)
    send_email_verification(user.email,verify_raw)
    return {"access_token":token,"token_type":"bearer","organization":{"id":org.id,"name":org.name,"slug":org.slug},"user":{"id":user.id,"email":user.email,"full_name":user.full_name,"role":MembershipRole.ORGANIZATION_ADMIN.value}}


@router.get("/organization",response_model=OrganizationOut)
def organization(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    org=_ensure_org(db,user); db.commit(); db.refresh(org); return org


@router.patch("/organization",response_model=OrganizationOut)
def update_organization(body:OrganizationUpdate,db:Session=Depends(get_db),admin:User=Depends(require_roles(Role.ADMIN))):
    org=_ensure_org(db,admin)
    if body.name is not None: org.name=body.name.strip()
    if "country" in body.model_fields_set: org.country=body.country
    db.commit(); db.refresh(org); return org


@router.get("/members",response_model=list[MemberOut])
def members(db:Session=Depends(get_db),admin:User=Depends(require_roles(Role.ADMIN))):
    _ensure_org(db,admin); users=list(db.scalars(select(User).where(User.organization_id==admin.organization_id).order_by(User.full_name)).all()); output=[]
    for user in users:
        member=db.scalar(select(OrganizationMember).where(OrganizationMember.organization_id==admin.organization_id,OrganizationMember.user_id==user.id))
        if not member:
            member=OrganizationMember(organization_id=admin.organization_id,user_id=user.id,role=_membership_role(user.role),status=MembershipStatus.ACTIVE.value); db.add(member); db.flush()
        project_ids=list(db.scalars(select(ProjectMember.project_id).where(ProjectMember.organization_id==admin.organization_id,ProjectMember.user_id==user.id)).all())
        output.append(MemberOut(id=member.id,user_id=user.id,email=user.email,full_name=user.full_name,role=member.role,status=member.status,job_title=member.job_title,project_ids=project_ids))
    db.commit(); return output


@router.post("/invitations",response_model=InvitationOut,status_code=201)
def invite(body:InvitationCreate,db:Session=Depends(get_db),admin:User=Depends(require_roles(Role.ADMIN))):
    org=_ensure_org(db,admin); email=body.email.lower()
    if db.scalar(select(User.id).where(User.email==email)): raise HTTPException(409,"A user with this email already exists")
    if body.project_id:
        project=db.get(Project,body.project_id)
        if not project or project.organization_id!=admin.organization_id: raise HTTPException(404,"Project not found")
    existing=db.scalar(select(Invitation).where(Invitation.organization_id==admin.organization_id,Invitation.email==email,Invitation.accepted_at.is_(None)))
    if existing: db.delete(existing); db.flush()
    invitation=Invitation(organization_id=admin.organization_id,email=email,role=body.role.value,project_id=body.project_id,invited_by=admin.id); db.add(invitation); db.commit(); db.refresh(invitation)
    send_invitation(invitation.email,invitation.token,org.name)
    return invitation


@router.get("/invitations",response_model=list[InvitationOut])
def invitations(db:Session=Depends(get_db),admin:User=Depends(require_roles(Role.ADMIN))):
    return list(db.scalars(select(Invitation).where(Invitation.organization_id==admin.organization_id).order_by(Invitation.created_at.desc())).all())


@router.delete("/invitations/{invitation_id}",status_code=204)
def revoke_invitation(invitation_id:str,db:Session=Depends(get_db),admin:User=Depends(require_roles(Role.ADMIN))):
    invitation=db.scalar(select(Invitation).where(Invitation.id==invitation_id,Invitation.organization_id==admin.organization_id))
    if not invitation: raise HTTPException(404,"Invitation not found")
    if invitation.accepted_at is not None: raise HTTPException(400,"Accepted invitation cannot be revoked")
    db.delete(invitation); db.commit(); return Response(status_code=204)


@router.post("/invitations/accept",status_code=201)
def accept_invitation(body:InvitationAccept,db:Session=Depends(get_db)):
    invitation=db.scalar(select(Invitation).where(Invitation.token==body.token))
    if not invitation or invitation.accepted_at is not None: raise HTTPException(404,"Invitation not found or already accepted")
    expires_at=invitation.expires_at
    if expires_at.tzinfo is None: expires_at=expires_at.replace(tzinfo=timezone.utc)
    if expires_at<datetime.now(timezone.utc): raise HTTPException(410,"Invitation has expired")
    if db.scalar(select(User.id).where(User.email==invitation.email)): raise HTTPException(409,"Email already registered")
    user=User(organization_id=invitation.organization_id,email=invitation.email,full_name=body.full_name.strip(),password_hash=hash_password(body.password),role=_legacy_role(invitation.role),is_active=True); db.add(user); db.flush()
    db.add(OrganizationMember(organization_id=invitation.organization_id,user_id=user.id,role=invitation.role,status=MembershipStatus.ACTIVE.value,job_title=body.job_title))
    if invitation.project_id: db.add(ProjectMember(organization_id=invitation.organization_id,project_id=invitation.project_id,user_id=user.id,role=invitation.role))
    proof_raw=token_value(); proof=EmailVerificationToken.create(user.id,proof_raw); proof.verified_at=datetime.now(timezone.utc); db.add(proof)
    invitation.accepted_at=datetime.now(timezone.utc); token=_session_token(db,user); db.commit(); db.refresh(user)
    return {"access_token":token,"token_type":"bearer","user":{"id":user.id,"email":user.email,"full_name":user.full_name,"role":invitation.role}}


@router.patch("/members/{user_id}/role")
def update_role(user_id:str,body:MemberRoleUpdate,db:Session=Depends(get_db),admin:User=Depends(require_roles(Role.ADMIN))):
    if user_id==admin.id and body.role!=MembershipRole.ORGANIZATION_ADMIN: raise HTTPException(400,"You cannot remove your own organization admin role")
    user=db.get(User,user_id)
    if not user or user.organization_id!=admin.organization_id: raise HTTPException(404,"User not found")
    member=db.scalar(select(OrganizationMember).where(OrganizationMember.organization_id==admin.organization_id,OrganizationMember.user_id==user_id))
    if not member: raise HTTPException(404,"Membership not found")
    member.role=body.role.value; user.role=_legacy_role(body.role.value); db.commit(); return {"status":"ok","role":member.role}


@router.patch("/members/{user_id}/status")
def update_status(user_id:str,body:MemberStatusUpdate,db:Session=Depends(get_db),admin:User=Depends(require_roles(Role.ADMIN))):
    allowed={MembershipStatus.ACTIVE.value,MembershipStatus.SUSPENDED.value,MembershipStatus.DISABLED.value}; status=body.status.upper()
    if status not in allowed: raise HTTPException(400,"Invalid member status")
    if user_id==admin.id and status!=MembershipStatus.ACTIVE.value: raise HTTPException(400,"You cannot disable your own account")
    user=db.get(User,user_id); member=db.scalar(select(OrganizationMember).where(OrganizationMember.organization_id==admin.organization_id,OrganizationMember.user_id==user_id))
    if not user or not member or user.organization_id!=admin.organization_id: raise HTTPException(404,"User not found")
    member.status=status; user.is_active=status==MembershipStatus.ACTIVE.value; db.commit(); return {"status":"ok","member_status":status}


@router.post("/members/{user_id}/projects",status_code=201)
def assign_project(user_id:str,body:ProjectAssignmentIn,db:Session=Depends(get_db),admin:User=Depends(require_roles(Role.ADMIN))):
    user=db.get(User,user_id); project=db.get(Project,body.project_id)
    if not user or user.organization_id!=admin.organization_id: raise HTTPException(404,"User not found")
    if not project or project.organization_id!=admin.organization_id: raise HTTPException(404,"Project not found")
    existing=db.scalar(select(ProjectMember).where(ProjectMember.project_id==body.project_id,ProjectMember.user_id==user_id)); role=body.role.value if body.role else _membership_role(user.role)
    if existing: existing.role=role
    else: db.add(ProjectMember(organization_id=admin.organization_id,project_id=body.project_id,user_id=user_id,role=role))
    db.commit(); return {"status":"ok","project_id":body.project_id,"user_id":user_id,"role":role}


@router.delete("/members/{user_id}/projects/{project_id}")
def remove_project(user_id:str,project_id:str,db:Session=Depends(get_db),admin:User=Depends(require_roles(Role.ADMIN))):
    assignment=db.scalar(select(ProjectMember).where(ProjectMember.organization_id==admin.organization_id,ProjectMember.project_id==project_id,ProjectMember.user_id==user_id))
    if not assignment: raise HTTPException(404,"Project assignment not found")
    db.delete(assignment); db.commit(); return {"status":"ok"}
