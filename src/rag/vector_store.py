"""
Vector Database Storage and Search Implementation.
Combines SQLite storage with TF-IDF n-gram vectorization and cosine similarity retrieval.
Calibrated similarity thresholding ensures clean rejection of out-of-scope queries.
Satisfies Requirement 1 (AC 5) and Requirement 2 (AC 1, 4, 5).
"""

import sqlite3
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.ingestion.chunker import PolicyChunk

@dataclass
class SearchResult:
    chunk_id: str
    doc_id: str
    doc_title: str
    section_heading: str
    content: str
    snippet: str
    score: float

class RAGIndex:
    def __init__(self, db_path: Optional[str] = None, similarity_threshold: float = 0.08):
        if db_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.db_path = base_dir / "data" / "rag_index" / "rag_index.db"
        else:
            self.db_path = Path(db_path)
            
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.similarity_threshold = similarity_threshold
        self._init_db()
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._tfidf_matrix = None
        self._chunk_records: List[tuple] = []
        self._fit_corpus()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS policy_chunks (
            chunk_id TEXT PRIMARY KEY,
            doc_id TEXT NOT NULL,
            doc_title TEXT NOT NULL,
            section_heading TEXT NOT NULL,
            content TEXT NOT NULL,
            snippet TEXT NOT NULL,
            token_count INTEGER NOT NULL,
            embedding BLOB
        );
        """)
        conn.commit()
        conn.close()

    def _fit_corpus(self):
        """Loads all chunks and builds TF-IDF index for fast vector search."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
        SELECT chunk_id, doc_id, doc_title, section_heading, content, snippet, token_count
        FROM policy_chunks;
        """)
        self._chunk_records = cur.fetchall()
        conn.close()

        if self._chunk_records:
            corpus_texts = [
                f"{r[2]} {r[3]} {r[4]}" for r in self._chunk_records
            ]
            self._vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                sublinear_tf=True,
                stop_words='english'
            )
            self._tfidf_matrix = self._vectorizer.fit_transform(corpus_texts)
        else:
            self._vectorizer = None
            self._tfidf_matrix = None

    def add_chunks(self, chunks: List[PolicyChunk]):
        """Persists chunks into SQLite vector index and rebuilds memory vector matrix."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        for chunk in chunks:
            cur.execute("""
            INSERT OR REPLACE INTO policy_chunks (
                chunk_id, doc_id, doc_title, section_heading,
                content, snippet, token_count, embedding
            ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL);
            """, (
                chunk.chunk_id, chunk.doc_id, chunk.doc_title, chunk.section_heading,
                chunk.content, chunk.snippet, chunk.token_count
            ))
            
        conn.commit()
        conn.close()
        self._fit_corpus()

    def search(self, query: str, top_k: int = 5, score_threshold: Optional[float] = None) -> List[SearchResult]:
        """
        Retrieves top-k relevant chunks exceeding similarity score threshold.
        Satisfies Requirement 2 (AC 1, 4, 5).
        """
        if not self._chunk_records or self._vectorizer is None or self._tfidf_matrix is None:
            self._fit_corpus()
            if not self._chunk_records:
                return []

        threshold = score_threshold if score_threshold is not None else self.similarity_threshold
        query_vec = self._vectorizer.transform([query])
        
        sims = cosine_similarity(query_vec, self._tfidf_matrix)[0]
        
        results: List[SearchResult] = []
        for idx, score in enumerate(sims):
            if score >= threshold:
                r = self._chunk_records[idx]
                results.append(SearchResult(
                    chunk_id=r[0],
                    doc_id=r[1],
                    doc_title=r[2],
                    section_heading=r[3],
                    content=r[4],
                    snippet=r[5],
                    score=round(float(score), 4)
                ))
                
        # Sort descending by similarity score
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def get_policy_section(self, doc_name_or_id: str, section_heading: str) -> Optional[dict]:
        """
        Retrieves the full text of a specific section from a named policy document.
        Satisfies Requirement 6 (AC 3).
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        query = """
        SELECT chunk_id, doc_id, doc_title, section_heading, content
        FROM policy_chunks
        WHERE (doc_id = ? OR doc_title LIKE ?)
          AND section_heading LIKE ?;
        """
        cur.execute(query, (doc_name_or_id, f"%{doc_name_or_id}%", f"%{section_heading}%"))
        rows = cur.fetchall()
        conn.close()
        
        if not rows:
            return None
            
        full_content = "\n\n".join([r[4] for r in rows])
        return {
            "doc_id": rows[0][1],
            "doc_title": rows[0][2],
            "section_heading": rows[0][3],
            "content": full_content
        }

    def total_chunks_count(self) -> int:
        return len(self._chunk_records)
