"""
Code and text embedding service.
Supports multiple backends: sentence-transformers (lightweight), CodeBERT, GraphCodeBERT.
"""
import numpy as np
from typing import Optional, Union
import structlog

from config import settings

log = structlog.get_logger()


class EmbeddingService:
    """Unified embedding service with model fallback."""

    def __init__(self, model_type: Optional[str] = None):
        self.model_type = model_type or settings.EMBEDDING_MODEL
        self._model = None
        self._tokenizer = None

    def _load_model(self):
        if self._model is not None:
            return

        if self.model_type == "lightweight":
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2",
                cache_folder=settings.MODELS_CACHE_DIR,
            )
            log.info("Loaded lightweight embedding model ✓")

        elif self.model_type == "codebert":
            from transformers import AutoTokenizer, AutoModel
            model_name = "microsoft/codebert-base"
            self._tokenizer = AutoTokenizer.from_pretrained(
                model_name, cache_dir=settings.MODELS_CACHE_DIR
            )
            self._model = AutoModel.from_pretrained(
                model_name, cache_dir=settings.MODELS_CACHE_DIR
            )
            self._model.eval()
            log.info("Loaded CodeBERT model ✓")

        elif self.model_type == "graphcodebert":
            from transformers import AutoTokenizer, AutoModel
            model_name = "microsoft/graphcodebert-base"
            self._tokenizer = AutoTokenizer.from_pretrained(
                model_name, cache_dir=settings.MODELS_CACHE_DIR
            )
            self._model = AutoModel.from_pretrained(
                model_name, cache_dir=settings.MODELS_CACHE_DIR
            )
            self._model.eval()
            log.info("Loaded GraphCodeBERT model ✓")

    def embed(self, texts: Union[str, list[str]]) -> np.ndarray:
        """Embed text(s) and return numpy array."""
        self._load_model()
        if isinstance(texts, str):
            texts = [texts]

        if self.model_type == "lightweight":
            embeddings = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            return embeddings

        else:
            # HuggingFace transformer models
            import torch
            inputs = self._tokenizer(
                texts,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True,
            )
            with torch.no_grad():
                outputs = self._model(**inputs)
            # Mean pooling
            token_embeddings = outputs.last_hidden_state
            attention_mask = inputs["attention_mask"]
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            embeddings = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
                input_mask_expanded.sum(1), min=1e-9
            )
            # L2 normalize
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
            return embeddings.numpy()

    def embed_single(self, text: str) -> list[float]:
        """Embed a single string and return a plain list for JSON serialization."""
        return self.embed(text)[0].tolist()

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Embed in batches."""
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embs = self.embed(batch)
            results.extend(embs.tolist())
        return results

    def chunk_code(self, code: str, max_chars: int = 1500) -> list[str]:
        """Split code into overlapping chunks for embedding."""
        lines = code.splitlines()
        chunks, current, current_len = [], [], 0

        for line in lines:
            line_len = len(line)
            if current_len + line_len > max_chars and current:
                chunks.append("\n".join(current))
                # Overlap: keep last 5 lines
                current = current[-5:]
                current_len = sum(len(l) for l in current)
            current.append(line)
            current_len += line_len

        if current:
            chunks.append("\n".join(current))

        return chunks if chunks else [code[:max_chars]]


# Singleton
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
