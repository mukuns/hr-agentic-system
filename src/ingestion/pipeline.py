"""
Corpus Ingestion Pipeline.
Scans data/policy_corpus/, parses multi-format documents (Markdown, PDF, TXT),
chunks according to heading-aware rules, and indexes all chunks in RAGIndex.
Satisfies Requirement 1 (AC 1-8).
"""

import time
import logging
from pathlib import Path
from typing import List, Dict, Any

from src.ingestion.parser import parse_document
from src.ingestion.chunker import chunk_document, PolicyChunk
from src.rag.vector_store import RAGIndex

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class IngestionPipeline:
    def __init__(self, corpus_dir: Path, rag_index: RAGIndex):
        self.corpus_dir = Path(corpus_dir)
        self.rag_index = rag_index

    def run_ingestion(self) -> Dict[str, Any]:
        """
        Runs full ingestion of the Policy Corpus.
        Completes well within 5 minutes.
        Logs any corrupted or unparseable files and continues processing.
        """
        start_time = time.time()
        logger.info(f"Starting Policy Corpus ingestion from {self.corpus_dir}...")
        
        if not self.corpus_dir.exists():
            raise FileNotFoundError(f"Policy corpus directory does not exist: {self.corpus_dir}")
            
        supported_files = list(self.corpus_dir.glob("*.*"))
        # Filter out hidden or temp files
        supported_files = [f for f in supported_files if not f.name.startswith(".")]
        
        parsed_docs = []
        skipped_files = []
        all_chunks: List[PolicyChunk] = []
        total_tokens = 0
        
        for file_path in supported_files:
            try:
                doc = parse_document(file_path)
                if doc is None:
                    skipped_files.append((file_path.name, "Unsupported format or parsing failure"))
                    continue
                parsed_docs.append(doc)
                doc_chunks = chunk_document(doc, max_chunk_tokens=512, overlap_tokens=50)
                all_chunks.extend(doc_chunks)
                doc_tokens = sum(c.token_count for c in doc_chunks)
                total_tokens += doc_tokens
                logger.info(f"Parsed {file_path.name} ({doc.format}): {len(doc_chunks)} chunks, ~{doc_tokens} tokens")
            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}. Skipping file.")
                skipped_files.append((file_path.name, str(e)))

        # Store chunks in RAG Index
        logger.info(f"Indexing {len(all_chunks)} policy chunks in RAG Index...")
        self.rag_index.add_chunks(all_chunks)
        
        elapsed_seconds = round(time.time() - start_time, 2)
        # 1 page-equivalent = 400 tokens (Requirement 1, AC 6)
        page_equivalents = round(total_tokens / 400.0, 1)
        
        summary = {
            "status": "success",
            "documents_parsed": len(parsed_docs),
            "documents_skipped": len(skipped_files),
            "total_chunks": len(all_chunks),
            "total_tokens": total_tokens,
            "page_equivalents": page_equivalents,
            "elapsed_seconds": elapsed_seconds,
            "skipped_details": skipped_files
        }
        
        logger.info(
            f"Ingestion complete in {elapsed_seconds}s! "
            f"Processed {len(parsed_docs)} docs ({page_equivalents} page-equivalents, {len(all_chunks)} chunks)."
        )
        return summary

def main():
    base_dir = Path(__file__).resolve().parent.parent.parent
    corpus_path = base_dir / "data" / "policy_corpus"
    rag_index = RAGIndex()
    pipeline = IngestionPipeline(corpus_dir=corpus_path, rag_index=rag_index)
    result = pipeline.run_ingestion()
    print("Ingestion Result:", result)

if __name__ == "__main__":
    main()
