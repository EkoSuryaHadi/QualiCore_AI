from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .vendor_models import VendorStatus


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class VendorCreate(BaseModel):
    project_id: str
    vendor_code: str = Field(min_length=2, max_length=80)
    vendor_name: str
    category: str = "General"
    contact_name: str | None = None
    contact_email: EmailStr | None = None
    status: VendorStatus = VendorStatus.APPROVED
    quality_score: float = Field(default=100, ge=0, le=100)
    delivery_score: float = Field(default=100, ge=0, le=100)
    documentation_score: float = Field(default=100, ge=0, le=100)
    inspection_score: float = Field(default=100, ge=0, le=100)
    ncr_count: int = Field(default=0, ge=0)
    notes: str | None = None


class VendorUpdate(BaseModel):
    vendor_name: str | None = None
    category: str | None = None
    contact_name: str | None = None
    contact_email: EmailStr | None = None
    status: VendorStatus | None = None
    quality_score: float | None = Field(default=None, ge=0, le=100)
    delivery_score: float | None = Field(default=None, ge=0, le=100)
    documentation_score: float | None = Field(default=None, ge=0, le=100)
    inspection_score: float | None = Field(default=None, ge=0, le=100)
    ncr_count: int | None = Field(default=None, ge=0)
    notes: str | None = None


class VendorOut(VendorCreate, ORM):
    id: str
    organization_id: str
    overall_score: float
    created_by: str
    created_at: datetime
    updated_at: datetime
