from sqlalchemy.orm import Session
from .models import AuditLog, Notification, User

def audit(db:Session,user:User,action:str,entity_type:str,entity_id:str,summary:str):
    db.add(AuditLog(organization_id=user.organization_id,actor_id=user.id,action=action,entity_type=entity_type,entity_id=entity_id,summary=summary))

def notify(db:Session,user:User,title:str,message:str,entity_type:str|None=None,entity_id:str|None=None):
    db.add(Notification(organization_id=user.organization_id,user_id=user.id,title=title,message=message,entity_type=entity_type,entity_id=entity_id))
