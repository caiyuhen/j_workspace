from sqlmodel import Session

from app.models import FileRecord
from app.schemas import FileResponse, RegisterFileRequest


def register_file(session: Session, payload: RegisterFileRequest) -> FileResponse:
    record = FileRecord(
        project_id=payload.project_id,
        kind=payload.kind,
        name=payload.name,
        storage_path=payload.storage_path,
        checksum=payload.checksum,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return FileResponse.model_validate(record, from_attributes=True)
