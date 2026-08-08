# backend/app/main.py
# Main FastAPI application entrypoint registering configurations, middleware, & routes

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.auth.api.routes import router as auth_router, user_router
from backend.app.resume.api.routes import router as resume_router
from backend.app.jobs.api.routes import router as jobs_router
from backend.app.jobs.api.analysis_routes import router as analysis_router
from backend.app.resume.api.optimization_routes import router as optimization_router
from backend.app.email.api.routes import router as email_router
from backend.app.dashboard.api.routes import router as dashboard_router
from backend.app.shared.api_integration import router as integration_router
from backend.app.core.monitoring import router as monitoring_router
from backend.app.shared.exceptions import BaseAppException
from backend.app.core.middleware import ProductionHardeningMiddleware

app = FastAPI(
    title="AI Job Copilot Platform",
    description="Production-grade secure backend API for resume matching and tailoring.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS policies based on configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ProductionHardeningMiddleware)

# Global Exception handler to map BaseAppException instances to standard JSON responses
@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message
            }
        }
    )

from backend.app.api.v1.endpoints.resume_optimizer import router as resume_optimizer_router

# Expose base health check routes
@app.get("/health/api", tags=["System Health"])
async def api_health():
    """Simple API health probe endpoint."""
    return {"status": "healthy"}

# Register routes for Authentication and User Profile contexts
app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")

# Register specific sub-path routers first to prevent dynamic path parameter overlaps (e.g., /resume/{id} matching /resume/optimize)
app.include_router(resume_optimizer_router, prefix="/api/v1")
app.include_router(optimization_router, prefix="/api/v1")
app.include_router(resume_router, prefix="/api/v1")

app.include_router(analysis_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")

app.include_router(email_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(integration_router, prefix="/api/v1")
app.include_router(monitoring_router, prefix="/api/v1")
