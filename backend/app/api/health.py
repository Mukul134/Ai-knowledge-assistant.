from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Standard health check endpoint.
    Returns API status, version, and current configuration state.
    """
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "database_configured": bool(settings.DATABASE_URL or settings.POSTGRES_URL)
    }
