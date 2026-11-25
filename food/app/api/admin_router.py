from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import get_document_service, require_admin
from app.exceptions import ValidationFailedError
from app.models.user import User
from app.services.document_service import DocumentService

router = APIRouter(prefix="/api/admin/documents")


@router.get("")
def list_documents(
    _admin: User = Depends(require_admin),
    service: DocumentService = Depends(get_document_service),
) -> list[dict]:
    return service.list_documents()


@router.post("", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    admin: User = Depends(require_admin),
    service: DocumentService = Depends(get_document_service),
) -> dict:
    if not file.filename:
        raise ValidationFailedError("A filename is required")
    data = await file.read()
    doc = service.ingest(admin, file.filename, data)
    return {"id": doc.id, "filename": doc.filename, "version": doc.version, "status": doc.status}
