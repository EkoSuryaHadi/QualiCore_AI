from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Notification,User
from ..schemas import NotificationOut
from ..security import get_current_user
router=APIRouter(prefix='/notifications',tags=['Notifications'])
@router.get('',response_model=list[NotificationOut])
def items(unread_only:bool=False,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
 q=select(Notification).where(Notification.organization_id==user.organization_id,Notification.user_id==user.id)
 if unread_only:q=q.where(Notification.is_read.is_(False))
 return db.scalars(q.order_by(Notification.created_at.desc()).limit(100)).all()
@router.post('/{id}/read',response_model=NotificationOut)
def read(id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
 n=db.scalar(select(Notification).where(Notification.id==id,Notification.user_id==user.id,Notification.organization_id==user.organization_id))
 if not n:raise HTTPException(404,'Notification not found')
 n.is_read=True;db.commit();db.refresh(n);return n
