from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db, close_db
from app.api.routes import auth, users, api_keys, master_resumes, job_descriptions, generated_resumes


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="JD Resume Changer API",
    description="Tailor resumes to job descriptions using AI",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(api_keys.router, prefix="/api/v1")
app.include_router(master_resumes.router, prefix="/api/v1")
app.include_router(job_descriptions.router, prefix="/api/v1")
app.include_router(generated_resumes.router, prefix="/api/v1")


@app.get("/health")
async def health():
    from app.config import get_settings
    from app.database import engine
    from sqlalchemy import text

    settings = get_settings()

    # Check database
    db_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    # Check pdflatex
    import shutil
    pdflatex_ok = shutil.which("pdflatex") is not None
    pdfinfo_ok = shutil.which("pdfinfo") is not None
    pdftotext_ok = shutil.which("pdftotext") is not None

    return {
        "ok": True,
        "database": db_ok,
        "pdflatex": pdflatex_ok,
        "pdfinfo": pdfinfo_ok,
        "pdftotext": pdftotext_ok,
        "environment": settings.environment,
    }


@app.get("/")
async def root():
    return {
        "name": "JD Resume Changer API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }