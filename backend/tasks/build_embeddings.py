"""
tasks/build_embeddings.py — Stub for embedding pipeline tasks.
These run via Celery worker after a repo is analyzed.
"""
from celery_app import celery_app
import structlog

log = structlog.get_logger()


@celery_app.task(name="tasks.build_embeddings.index_repo")
def index_repo(repo_id: str, owner: str, repo_name: str, access_token: str):
    """Index repository files into Qdrant vector store."""
    log.info("build_embeddings.index_repo called", repo_id=repo_id)
    # Stub: embeddings are handled inline by agent_service during analysis
    return {"status": "skipped", "reason": "handled_inline"}


@celery_app.task(name="tasks.build_embeddings.reindex_file")
def reindex_file(repo_id: str, file_path: str, content: str):
    """Re-index a single file after it changes."""
    log.info("build_embeddings.reindex_file called", repo_id=repo_id, path=file_path)
    return {"status": "skipped"}
