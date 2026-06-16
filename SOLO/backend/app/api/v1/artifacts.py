"""任务交付物下载 API。"""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.api.v1.auth import TokenData, get_current_active_user
from app.services.artifact_service import artifact_service

router = APIRouter()


@router.get("/{artifact_id}/download")
async def download_artifact(
    artifact_id: str,
    current_user: TokenData = Depends(get_current_active_user),
):
    """下载当前用户拥有的任务交付物。"""
    try:
        artifact = artifact_service.get_owned_artifact(artifact_id, current_user.user_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    return FileResponse(
        path=str(Path(artifact["path"])),
        media_type=artifact.get("content_type") or "application/octet-stream",
        filename=artifact["filename"],
    )
