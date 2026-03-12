"""
Codora — FastAPI Application Entry Point
"""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from config import settings
from database import init_db
from neo4j_client import init_neo4j, close_neo4j
from qdrant_store import init_qdrant
from redis_client import init_redis, close_redis

# Routers
from routers import auth, users, repositories, mentor, issues, pr, graph, discover, repo_intel

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    log.info("Starting Codora API", env=settings.APP_ENV)

    # Initialize databases
    await init_db()
    await init_neo4j()
    await init_qdrant()
    await init_redis()

    log.info("All services initialized ✓")
    yield

    # Cleanup
    await close_neo4j()
    await close_redis()
    log.info("Shutdown complete")


app = FastAPI(
    title="Codora",
    description="Intelligent mentor platform for open source contributors",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ── Routers ───────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(repositories.router, prefix="/api/repos", tags=["repositories"])
app.include_router(mentor.router, prefix="/api/mentor", tags=["mentor"])
app.include_router(issues.router, prefix="/api/issues", tags=["issues"])
app.include_router(pr.router, prefix="/api/pr", tags=["pull-requests"])
app.include_router(graph.router, prefix="/api/graph", tags=["knowledge-graph"])
app.include_router(discover.router, prefix="/api/discover", tags=["discover"])
app.include_router(repo_intel.router, prefix="/api/intel", tags=["repo-intelligence"])


# ── Health Check ──────────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "version": "1.0.0", "env": settings.APP_ENV}


@app.get("/", tags=["system"])
async def root():
    return {
        "message": "Codora API",
        "docs": "/docs",
        "version": "1.0.0",
    }
