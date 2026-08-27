import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from app.core.limiter import limiter
from app.core.config import settings
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.chat import router as chat_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for the Agentic AI Knowledge Assistant",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# Register rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router, prefix="/api", tags=["System"])
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(documents_router, prefix="/api/documents", tags=["Documents"])
app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to the AI Knowledge Assistant API. Access endpoints via /api/health or /docs."
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development"
    )
