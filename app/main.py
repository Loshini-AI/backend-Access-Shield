from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import api_router

app = FastAPI(
    title="ACCESS SHIELD X Backend",
    description=(
        "Intelligent IAM Least-Privilege Auditor API. "
        "Detects unused, overbroad, wildcard, and destructive cloud IAM permissions using deterministic rule-based log comparison."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Middleware Configuration
origins = settings.cors_origins_list

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)


@app.get("/api/health", tags=["Health Check"], summary="Health Check Endpoint")
def health_check():
    return {
        "status": "healthy",
        "service": "access-shield-x-backend",
        "version": "2.0.0",
        "environment": settings.APP_ENV
    }


from app.api.routes.admin import seed_if_empty
seed_if_empty()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
