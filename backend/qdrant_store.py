"""Qdrant vector database client and collection management."""
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, OptimizersConfigDiff
from typing import Optional
import structlog

from config import settings

log = structlog.get_logger()

_client: Optional[AsyncQdrantClient] = None

# Collection naming conventions
CODE_COLLECTION_SUFFIX = "_code"
DOCS_COLLECTION_SUFFIX = "_docs"
USERS_COLLECTION = "users"


async def init_qdrant():
    global _client
    kwargs = {"host": settings.QDRANT_HOST, "port": settings.QDRANT_PORT}
    if settings.QDRANT_API_KEY:
        kwargs["api_key"] = settings.QDRANT_API_KEY
    _client = AsyncQdrantClient(**kwargs)

    # Ensure user collection exists
    await ensure_collection(USERS_COLLECTION, settings.EMBEDDING_DIM)
    log.info("Qdrant connected ✓", host=settings.QDRANT_HOST)


def get_client() -> AsyncQdrantClient:
    if _client is None:
        raise RuntimeError("Qdrant client not initialized")
    return _client


async def ensure_collection(name: str, dim: int):
    """Create collection if it doesn't exist."""
    client = get_client()
    existing = await client.get_collections()
    names = [c.name for c in existing.collections]
    if name not in names:
        await client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            optimizers_config=OptimizersConfigDiff(indexing_threshold=20000),
        )
        log.info("Qdrant collection created", name=name, dim=dim)


async def get_repo_collections(repo_id: str) -> tuple[str, str]:
    """Get or create collections for a repository."""
    code_col = f"{repo_id}{CODE_COLLECTION_SUFFIX}"
    docs_col = f"{repo_id}{DOCS_COLLECTION_SUFFIX}"
    dim = settings.EMBEDDING_DIM
    await ensure_collection(code_col, dim)
    await ensure_collection(docs_col, dim)
    return code_col, docs_col
