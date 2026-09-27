"""
Embedding generator supporting local zero-dependency semantic vectorization
and optional Gemini API embeddings with automatic retry logic (3 retries, 2s backoff).
Satisfies Requirement 1 (AC 4, 8).
"""

import os
import time
import logging
import hashlib
import numpy as np
from typing import List, Optional

logger = logging.getLogger(__name__)

class EmbeddingEngine:
    def __init__(self, vector_dim: int = 256):
        self.vector_dim = vector_dim
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        self._fitted = False
        self._vocab = {}
        
    def _local_embed_text(self, text: str) -> np.ndarray:
        """
        Deterministic, lightweight subword/n-gram hashing vectorizer.
        Generates dense, L2-normalized float32 vectors of dimension `vector_dim`.
        Completely local, free, fast, and reproducible with zero external network dependency.
        """
        words = text.lower().split()
        vec = np.zeros(self.vector_dim, dtype=np.float32)
        
        if not words:
            return vec
            
        for word in words:
            # Word level hash
            h_word = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h_word % self.vector_dim
            sign = 1.0 if (h_word // self.vector_dim) % 2 == 0 else -1.0
            vec[idx] += sign * 1.5
            
            # Character n-grams (3 to 5 chars) for subword semantic matching
            if len(word) >= 3:
                for n in range(3, min(6, len(word) + 1)):
                    for i in range(len(word) - n + 1):
                        ngram = word[i:i+n]
                        h_ng = int(hashlib.md5(ngram.encode("utf-8")).hexdigest(), 16)
                        n_idx = h_ng % self.vector_dim
                        n_sign = 1.0 if (h_ng // self.vector_dim) % 2 == 0 else -1.0
                        vec[n_idx] += n_sign * 0.8

        # L2 Normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def embed_text(self, text: str) -> np.ndarray:
        """
        Embeds a single string with retry logic (up to 3 retries with 2-second delay).
        Satisfies Requirement 1 (AC 8).
        """
        max_retries = 3
        delay_seconds = 2.0
        
        for attempt in range(1, max_retries + 1):
            try:
                # If Gemini API key is configured and user desires cloud embeddings
                if self.gemini_api_key:
                    import httpx
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={self.gemini_api_key}"
                    resp = httpx.post(url, json={
                        "model": "models/text-embedding-004",
                        "content": {"parts": [{"text": text[:2000]}]}
                    }, timeout=10.0)
                    resp.raise_for_status()
                    values = resp.json()["embedding"]["values"]
                    vec = np.array(values, dtype=np.float32)
                    norm = np.linalg.norm(vec)
                    return vec / norm if norm > 0 else vec
                else:
                    return self._local_embed_text(text)
            except Exception as e:
                logger.warning(f"Embedding attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    time.sleep(delay_seconds)
                else:
                    logger.error(f"All {max_retries} embedding retries failed for text: {text[:50]}...")
                    # Fall back to local embedder if remote failed, or raise
                    return self._local_embed_text(text)
                    
        return self._local_embed_text(text)

    def embed_chunks(self, texts: List[str]) -> List[np.ndarray]:
        """Batch embeds a list of strings."""
        return [self.embed_text(t) for t in texts]
