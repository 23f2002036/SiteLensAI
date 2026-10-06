"""
SiteLens AI — SOP Document Ingestion

Reads safety documents from data/sops/, chunks them with overlap,
generates embeddings, and stores them in the vector store.

Usage:
    python -m app.rag.ingest
    python -m app.rag.ingest --directory data/sops/ --chunk-size 500
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import sys
from pathlib import Path
from typing import Optional

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from app.rag.embeddings import EmbeddingEngine
from app.rag.vector_store import DocumentChunk, FAISSVectorStore

logger = logging.getLogger("sitelens.rag.ingest")


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    """
    Split text into overlapping chunks by token count (approx. words).

    Parameters
    ----------
    text : the full document text
    chunk_size : target tokens per chunk
    overlap : tokens of overlap between consecutive chunks
    """
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk.strip())
        start += chunk_size - overlap

    return chunks


def extract_sections(text: str) -> list[tuple[str, str]]:
    """
    Split markdown-style document into (section_title, section_text) pairs.
    Falls back to the full document as a single section.
    """
    # Split on markdown headers (## or #)
    sections = re.split(r'\n(?=#{1,3}\s)', text)
    results = []

    for section in sections:
        lines = section.strip().split('\n', 1)
        if len(lines) >= 2:
            title = lines[0].lstrip('#').strip()
            body = lines[1].strip()
        else:
            title = "General"
            body = section.strip()

        if body:
            results.append((title, body))

    if not results:
        results.append(("General", text.strip()))

    return results


def ingest_directory(
    directory: str | Path,
    chunk_size: int = 500,
    overlap: int = 50,
    store_path: Optional[str] = None,
):
    """
    Ingest all supported files from a directory into the vector store.

    Supported formats: .txt, .md
    """
    directory = Path(directory)
    if not directory.exists():
        logger.error("Directory not found: %s", directory)
        return

    # Collect files
    files = []
    for ext in ("*.txt", "*.md"):
        files.extend(directory.glob(ext))

    if not files:
        logger.warning("No .txt or .md files found in %s", directory)
        return

    logger.info("Found %d files to ingest from %s", len(files), directory)

    # Initialize engines
    embedder = EmbeddingEngine()
    store = FAISSVectorStore(
        index_path=store_path,
        dimension=embedder.dimension,
    )

    all_chunks: list[DocumentChunk] = []

    for filepath in sorted(files):
        logger.info("Processing: %s", filepath.name)

        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        if not text.strip():
            logger.warning("  Skipping empty file: %s", filepath.name)
            continue

        # Extract sections, then chunk each section
        sections = extract_sections(text)
        for section_title, section_body in sections:
            text_chunks = chunk_text(section_body, chunk_size, overlap)

            for i, chunk_text_content in enumerate(text_chunks):
                doc_chunk = DocumentChunk(
                    content=chunk_text_content,
                    chunk_id=f"{filepath.stem}_{section_title}_{i}",
                    source_file=filepath.name,
                    section=section_title,
                    metadata={
                        "source": filepath.name,
                        "section": section_title,
                        "chunk_index": i,
                        "total_chunks": len(text_chunks),
                    },
                )
                all_chunks.append(doc_chunk)

        logger.info(
            "  → %d sections, %d chunks from %s",
            len(sections),
            sum(1 for c in all_chunks if c.source_file == filepath.name),
            filepath.name,
        )

    if not all_chunks:
        logger.warning("No chunks generated. Nothing to ingest.")
        return

    # Generate embeddings
    logger.info("Generating embeddings for %d chunks...", len(all_chunks))
    texts = [c.content for c in all_chunks]
    embeddings = embedder.embed_batch(texts)

    # Store
    store.add(all_chunks, embeddings)
    store.save()

    logger.info(
        "✓ Ingestion complete: %d chunks from %d files stored in %s",
        len(all_chunks),
        len(files),
        store.index_path,
    )


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s │ %(name)-30s │ %(levelname)-7s │ %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="SiteLens AI — SOP Document Ingester")
    parser.add_argument(
        "--directory", "-d",
        default="data/sops",
        help="Directory containing SOP documents (default: data/sops)",
    )
    parser.add_argument("--chunk-size", type=int, default=500, help="Target chunk size in tokens")
    parser.add_argument("--overlap", type=int, default=50, help="Overlap between chunks")
    parser.add_argument("--store-path", default=None, help="Path to FAISS index directory")

    args = parser.parse_args()
    ingest_directory(args.directory, args.chunk_size, args.overlap, args.store_path)


if __name__ == "__main__":
    main()
