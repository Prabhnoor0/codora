"""Neo4j async driver wrapper."""
from neo4j import AsyncGraphDatabase, AsyncDriver
from typing import Optional
import structlog

from config import settings

log = structlog.get_logger()

_driver: Optional[AsyncDriver] = None


async def init_neo4j():
    global _driver
    _driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
    )
    await _driver.verify_connectivity()
    await _create_constraints()
    log.info("Neo4j connected ✓", uri=settings.NEO4J_URI)


async def close_neo4j():
    global _driver
    if _driver:
        await _driver.close()


def get_driver() -> AsyncDriver:
    if _driver is None:
        raise RuntimeError("Neo4j driver not initialized")
    return _driver


async def _create_constraints():
    """Create uniqueness constraints and indexes."""
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Developer) REQUIRE d.github_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Repository) REQUIRE r.full_name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (f:File) REQUIRE (f.repo_id, f.path) IS NODE KEY",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Issue) REQUIRE (i.repo_id, i.number) IS NODE KEY",
        "CREATE INDEX IF NOT EXISTS FOR (s:Skill) ON (s.name)",
        "CREATE INDEX IF NOT EXISTS FOR (t:Technology) ON (t.name)",
    ]
    async with get_driver().session() as session:
        for stmt in constraints:
            try:
                await session.run(stmt)
            except Exception as e:
                log.warning("Constraint creation", stmt=stmt, error=str(e))
