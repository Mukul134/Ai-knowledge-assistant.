import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, UUID4
from app.core.config import settings

# HTTPBearer helper parses the Authorization header
security = HTTPBearer()

class CurrentUser(BaseModel):
    id: UUID4
    email: str
    role: str = "authenticated"

async def get_current_user() -> CurrentUser:
    """
    Bypassed authentication dependency. Returns a static developer profile
    for local-only, single-user mode.
    """
    return CurrentUser(
        id="de305d54-75b4-431b-adb2-eb6b9e546013",
        email="developer@example.com",
        role="authenticated"
    )
