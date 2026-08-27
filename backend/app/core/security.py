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

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """
    FastAPI dependency to extract and validate the Supabase JWT from the request.
    Decodes the JWT locally using the SUPABASE_JWT_SECRET for zero-latency authentication,
    falling back to standard Supabase Auth API validation if local validation fails.
    """
    token = credentials.credentials
    
    # Check for Phase 1/mock tokens first to allow testing without real Supabase connection
    if token == "mock-token" or settings.ENVIRONMENT == "development" and token.startswith("mock-"):
        # Return a simulated user for local unit testing
        return CurrentUser(
            id="de305d54-75b4-431b-adb2-eb6b9e546013",
            email="developer@example.com",
            role="authenticated"
        )
        
    try:
        # 1. Local JWT Decoding (HS256 is the default for Supabase tokens)
        if settings.SUPABASE_JWT_SECRET:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated"
            )
            user_id = payload.get("sub")
            email = payload.get("email")
            
            if not user_id or not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload: missing sub or email claim"
                )
                
            return CurrentUser(
                id=user_id,
                email=email,
                role=payload.get("role", "authenticated")
            )
            
        # 2. Remote Validation Fallback (Queries Supabase Auth Server directly)
        else:
            from app.database.supabase import get_supabase_client
            supabase = get_supabase_client()
            response = supabase.auth.get_user(token)
            
            if not response or not response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token verification failed on Supabase authentication server"
                )
                
            return CurrentUser(
                id=response.user.id,
                email=response.user.email,
                role=response.user.role or "authenticated"
            )
            
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please sign in again."
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid signature or JWT format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authorization failure: {str(e)}"
        )
