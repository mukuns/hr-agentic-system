"""
Heading-aware chunker with token-window fallback.
Limits chunks to max 512 tokens with 50-token overlap.
Generates snippet metadata <= 200 chars.
Satisfies Requirement 1 (AC 2, 3).
"""

import re
from dataclasses import dataclass
from typing import List
from src.ingestion.parser import ParsedDocument

@dataclass
class PolicyChunk:
    chunk_id: str
    doc_id: str
    doc_title: str
    section_heading: str
    content: str
    snippet: str
    token_count: int

def estimate_tokens(text: str) -> int:
    """Estimates token count using whitespace and punctuation boundaries (~0.75 words per token)."""
    words = re.findall(r"\w+|[^\w\s]", text)
    return max(1, len(words))

def split_text_token_window(text: str, max_tokens: int = 512, overlap_tokens: int = 50) -> List[str]:
    """Splits text into windows of at most max_tokens with overlap_tokens."""
    words = text.split()
    if not words:
        return []
    
    # We estimate 1 token ~= 0.75 words, so max_words ~= max_tokens * 0.75
    max_words = int(max_tokens * 0.75)
    overlap_words = int(overlap_tokens * 0.75)
    
    if len(words) <= max_words:
        return [text]
        
    chunks = []
    start = 0
    step = max_words - overlap_words
    
    while start < len(words):
        end = min(start + max_words, len(words))
        chunk_text = " ".join(words[start:end])
        chunks.append(chunk_text)
        if end >= len(words):
            break
        start += step
        
    return chunks

def extract_snippet(text: str, max_length: int = 200) -> str:
    """Extracts a source snippet of no more than 200 characters."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= max_length:
        return cleaned
    # Cut off at last word boundary before max_length - 3
    truncated = cleaned[:max_length - 3]
    last_space = truncated.rfind(" ")
    if last_space > 50:
        truncated = truncated[:last_space]
    return truncated + "..."

def chunk_document(doc: ParsedDocument, max_chunk_tokens: int = 512, overlap_tokens: int = 50) -> List[PolicyChunk]:
    """
    Chunks a parsed document using heading-aware segmentation, applying
    token-window splitting for sections that exceed max_chunk_tokens.
    """
    chunks: List[PolicyChunk] = []
    chunk_index = 0
    
    for section in doc.sections:
        heading = section.heading.strip() if section.heading else "General"
        section_content = section.content.strip()
        if not section_content:
            continue
            
        estimated_toks = estimate_tokens(section_content)
        
        if estimated_toks <= max_chunk_tokens:
            chunk_index += 1
            chunk_id = f"{doc.doc_id}-C{chunk_index:03d}"
            snippet = extract_snippet(section_content, max_length=200)
            chunks.append(PolicyChunk(
                chunk_id=chunk_id,
                doc_id=doc.doc_id,
                doc_title=doc.title,
                section_heading=heading,
                content=section_content,
                snippet=snippet,
                token_count=estimated_toks
            ))
        else:
            # Section exceeds max tokens, split with token window & overlap
            sub_texts = split_text_token_window(section_content, max_tokens=max_chunk_tokens, overlap_tokens=overlap_tokens)
            for sub_idx, sub_text in enumerate(sub_texts):
                chunk_index += 1
                chunk_id = f"{doc.doc_id}-C{chunk_index:03d}"
                sub_heading = f"{heading} (Part {sub_idx + 1})" if len(sub_texts) > 1 else heading
                snippet = extract_snippet(sub_text, max_length=200)
                chunks.append(PolicyChunk(
                    chunk_id=chunk_id,
                    doc_id=doc.doc_id,
                    doc_title=doc.title,
                    section_heading=sub_heading,
                    content=sub_text,
                    snippet=snippet,
                    token_count=estimate_tokens(sub_text)
                ))
                
    return chunks
