from fastapi import APIRouter, Depends
from app.core.security import get_current_user, CurrentUser

router = APIRouter()

@router.get("/me", response_model=CurrentUser)
async def get_current_authenticated_user(current_user: CurrentUser = Depends(get_current_user)):
    """
    Get information about the currently authenticated user.
    Forces JWT validation.
    """
    return current_user
