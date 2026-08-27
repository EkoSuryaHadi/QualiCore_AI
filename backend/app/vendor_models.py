import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base
from .models import now, uid


class VendorStatus(str, enum.Enum):
    APPROVED = "APPROVED"
    WATCHLIST = "WATCHLIST"
    SUSPENDED = "SUSPENDED"


class VendorQuality(Base):
    __tablename__ = "vendor_quality"
    __table_args__ = (
        UniqueConstraint("organization_id", "project_id", "vendor_code", name="uq_vendor_project_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organization_id: Mapped[str] = mapped_column(String(36), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    vendor_code: Mapped[str] = mapped_column(String(80), index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str] = mapped_column(String(120), default="General")
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[VendorStatus] = mapped_column(Enum(VendorStatus), default=VendorStatus.APPROVED, index=True)
    quality_score: Mapped[float] = mapped_column(Float, default=100)
    delivery_score: Mapped[float] = mapped_column(Float, default=100)
    documentation_score: Mapped[float] = mapped_column(Float, default=100)
    inspection_score: Mapped[float] = mapped_column(Float, default=100)
    ncr_count: Mapped[int] = mapped_column(Integer, default=0)
    overall_score: Mapped[float] = mapped_column(Float, default=100, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
