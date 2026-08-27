from fastapi import APIRouter, Depends, UploadFile, File, Header, HTTPException, status, BackgroundTasks, Request
from app.core.security import get_current_user, CurrentUser
from app.services.document_service import DocumentService
from app.core.limiter import limiter

router = APIRouter()

def get_token_from_header(authorization: str = Header(...)) -> str:
    """Extracts raw JWT token from Bearer Authorization header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <JWT>'."
        )
    return authorization.split(" ")[1]

@router.post("/upload", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def upload_pdf(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Upload a PDF document to private storage.
    Limits file size to 10MB and enforces PDF mime-type.
    """
    return await DocumentService.upload_document(file, current_user, background_tasks)

@router.get("", response_model=list[dict])
async def list_user_documents(
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_token_from_header)
):
    """
    List all documents uploaded by the authenticated user.
    """
    return DocumentService.list_documents(current_user, token)

@router.get("/{document_id}")
async def get_document_meta(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_token_from_header)
):
    """
    Retrieve metadata for a specific document.
    """
    return DocumentService.get_document(document_id, current_user, token)

@router.delete("/{document_id}")
async def delete_user_document(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_token_from_header)
):
    """
    Delete a document from database and private storage.
    Cascades chunk deletions.
    """
    return DocumentService.delete_document(document_id, current_user, token)
