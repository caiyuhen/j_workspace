<<<<<<< HEAD
"""
文档管理 API (eTMF)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from pydantic import BaseModel
from typing import Optional
from datetime import date
from uuid import UUID

from app.db.session import get_db
from app.models.models import Document, User
from app.core.dependencies import get_current_active_user, require_permissions

router = APIRouter()


class DocumentCreate(BaseModel):
    trial_id: UUID
    folder_id: Optional[UUID] = None
    title: str
    doc_type: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    version: str = "1.0"
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    requires_esig: bool = False


def doc_to_dict(d: Document) -> dict:
    return {
        "id": str(d.id),
        "trial_id": str(d.trial_id) if d.trial_id else None,
        "title": d.title,
        "doc_type": d.doc_type,
        "file_name": d.file_name,
        "file_size": d.file_size,
        "file_path": d.file_path,
        "version": d.version,
        "effective_date": d.effective_date.isoformat() if d.effective_date else None,
        "expiry_date": d.expiry_date.isoformat() if d.expiry_date else None,
        "requires_esig": d.requires_esig,
        "esig_status": d.esig_status,
        "status": d.status,
        "is_current": d.is_current,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


@router.get("", summary="文档列表")
async def list_documents(
    trial_id: Optional[UUID] = Query(None),
    folder_id: Optional[UUID] = Query(None),
    doc_type: Optional[str] = Query(None),
    expiry_warning: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(Document).where(Document.is_current == True)
    filters = []
    if trial_id:
        filters.append(Document.trial_id == trial_id)
    if folder_id:
        filters.append(Document.folder_id == folder_id)
    if doc_type:
        filters.append(Document.doc_type == doc_type)
    if expiry_warning:
        from datetime import timedelta
        warn_date = date.today() + timedelta(days=30)
        filters.append(Document.expiry_date <= warn_date)
    if filters:
        query = query.where(and_(*filters))

    # 数据隔离：非管理员只能看自己负责的试验或所属中心相关的文档
    if not current_user.is_superuser:
        from app.models.models import TrialSite, Trial, Site
        subq = select(Trial.id).where(
            (Trial.pm_user_id == current_user.id) | 
            (Trial.created_by == current_user.id)
        )
        subq2 = select(TrialSite.trial_id).where(
            (TrialSite.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id))) |
            (TrialSite.pi_user_id == current_user.id)
        )
        # 文档的trial_id为空代表全局文档，或者trial_id在自己权限内
        cond = (Document.trial_id.is_(None)) | (Document.trial_id.in_(subq)) | (Document.trial_id.in_(subq2))
        query = query.where(cond)

    result = await db.execute(query.order_by(desc(Document.created_at)))
    docs = result.scalars().all()
    return {"total": len(docs), "items": [doc_to_dict(d) for d in docs]}


@router.post("", summary="上传文档", status_code=201)
async def upload_document(
    body: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("document:write")),
):
    """创建文档记录（文件实际通过 /upload 接口上传）"""
    doc = Document(
        trial_id=body.trial_id,
        folder_id=body.folder_id,
        title=body.title,
        doc_type=body.doc_type,
        file_name=body.file_name,
        file_size=body.file_size,
        version=body.version,
        effective_date=body.effective_date,
        expiry_date=body.expiry_date,
        requires_esig=body.requires_esig,
        esig_status="NONE" if not body.requires_esig else "PENDING",
        status="DRAFT",
        is_current=True,
        uploaded_by=current_user.id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return {"message": "文档记录创建成功", "data": doc_to_dict(doc)}


@router.post("/{doc_id}/sign", summary="文档电子签名 (21 CFR Part 11)")
async def sign_document(
    doc_id: UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """对文档进行电子签名，符合 21 CFR Part 11 PKI 要求"""
    from datetime import datetime, timezone
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if doc.esig_status == "SIGNED":
        raise HTTPException(status_code=400, detail="文档已签署")

    doc.esig_status = "SIGNED"
    doc.esig_by = current_user.id
    doc.esig_at = datetime.now(timezone.utc)
    doc.esig_cert = body.get("cert_info")
    doc.status = "APPROVED"
    await db.commit()
    return {"message": "电子签名成功"}


@router.delete("/{doc_id}", summary="删除文档")
async def delete_document(
    doc_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("document:write")),
):
    """物理删除文档记录"""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
        
    await db.delete(doc)
    await db.commit()
    return {"message": "文档删除成功"}
=======
"""
文档管理 API (eTMF)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from pydantic import BaseModel
from typing import Optional
from datetime import date
from uuid import UUID

from app.db.session import get_db
from app.models.models import Document, User
from app.core.dependencies import get_current_active_user, require_permissions

router = APIRouter()


class DocumentCreate(BaseModel):
    trial_id: UUID
    folder_id: Optional[UUID] = None
    title: str
    doc_type: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    version: str = "1.0"
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    requires_esig: bool = False


def doc_to_dict(d: Document) -> dict:
    return {
        "id": str(d.id),
        "trial_id": str(d.trial_id) if d.trial_id else None,
        "title": d.title,
        "doc_type": d.doc_type,
        "file_name": d.file_name,
        "file_size": d.file_size,
        "file_path": d.file_path,
        "version": d.version,
        "effective_date": d.effective_date.isoformat() if d.effective_date else None,
        "expiry_date": d.expiry_date.isoformat() if d.expiry_date else None,
        "requires_esig": d.requires_esig,
        "esig_status": d.esig_status,
        "status": d.status,
        "is_current": d.is_current,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


@router.get("", summary="文档列表")
async def list_documents(
    trial_id: Optional[UUID] = Query(None),
    folder_id: Optional[UUID] = Query(None),
    doc_type: Optional[str] = Query(None),
    expiry_warning: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(Document).where(Document.is_current == True)
    filters = []
    if trial_id:
        filters.append(Document.trial_id == trial_id)
    if folder_id:
        filters.append(Document.folder_id == folder_id)
    if doc_type:
        filters.append(Document.doc_type == doc_type)
    if expiry_warning:
        from datetime import timedelta
        warn_date = date.today() + timedelta(days=30)
        filters.append(Document.expiry_date <= warn_date)
    if filters:
        query = query.where(and_(*filters))

    # 数据隔离：非管理员只能看自己负责的试验或所属中心相关的文档
    if not current_user.is_superuser:
        from app.models.models import TrialSite, Trial, Site
        subq = select(Trial.id).where(
            (Trial.pm_user_id == current_user.id) | 
            (Trial.created_by == current_user.id)
        )
        subq2 = select(TrialSite.trial_id).where(
            (TrialSite.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id))) |
            (TrialSite.pi_user_id == current_user.id)
        )
        # 文档的trial_id为空代表全局文档，或者trial_id在自己权限内
        cond = (Document.trial_id.is_(None)) | (Document.trial_id.in_(subq)) | (Document.trial_id.in_(subq2))
        query = query.where(cond)

    result = await db.execute(query.order_by(desc(Document.created_at)))
    docs = result.scalars().all()
    return {"total": len(docs), "items": [doc_to_dict(d) for d in docs]}


@router.post("", summary="上传文档", status_code=201)
async def upload_document(
    body: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("document:write")),
):
    """创建文档记录（文件实际通过 /upload 接口上传）"""
    doc = Document(
        trial_id=body.trial_id,
        folder_id=body.folder_id,
        title=body.title,
        doc_type=body.doc_type,
        file_name=body.file_name,
        file_size=body.file_size,
        version=body.version,
        effective_date=body.effective_date,
        expiry_date=body.expiry_date,
        requires_esig=body.requires_esig,
        esig_status="NONE" if not body.requires_esig else "PENDING",
        status="DRAFT",
        is_current=True,
        uploaded_by=current_user.id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return {"message": "文档记录创建成功", "data": doc_to_dict(doc)}


@router.post("/{doc_id}/sign", summary="文档电子签名 (21 CFR Part 11)")
async def sign_document(
    doc_id: UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """对文档进行电子签名，符合 21 CFR Part 11 PKI 要求"""
    from datetime import datetime, timezone
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if doc.esig_status == "SIGNED":
        raise HTTPException(status_code=400, detail="文档已签署")

    doc.esig_status = "SIGNED"
    doc.esig_by = current_user.id
    doc.esig_at = datetime.now(timezone.utc)
    doc.esig_cert = body.get("cert_info")
    doc.status = "APPROVED"
    await db.commit()
    return {"message": "电子签名成功"}


@router.delete("/{doc_id}", summary="删除文档")
async def delete_document(
    doc_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("document:write")),
):
    """物理删除文档记录"""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
        
    await db.delete(doc)
    await db.commit()
    return {"message": "文档删除成功"}
>>>>>>> origin/main
