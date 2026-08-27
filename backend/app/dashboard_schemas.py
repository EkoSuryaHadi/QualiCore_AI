from pydantic import BaseModel


class ProjectHealthOut(BaseModel):
    project_id: str
    code: str
    name: str
    progress: float
    quality_score: float
    failed_inspections: int
    open_ncr: int
    open_punch: int
    open_documents: int
    high_risks: int
    vendor_watchlist: int


class ExecutiveDashboardOut(BaseModel):
    total_projects: int
    active_projects: int
    total_inspections: int
    failed_inspections: int
    pass_rate: float
    open_ncr: int
    critical_ncr: int
    open_punch: int
    overdue_punch: int
    open_documents: int
    documents_in_review: int
    high_risks: int
    open_risks: int
    vendor_count: int
    vendor_watchlist: int
    vendor_suspended: int
    average_vendor_score: float
    assurance_score: float
    health_status: str
    projects: list[ProjectHealthOut]
