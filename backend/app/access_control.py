from sqlalchemy import select
from sqlalchemy.orm import Session

from .identity_models import MembershipRole, OrganizationMember, ProjectMember
from .models import Role, User


def membership_role(db: Session, user: User) -> str:
    member = db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == user.organization_id,
            OrganizationMember.user_id == user.id,
        )
    )
    if member:
        return member.role
    return {
        Role.ADMIN: MembershipRole.ORGANIZATION_ADMIN.value,
        Role.QA_MANAGER: MembershipRole.QA_MANAGER.value,
        Role.QA_ENGINEER: MembershipRole.QA_ENGINEER.value,
        Role.VIEWER: MembershipRole.VIEWER.value,
    }.get(user.role, MembershipRole.VIEWER.value)


def has_org_wide_access(db: Session, user: User) -> bool:
    role = membership_role(db, user)
    if role in {MembershipRole.ORGANIZATION_ADMIN.value, MembershipRole.QA_MANAGER.value}:
        return True
    # Backward compatibility for seeded demo users until explicit assignments are added.
    if user.organization_id == "demo-org":
        assignments = db.scalar(
            select(ProjectMember.id).where(
                ProjectMember.organization_id == user.organization_id,
                ProjectMember.user_id == user.id,
            ).limit(1)
        )
        return assignments is None
    return False


def project_ids_for_user(db: Session, user: User) -> list[str] | None:
    """Return None for organization-wide access, otherwise explicit project ids."""
    if has_org_wide_access(db, user):
        return None
    return list(
        db.scalars(
            select(ProjectMember.project_id).where(
                ProjectMember.organization_id == user.organization_id,
                ProjectMember.user_id == user.id,
            )
        ).all()
    )


def can_access_project(db: Session, user: User, project_id: str) -> bool:
    allowed = project_ids_for_user(db, user)
    return allowed is None or project_id in allowed
