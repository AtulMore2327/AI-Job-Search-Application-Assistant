from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings
from app.api.routes_resume import router as resume_router
from app.api.routes_jobs import router as jobs_router
from app.api.routes_match import router as match_router
from app.api.routes_application import router as app_router
from app.database.db import init_db

init_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Portfolio-quality 10X AI Job Search & Application Assistant API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume_router)
app.include_router(jobs_router)
app.include_router(match_router)
app.include_router(app_router)

@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "demo_mode": settings.DEMO_MODE,
        "groq_configured": bool(settings.GROQ_API_KEY),
        "tavily_configured": bool(settings.TAVILY_API_KEY)
    }

@app.get("/platforms/status", tags=["System"])
def get_platforms_status():
    return {
        "platforms": [
            {"name": "LinkedIn", "status": "ACTIVE", "type": "Tavily Search API Adapter"},
            {"name": "Naukri", "status": "ACTIVE", "type": "Tavily Search API Adapter"},
            {"name": "Indeed", "status": "ACTIVE", "type": "Tavily Search API Adapter"},
            {"name": "Glassdoor", "status": "ACTIVE", "type": "Tavily Search API Adapter"},
            {"name": "Internshala", "status": "ACTIVE", "type": "Tavily Search API Adapter"},
            {"name": "Foundit", "status": "ACTIVE", "type": "Tavily Search API Adapter"},
            {"name": "Shine", "status": "ACTIVE", "type": "Tavily Search API Adapter"},
            {"name": "Google Careers / Direct Corporate Portals", "status": "ACTIVE", "type": "Direct Search Adapter"}
        ],
        "demo_mode": settings.DEMO_MODE
    }

# Mount Web Dashboard Frontend
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
FRONTEND_DIR.mkdir(exist_ok=True)

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def serve_dashboard():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>10X AI Job Search Assistant API</h1><p>Visit <a href='/docs'>/docs</a> for API Swagger UI.</p>")
