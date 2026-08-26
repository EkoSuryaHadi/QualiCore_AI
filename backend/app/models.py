import enum
import uuid
from datetime import date, datetime, timezone
from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

def uid(): return str(uuid.uuid4())
def now(): return datetime.now(timezone.utc)

class Role(str, enum.Enum):
    ADMIN="ADMIN"; QA_MANAGER="QA_MANAGER"; QA_ENGINEER="QA_ENGINEER"; VIEWER="VIEWER"
class ProjectStatus(str, enum.Enum):
    ACTIVE="ACTIVE"; HOLD="HOLD"; COMPLETED="COMPLETED"
class InspectionResult(str, enum.Enum):
    PASS="PASS"; FAIL="FAIL"; CONDITIONAL="CONDITIONAL"
class WorkflowStatus(str, enum.Enum):
    OPEN="OPEN"; IN_PROGRESS="IN_PROGRESS"; CLOSED="CLOSED"
class Severity(str, enum.Enum):
    LOW="LOW"; MEDIUM="MEDIUM"; HIGH="HIGH"; CRITICAL="CRITICAL"
class EvidenceEntity(str, enum.Enum):
    INSPECTION="INSPECTION"; NCR="NCR"; PUNCH="PUNCH"

class User(Base):
    __tablename__="users"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str]=mapped_column(String(36), index=True, default="demo-org")
    email: Mapped[str]=mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str]=mapped_column(String(255))
    password_hash: Mapped[str]=mapped_column(String(255))
    role: Mapped[Role]=mapped_column(Enum(Role), default=Role.VIEWER)
    is_active: Mapped[bool]=mapped_column(Boolean, default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class Project(Base):
    __tablename__="projects"
    __table_args__=(UniqueConstraint("organization_id","code",name="uq_project_org_code"),)
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str]=mapped_column(String(36), index=True)
    code: Mapped[str]=mapped_column(String(50), index=True)
    name: Mapped[str]=mapped_column(String(255))
    client_name: Mapped[str|None]=mapped_column(String(255), nullable=True)
    location: Mapped[str|None]=mapped_column(String(255), nullable=True)
    start_date: Mapped[date|None]=mapped_column(Date, nullable=True)
    finish_date: Mapped[date|None]=mapped_column(Date, nullable=True)
    status: Mapped[ProjectStatus]=mapped_column(Enum(ProjectStatus), default=ProjectStatus.ACTIVE)
    progress: Mapped[float]=mapped_column(Float, default=0)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class Inspection(Base):
    __tablename__="inspections"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str]=mapped_column(String(36), index=True)
    project_id: Mapped[str]=mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    discipline: Mapped[str]=mapped_column(String(100))
    inspection_type: Mapped[str]=mapped_column(String(120))
    location: Mapped[str|None]=mapped_column(String(255), nullable=True)
    inspection_date: Mapped[date]=mapped_column(Date)
    result: Mapped[InspectionResult]=mapped_column(Enum(InspectionResult))
    remarks: Mapped[str|None]=mapped_column(Text, nullable=True)
    created_by: Mapped[str]=mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class NCR(Base):
    __tablename__="ncrs"
    __table_args__=(UniqueConstraint("organization_id","number",name="uq_ncr_org_number"),)
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str]=mapped_column(String(36), index=True)
    project_id: Mapped[str]=mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    number: Mapped[str]=mapped_column(String(80), index=True)
    title: Mapped[str]=mapped_column(String(255))
    description: Mapped[str]=mapped_column(Text)
    discipline: Mapped[str]=mapped_column(String(100))
    severity: Mapped[Severity]=mapped_column(Enum(Severity), default=Severity.MEDIUM)
    status: Mapped[WorkflowStatus]=mapped_column(Enum(WorkflowStatus), default=WorkflowStatus.OPEN)
    root_cause: Mapped[str|None]=mapped_column(Text, nullable=True)
    corrective_action: Mapped[str|None]=mapped_column(Text, nullable=True)
    due_date: Mapped[date|None]=mapped_column(Date, nullable=True)
    created_by: Mapped[str]=mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
    closed_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True), nullable=True)

class PunchItem(Base):
    __tablename__="punch_items"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str]=mapped_column(String(36), index=True)
    project_id: Mapped[str]=mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    description: Mapped[str]=mapped_column(Text)
    category: Mapped[str]=mapped_column(String(100), default="General")
    severity: Mapped[Severity]=mapped_column(Enum(Severity), default=Severity.MEDIUM)
    status: Mapped[WorkflowStatus]=mapped_column(Enum(WorkflowStatus), default=WorkflowStatus.OPEN)
    owner_name: Mapped[str|None]=mapped_column(String(255), nullable=True)
    due_date: Mapped[date|None]=mapped_column(Date, nullable=True)
    created_by: Mapped[str]=mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
    closed_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True), nullable=True)

class Evidence(Base):
    __tablename__="evidence"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str]=mapped_column(String(36), index=True)
    project_id: Mapped[str]=mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    entity_type: Mapped[EvidenceEntity]=mapped_column(Enum(EvidenceEntity), index=True)
    entity_id: Mapped[str]=mapped_column(String(36), index=True)
    file_name: Mapped[str]=mapped_column(String(255))
    stored_name: Mapped[str]=mapped_column(String(255), unique=True)
    content_type: Mapped[str|None]=mapped_column(String(120), nullable=True)
    size_bytes: Mapped[int]=mapped_column(Integer, default=0)
    uploaded_by: Mapped[str]=mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class AuditLog(Base):
    __tablename__="audit_logs"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str]=mapped_column(String(36), index=True)
    actor_id: Mapped[str]=mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str]=mapped_column(String(80), index=True)
    entity_type: Mapped[str]=mapped_column(String(80), index=True)
    entity_id: Mapped[str]=mapped_column(String(36), index=True)
    summary: Mapped[str]=mapped_column(String(500))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now, index=True)

class Notification(Base):
    __tablename__="notifications"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str]=mapped_column(String(36), index=True)
    user_id: Mapped[str|None]=mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    title: Mapped[str]=mapped_column(String(200))
    message: Mapped[str]=mapped_column(String(500))
    entity_type: Mapped[str|None]=mapped_column(String(80), nullable=True)
    entity_id: Mapped[str|None]=mapped_column(String(36), nullable=True)
    is_read: Mapped[bool]=mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now, index=True)

class DocumentStatus(str, enum.Enum):
    DRAFT="DRAFT"; IN_REVIEW="IN_REVIEW"; APPROVED="APPROVED"; REJECTED="REJECTED"
class RiskStatus(str, enum.Enum):
    OPEN="OPEN"; MITIGATING="MITIGATING"; CLOSED="CLOSED"
class WorkflowEntity(str, enum.Enum):
    DOCUMENT="DOCUMENT"; RISK="RISK"; NCR="NCR"; PUNCH="PUNCH"

class Document(Base):
    __tablename__="documents"
    __table_args__=(UniqueConstraint("organization_id","document_no",name="uq_document_org_no"),)
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str]=mapped_column(String(36), index=True)
    project_id: Mapped[str]=mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    document_no: Mapped[str]=mapped_column(String(100), index=True)
    title: Mapped[str]=mapped_column(String(255))
    discipline: Mapped[str]=mapped_column(String(100))
    revision: Mapped[str]=mapped_column(String(20), default="A")
    status: Mapped[DocumentStatus]=mapped_column(Enum(DocumentStatus), default=DocumentStatus.DRAFT, index=True)
    owner_name: Mapped[str|None]=mapped_column(String(255), nullable=True)
    due_date: Mapped[date|None]=mapped_column(Date, nullable=True)
    created_by: Mapped[str]=mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now, onupdate=now)

class DocumentRevision(Base):
    __tablename__="document_revisions"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str]=mapped_column(String(36), index=True)
    document_id: Mapped[str]=mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    revision: Mapped[str]=mapped_column(String(20))
    note: Mapped[str|None]=mapped_column(Text, nullable=True)
    created_by: Mapped[str]=mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class Risk(Base):
    __tablename__="risks"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str]=mapped_column(String(36), index=True)
    project_id: Mapped[str]=mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    title: Mapped[str]=mapped_column(String(255))
    category: Mapped[str]=mapped_column(String(100), default="Quality")
    probability: Mapped[int]=mapped_column(Integer)
    impact: Mapped[int]=mapped_column(Integer)
    score: Mapped[int]=mapped_column(Integer, index=True)
    mitigation: Mapped[str|None]=mapped_column(Text, nullable=True)
    owner_name: Mapped[str|None]=mapped_column(String(255), nullable=True)
    status: Mapped[RiskStatus]=mapped_column(Enum(RiskStatus), default=RiskStatus.OPEN, index=True)
    due_date: Mapped[date|None]=mapped_column(Date, nullable=True)
    created_by: Mapped[str]=mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
    closed_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True), nullable=True)

class WorkflowEvent(Base):
    __tablename__="workflow_events"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str]=mapped_column(String(36), index=True)
    entity_type: Mapped[WorkflowEntity]=mapped_column(Enum(WorkflowEntity), index=True)
    entity_id: Mapped[str]=mapped_column(String(36), index=True)
    from_status: Mapped[str|None]=mapped_column(String(50), nullable=True)
    to_status: Mapped[str]=mapped_column(String(50))
    comment: Mapped[str|None]=mapped_column(Text, nullable=True)
    actor_id: Mapped[str]=mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now, index=True)
