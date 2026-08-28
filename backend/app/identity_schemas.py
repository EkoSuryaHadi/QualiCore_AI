from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from .identity_models import MembershipRole


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RegisterOrganizationIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    organization_name: str = Field(min_length=2, max_length=255)
    country: str | None = Field(default=None, max_length=100)
    job_title: str | None = Field(default=None, max_length=150)


class OrganizationOut(ORM):
    id: str
    name: str
    slug: str
    country: str | None
    is_active: bool
    created_at: datetime


class MemberOut(BaseModel):
    id: str
    user_id: str
    email: EmailStr
    full_name: str
    role: str
    status: str
    job_title: str | None = None
    project_ids: list[str] = []


class InvitationCreate(BaseModel):
    email: EmailStr
    role: MembershipRole = MembershipRole.VIEWER
    project_id: str | None = None


class InvitationOut(ORM):
    id: str
    organization_id: str
    email: EmailStr
    role: str
    project_id: str | None
    token: str
    accepted_at: datetime | None
    expires_at: datetime
    created_at: datetime


class InvitationAccept(BaseModel):
    token: str
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    job_title: str | None = Field(default=None, max_length=150)


class MemberRoleUpdate(BaseModel):
    role: MembershipRole


class ProjectAssignmentIn(BaseModel):
    project_id: str
    role: MembershipRole | None = None


class MemberStatusUpdate(BaseModel):
    status: str
