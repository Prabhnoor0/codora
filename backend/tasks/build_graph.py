"""
tasks/build_graph.py — Stub for Neo4j knowledge graph build tasks.
"""
from celery_app import celery_app
import structlog

log = structlog.get_logger()


@celery_app.task(name="tasks.build_graph.build_repo_graph")
def build_repo_graph(repo_id: str, owner: str, repo_name: str, access_token: str):
    """Build Neo4j code knowledge graph for a repository."""
    log.info("build_graph.build_repo_graph called", repo_id=repo_id)
    return {"status": "skipped", "reason": "handled_inline"}


@celery_app.task(name="tasks.build_graph.update_user_node")
def update_user_node(user_id: str):
    """Update the user node in the knowledge graph after skill changes."""
    log.info("build_graph.update_user_node called", user_id=user_id)
    return {"status": "skipped"}
