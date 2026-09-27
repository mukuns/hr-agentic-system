"""
Document parsers for Markdown and PDF policy documents.
Handles multi-format parsing, error recovery, and corrupted file skipping.
Satisfies Requirement 1 (AC 1, 7).
"""

import os
import re
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

@dataclass
class DocumentSection:
    heading: str
    content: str

@dataclass
class ParsedDocument:
    doc_id: str
    title: str
    file_path: str
    format: str
    sections: List[DocumentSection] = field(default_factory=list)

def extract_metadata_from_text(text: str, default_id: str, default_title: str) -> tuple[str, str]:
    """Extracts Document ID and Title from document header if present."""
    doc_id = default_id
    title = default_title
    
    # Try finding Document ID: DOC-xxx
    id_match = re.search(r"\bDocument\s*ID:\s*(DOC-[\w-]+)", text, re.IGNORECASE)
    if id_match:
        doc_id = id_match.group(1).strip()
        
    # Try finding Title from Markdown '# Title' or first line
    title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip()
    elif not title or title == default_title:
        # Fallback to first non-empty line
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if lines:
            title = lines[0].replace("#", "").strip()
            
    return doc_id, title

def parse_markdown(file_path: Path) -> ParsedDocument:
    """Parses a Markdown document into structured sections based on headings."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
    except Exception as e:
        raise ValueError(f"Failed to read markdown file {file_path.name}: {e}")

    default_id = file_path.stem.split("_")[0]
    default_title = file_path.stem.replace("_", " ").title()
    doc_id, title = extract_metadata_from_text(raw_text, default_id, default_title)

    sections: List[DocumentSection] = []
    current_heading = "General"
    current_lines: List[str] = []

    for line in raw_text.splitlines():
        # Match ## or ### headings
        heading_match = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading_match:
            # If line is main title (# Title), don't treat as section
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()
            
            if level == 1:
                # Top-level doc title
                current_lines.append(line)
                continue
                
            # Save accumulated section
            if current_lines:
                body = "\n".join(current_lines).strip()
                if body:
                    sections.append(DocumentSection(heading=current_heading, content=body))
                current_lines = []
            current_heading = heading_text
        else:
            current_lines.append(line)

    if current_lines:
        body = "\n".join(current_lines).strip()
        if body:
            sections.append(DocumentSection(heading=current_heading, content=body))

    if not sections:
        sections.append(DocumentSection(heading="General", content=raw_text.strip()))

    return ParsedDocument(
        doc_id=doc_id,
        title=title,
        file_path=str(file_path),
        format="markdown",
        sections=sections
    )

def parse_pdf(file_path: Path) -> ParsedDocument:
    """Parses a PDF document into structured sections using pypdf."""
    from pypdf import PdfReader
    try:
        reader = PdfReader(str(file_path))
        extracted_pages = []
        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                extracted_pages.append(text)
        full_text = "\n\n".join(extracted_pages)
    except Exception as e:
        raise ValueError(f"Failed to parse PDF file {file_path.name}: {e}")

    if not full_text.strip():
        raise ValueError(f"PDF {file_path.name} contains no extractable text.")

    default_id = file_path.stem.split("_")[0]
    default_title = file_path.stem.replace("_", " ").title()
    doc_id, title = extract_metadata_from_text(full_text, default_id, default_title)

    # Parse sections from PDF text using heuristic pattern: numbered headings or capitals
    sections: List[DocumentSection] = []
    current_heading = "General"
    current_lines: List[str] = []

    heading_pattern = re.compile(r"^(\d+\.?\s+[A-Z][\w\s,/-]+|\d+\.\d+\s+[A-Z][\w\s,/-]+)$")

    for line in full_text.splitlines():
        trimmed = line.strip()
        if heading_pattern.match(trimmed) and len(trimmed) < 100:
            if current_lines:
                body = "\n".join(current_lines).strip()
                if body:
                    sections.append(DocumentSection(heading=current_heading, content=body))
                current_lines = []
            current_heading = trimmed
        else:
            current_lines.append(line)

    if current_lines:
        body = "\n".join(current_lines).strip()
        if body:
            sections.append(DocumentSection(heading=current_heading, content=body))

    if not sections:
        sections.append(DocumentSection(heading="General", content=full_text.strip()))

    return ParsedDocument(
        doc_id=doc_id,
        title=title,
        file_path=str(file_path),
        format="pdf",
        sections=sections
    )

def parse_document(file_path: Path) -> Optional[ParsedDocument]:
    """
    Parses a document file. If unsupported or corrupted, logs error and returns None.
    Satisfies Requirement 1 (AC 7).
    """
    suffix = file_path.suffix.lower()
    try:
        if suffix in [".md", ".markdown"]:
            return parse_markdown(file_path)
        elif suffix == ".pdf":
            return parse_pdf(file_path)
        elif suffix in [".txt"]:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return ParsedDocument(
                doc_id=file_path.stem.split("_")[0],
                title=file_path.stem.replace("_", " ").title(),
                file_path=str(file_path),
                format="txt",
                sections=[DocumentSection(heading="General", content=content)]
            )
        else:
            logger.error(f"Skipping unsupported file format for {file_path.name} (extension: {suffix})")
            return None
    except Exception as e:
        logger.error(f"Failed to parse document {file_path.name}: {e}. Skipping document.")
        return None
