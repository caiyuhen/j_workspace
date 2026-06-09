"""
通知消息 API
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, desc, and_
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.models.models import Notification, User
from app.core.dependencies import get_current_active_user

router = APIRouter()


@router.get("", summary="我的通知列表")
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_read: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(Notification).where(Notification.user_id == current_user.id)
    count_query = select(func.count(Notification.id)).where(Notification.user_id == current_user.id)

    if is_read is not None:
        query = query.where(Notification.is_read == is_read)
        count_query = count_query.where(Notification.is_read == is_read)

    total = (await db.execute(count_query)).scalar()
    unread = (await db.execute(
        select(func.count(Notification.id)).where(
            and_(Notification.user_id == current_user.id, Notification.is_read == False)
        )
    )).scalar()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(desc(Notification.created_at)).offset(offset).limit(page_size)
    )
    notifications = result.scalars().all()

    return {
        "total": total,
        "unread": unread,
        "page": page,
        "page_size": page_size,
        "items": [{
            "id": str(n.id),
            "type": n.type,
            "priority": n.priority,
            "title": n.title,
            "content": n.content,
            "is_read": n.is_read,
            "read_at": n.read_at.isoformat() if n.read_at else None,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        } for n in notifications]
    }


from pydantic import BaseModel, EmailStr
from app.core.config import settings
import smtplib
from email.mime.text import MIMEText
from email.header import Header

class EmailRequest(BaseModel):
    to_emails: list[EmailStr]
    subject: str
    content: str

@router.post("/send-email", summary="发送邮件通知")
async def send_email(
    request: EmailRequest,
    current_user: User = Depends(get_current_active_user)
):
    try:
        msg = MIMEText(request.content, 'plain', 'utf-8')
        msg['Subject'] = Header(request.subject, 'utf-8')
        msg['From'] = Header(settings.EMAILS_FROM_NAME, 'utf-8')
        msg['From'].append(f" <{settings.EMAILS_FROM_EMAIL}>", 'ascii')
        msg['To'] = ",".join(request.to_emails)

        if settings.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            if settings.SMTP_TLS:
                server.starttls()
                
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAILS_FROM_EMAIL, request.to_emails, msg.as_string())
        server.quit()
        return {"message": f"成功向 {len(request.to_emails)} 个邮箱发送了邮件"}
    except smtplib.SMTPAuthenticationError as auth_e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail="阿里云邮箱认证失败！请检查密码是否正确，或者是否需要使用“客户端专属授权码”代替网页登录密码，并确认账号已在阿里云后台开启了 SMTP 服务。"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"发送邮件失败: {str(e)}")

@router.put("/{notification_id}/read", summary="标记为已读")
async def mark_as_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    from datetime import datetime, timezone
    await db.execute(
        update(Notification)
        .where(and_(Notification.id == notification_id, Notification.user_id == current_user.id))
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    await db.commit()
    return {"message": "已标记为已读"}


@router.put("/read-all", summary="全部标记为已读")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    from datetime import datetime, timezone
    await db.execute(
        update(Notification)
        .where(and_(Notification.user_id == current_user.id, Notification.is_read == False))
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    await db.commit()
    return {"message": "全部已读"}
