from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from .models import EvidenceEntity, InspectionResult, ProjectStatus, Role, Severity, WorkflowStatus

class ORM(BaseModel): model_config=ConfigDict(from_attributes=True)
class LoginIn(BaseModel): email: EmailStr; password: str
class TokenOut(BaseModel): access_token: str; token_type: str="bearer"; user: dict
class UserCreate(BaseModel): email:EmailStr; full_name:str; password:str=Field(min_length=8); role:Role=Role.VIEWER
class UserOut(ORM): id:str; organization_id:str; email:EmailStr; full_name:str; role:Role; is_active:bool

class ProjectCreate(BaseModel):
    code:str=Field(min_length=2,max_length=50); name:str; client_name:str|None=None; location:str|None=None
    start_date:date|None=None; finish_date:date|None=None; status:ProjectStatus=ProjectStatus.ACTIVE; progress:float=Field(default=0,ge=0,le=100)
class ProjectUpdate(BaseModel):
    name:str|None=None; client_name:str|None=None; location:str|None=None; start_date:date|None=None; finish_date:date|None=None
    status:ProjectStatus|None=None; progress:float|None=Field(default=None,ge=0,le=100)
class ProjectOut(ProjectCreate, ORM): id:str; organization_id:str; created_at:datetime

class InspectionCreate(BaseModel):
    project_id:str; discipline:str; inspection_type:str; location:str|None=None; inspection_date:date; result:InspectionResult; remarks:str|None=None
class InspectionUpdate(BaseModel):
    discipline:str|None=None; inspection_type:str|None=None; location:str|None=None; inspection_date:date|None=None; result:InspectionResult|None=None; remarks:str|None=None
class InspectionOut(InspectionCreate, ORM): id:str; organization_id:str; created_by:str; created_at:datetime

class NCRCreate(BaseModel):
    project_id:str; number:str; title:str; description:str; discipline:str; severity:Severity=Severity.MEDIUM; due_date:date|None=None
class NCRUpdate(BaseModel):
    title:str|None=None; description:str|None=None; severity:Severity|None=None; status:WorkflowStatus|None=None
    root_cause:str|None=None; corrective_action:str|None=None; due_date:date|None=None
class NCRClose(BaseModel):
    comment:str|None=None
class NCROut(NCRCreate, ORM): id:str; organization_id:str; status:WorkflowStatus; root_cause:str|None; corrective_action:str|None; created_by:str; created_at:datetime; closed_at:datetime|None

class PunchCreate(BaseModel):
    project_id:str; description:str; category:str="General"; severity:Severity=Severity.MEDIUM; owner_name:str|None=None; due_date:date|None=None
class PunchUpdate(BaseModel):
    description:str|None=None; category:str|None=None; severity:Severity|None=None; status:WorkflowStatus|None=None; owner_name:str|None=None; due_date:date|None=None
class PunchOut(PunchCreate, ORM): id:str; organization_id:str; status:WorkflowStatus; created_by:str; created_at:datetime; closed_at:datetime|None

class DashboardOut(BaseModel):
    total_projects:int; active_projects:int; total_inspections:int; failed_inspections:int; open_ncr:int; open_punch:int; overdue_punch:int; quality_score:float
class ProjectWorkspaceOut(BaseModel):
    project:ProjectOut; total_inspections:int; failed_inspections:int; open_ncr:int; critical_ncr:int; open_punch:int; overdue_punch:int; evidence_count:int; quality_score:float
class EvidenceOut(ORM):
    id:str; project_id:str; entity_type:EvidenceEntity; entity_id:str; file_name:str; content_type:str|None; size_bytes:int; uploaded_by:str; created_at:datetime
class AuditOut(ORM):
    id:str; actor_id:str; action:str; entity_type:str; entity_id:str; summary:str; created_at:datetime
class NotificationOut(ORM):
    id:str; title:str; message:str; entity_type:str|None; entity_id:str|None; is_read:bool; created_at:datetime

from .models import DocumentStatus, RiskStatus, WorkflowEntity

class DocumentCreate(BaseModel):
    project_id:str; document_no:str; title:str; discipline:str; revision:str="A"; owner_name:str|None=None; due_date:date|None=None
class DocumentUpdate(BaseModel):
    title:str|None=None; discipline:str|None=None; revision:str|None=None; owner_name:str|None=None; due_date:date|None=None
class DocumentOut(DocumentCreate, ORM):
    id:str; organization_id:str; status:DocumentStatus; created_by:str; created_at:datetime; updated_at:datetime
class RevisionCreate(BaseModel): revision:str; note:str|None=None
class RevisionOut(ORM): id:str; document_id:str; revision:str; note:str|None; created_by:str; created_at:datetime

class RiskCreate(BaseModel):
    project_id:str; title:str; category:str="Quality"; probability:int=Field(ge=1,le=5); impact:int=Field(ge=1,le=5); mitigation:str|None=None; owner_name:str|None=None; due_date:date|None=None
class RiskUpdate(BaseModel):
    title:str|None=None; category:str|None=None; probability:int|None=Field(default=None,ge=1,le=5); impact:int|None=Field(default=None,ge=1,le=5); mitigation:str|None=None; owner_name:str|None=None; due_date:date|None=None; status:RiskStatus|None=None
class RiskOut(RiskCreate, ORM):
    id:str; organization_id:str; score:int; status:RiskStatus; created_by:str; created_at:datetime; closed_at:datetime|None
class WorkflowAction(BaseModel): comment:str|None=None
class WorkflowEventOut(ORM):
    id:str; entity_type:WorkflowEntity; entity_id:str; from_status:str|None; to_status:str; comment:str|None; actor_id:str; created_at:datetime

class RiskHeatmapCell(BaseModel): probability:int; impact:int; count:int
class ReportSummary(BaseModel):
    generated_at:datetime; project_count:int; inspection_count:int; fail_count:int; open_ncr:int; open_punch:int; open_documents:int; high_risks:int; quality_score:float
