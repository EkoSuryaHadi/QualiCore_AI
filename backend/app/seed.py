from datetime import date, timedelta
from sqlalchemy import select
from .database import Base, SessionLocal, engine
from .models import Inspection, InspectionResult, NCR, Project, PunchItem, Role, Severity, User
from .security import hash_password

def run():
    Base.metadata.create_all(bind=engine)
    db=SessionLocal()
    try:
        admin=db.scalar(select(User).where(User.email=="admin@qualicore.ai"))
        if not admin:
            admin=User(email="admin@qualicore.ai",full_name="QualiCore Admin",password_hash=hash_password("Admin123!"),role=Role.ADMIN,organization_id="demo-org")
            db.add(admin); db.flush()
        project=db.scalar(select(Project).where(Project.code=="QC-DEMO-001",Project.organization_id=="demo-org"))
        if not project:
            project=Project(organization_id="demo-org",code="QC-DEMO-001",name="EPC Demo Project",client_name="Demo Client",location="Balikpapan",start_date=date.today()-timedelta(days=30),finish_date=date.today()+timedelta(days=180),progress=18.5)
            db.add(project); db.flush()
            db.add(Inspection(organization_id="demo-org",project_id=project.id,discipline="Mechanical",inspection_type="Welding Visual Inspection",location="Area A",inspection_date=date.today(),result=InspectionResult.FAIL,remarks="Demo failed inspection",created_by=admin.id))
            db.add(NCR(organization_id="demo-org",project_id=project.id,number="NCR-0001",title="Weld visual defect",description="Surface defect found during inspection",discipline="Mechanical",severity=Severity.HIGH,due_date=date.today()+timedelta(days=7),created_by=admin.id))
            db.add(PunchItem(organization_id="demo-org",project_id=project.id,description="Repair coating damage",category="Mechanical Completion",severity=Severity.MEDIUM,owner_name="Construction Team",due_date=date.today()+timedelta(days=5),created_by=admin.id))
        db.commit()
        print("Seed complete: admin@qualicore.ai / Admin123!")
    finally: db.close()

if __name__=="__main__": run()
