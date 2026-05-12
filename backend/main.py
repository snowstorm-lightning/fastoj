import logging
import sys
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.core.config import settings
from backend.core.database import Base, engine

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import routers
from backend.api.auth import router as auth_router
from backend.api.problems import router as problems_router
from backend.api.problems.solutions import router as solutions_router
from backend.api.submissions import router as submissions_router
from backend.api.submissions.run import router as run_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

# Mount static files for web UI. Prefer the container path, but also work from a
# local checkout so `uvicorn backend.main:app` serves the same UI.
repo_root = Path(__file__).resolve().parents[1]
candidate_static_dirs = [
    Path("/app/frontend/src"),
    repo_root / "frontend" / "src",
]
static_dir = next((path for path in candidate_static_dirs if path.exists()), None)
if static_dir:
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware (disabled by default)
# from backend.api.middleware.rate_limit import RateLimitMiddleware
# app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.debug(f"Response: {request.method} {request.url.path} - {response.status_code}")
    return response


# Error handling middleware
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(exc) if settings.DEBUG else "Internal server error",
            },
        },
    )


# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(problems_router, prefix="/api/v1")
app.include_router(solutions_router, prefix="/api/v1")
app.include_router(submissions_router, prefix="/api/v1")
app.include_router(run_router, prefix="/api/v1")


# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME}


# Create tables on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Starting FastOJ API...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down FastOJ API...")


@app.get("/")
async def root():
    """Redirect to web UI."""
    if static_dir and (static_dir / "index.html").exists():
        return RedirectResponse(url="/static/index.html")
    return {"message": "FastOJ API", "version": settings.APP_VERSION}


@app.get("/app")
async def web_app():
    """Serve the web UI entrypoint directly."""
    if static_dir and (static_dir / "index.html").exists():
        return FileResponse(static_dir / "index.html")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"success": False, "error": {"message": "Web UI not found"}},
    )
