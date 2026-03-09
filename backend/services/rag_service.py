"""
RAG (Retrieval Augmented Generation) pipeline.
Handles indexing repository into Qdrant and retrieval for LLM context.
"""
import uuid
from typing import Optional
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue, SearchRequest
import structlog

from config import settings
from qdrant_store import get_client, get_repo_collections
from services.embedding_service import get_embedding_service

log = structlog.get_logger()


class RAGService:
    def __init__(self):
        self.embedder = get_embedding_service()

    # ── Indexing ──────────────────────────────────────────────
    async def index_file(self, repo_id: str, file_path: str, content: str, metadata: dict = None):
        """Index a file's code chunks into Qdrant."""
        code_col, _ = await get_repo_collections(repo_id)
        client = get_client()

        chunks = self.embedder.chunk_code(content)
        points = []

        for i, chunk in enumerate(chunks):
            embedding = self.embedder.embed_single(chunk)
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{repo_id}:{file_path}:{i}"))
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "repo_id": repo_id,
                    "file_path": file_path,
                    "chunk_index": i,
                    "content": chunk[:2000],  # store truncated for display
                    "type": "code",
                    **(metadata or {}),
                },
            ))

        if points:
            await client.upsert(collection_name=code_col, points=points)

    async def index_document(self, repo_id: str, doc_type: str, content: str, metadata: dict = None):
        """Index documentation/README into Qdrant."""
        _, docs_col = await get_repo_collections(repo_id)
        client = get_client()

        # Split docs into paragraphs
        paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 50]
        points = []

        for i, para in enumerate(paragraphs[:200]):
            embedding = self.embedder.embed_single(para)
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{repo_id}:{doc_type}:{i}"))
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "repo_id": repo_id,
                    "doc_type": doc_type,
                    "chunk_index": i,
                    "content": para[:2000],
                    "type": "documentation",
                    **(metadata or {}),
                },
            ))

        if points:
            await client.upsert(collection_name=docs_col, points=points)

    # ── Retrieval ─────────────────────────────────────────────
    async def search_code(self, repo_id: str, query: str, top_k: int = 5) -> list[dict]:
        """Search code chunks semantically."""
        code_col, _ = await get_repo_collections(repo_id)
        client = get_client()

        query_embedding = self.embedder.embed_single(query)
        results = await client.search(
            collection_name=code_col,
            query_vector=query_embedding,
            limit=top_k,
            with_payload=True,
        )
        return [{"score": r.score, **r.payload} for r in results]

    async def search_docs(self, repo_id: str, query: str, top_k: int = 5) -> list[dict]:
        """Search documentation chunks."""
        _, docs_col = await get_repo_collections(repo_id)
        client = get_client()

        query_embedding = self.embedder.embed_single(query)
        results = await client.search(
            collection_name=docs_col,
            query_vector=query_embedding,
            limit=top_k,
            with_payload=True,
        )
        return [{"score": r.score, **r.payload} for r in results]

    async def hybrid_search(self, repo_id: str, query: str, top_k: int = 8) -> list[dict]:
        """Combined code + docs search with deduplication."""
        import asyncio
        code_results, doc_results = await asyncio.gather(
            self.search_code(repo_id, query, top_k=top_k // 2 + 2),
            self.search_docs(repo_id, query, top_k=top_k // 2 + 2),
        )
        combined = code_results + doc_results
        combined.sort(key=lambda x: x["score"], reverse=True)
        return combined[:top_k]

    async def build_rag_context(self, repo_id: str, query: str, max_tokens: int = 3000) -> str:
        """Build a context string from retrieved chunks for LLM augmentation."""
        results = await self.hybrid_search(repo_id, query, top_k=6)
        if not results:
            return ""

        context_parts = []
        char_count = 0

        for r in results:
            file_path = r.get("file_path", r.get("doc_type", "unknown"))
            content = r.get("content", "")
            snippet = f"### {file_path}\n```\n{content}\n```\n"

            if char_count + len(snippet) > max_tokens * 4:  # approx 4 chars/token
                break
            context_parts.append(snippet)
            char_count += len(snippet)

        return "\n".join(context_parts)

    async def find_similar_files(self, repo_id: str, description: str, top_k: int = 10) -> list[dict]:
        """Find files most relevant to an issue description."""
        code_results = await self.search_code(repo_id, description, top_k=top_k)
        # Group by file path and max score
        file_scores: dict[str, float] = {}
        for r in code_results:
            path = r.get("file_path", "")
            score = r.get("score", 0.0)
            if path not in file_scores or score > file_scores[path]:
                file_scores[path] = score

        return sorted(
            [{"file_path": k, "confidence": round(v * 100, 1)} for k, v in file_scores.items()],
            key=lambda x: -x["confidence"]
        )


# Singleton
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
