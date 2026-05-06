"""
LibraryOfBabel RAG (Retrieval-Augmented Generation) Endpoint
============================================================

Uses semantic search to retrieve relevant chunks from the library,
then passes them to Gemma 4 (via Ollama) for synthesis.
"""

import logging
import os
import time
import requests
from flask import Blueprint, request, jsonify
from .auth import public_read
from .database import get_db
from .nomic_intelligent_search import NomicIntelligentSearch
from .response_helpers import StandardResponse, start_response_timer
from .validation import validate_params

logger = logging.getLogger(__name__)

standardized_rag_bp = Blueprint('standardized_rag', __name__)

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://host.docker.internal:11434"
    if os.getenv("RUNNING_IN_CONTAINER") == "true"
    else "http://127.0.0.1:11434",
)
DEFAULT_MODEL = "qwen3.5:latest"
DEFAULT_CHUNKS = 8
DEFAULT_NUM_CTX = 8192


def _retrieve_chunks(query: str, limit: int = 8, genre: str = None):
    """Retrieve relevant chunks via semantic search."""
    searcher = NomicIntelligentSearch()
    results = searcher.search_chapters_semantic(query, limit=limit, genre_filter=genre)
    if not results:
        return []
    return results


def _build_rag_prompt(query: str, chunks: list, system_prompt: str = None) -> list:
    """Build chat messages with retrieved context."""
    if system_prompt is None:
        system_prompt = (
            "You are a knowledgeable librarian with access to a curated book library. "
            "Answer the user's question based on the provided book excerpts. "
            "Cite sources by title and author. Be concise and accurate. "
            "If the excerpts don't contain enough information, say so."
        )

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        title = chunk.get("title", chunk.get("book_title", "Unknown"))
        author = chunk.get("author", "Unknown")
        content = chunk.get("content", chunk.get("text", ""))
        score = chunk.get("similarity_score", chunk.get("score", 0))
        # Truncate very long chunks
        if len(content) > 2000:
            content = content[:2000] + "..."
        context_parts.append(
            f"[Source {i}] \"{title}\" by {author} (relevance: {score:.2f})\n{content}"
        )

    context_block = "\n\n---\n\n".join(context_parts)

    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Book excerpts:\n\n{context_block}\n\n---\n\nQuestion: {query}",
        },
    ]


def _call_gemma(messages: list, model: str = DEFAULT_MODEL, num_ctx: int = DEFAULT_NUM_CTX):
    """Call Gemma via Ollama REST API (IPv4 to avoid macOS dual-server issue)."""
    t0 = time.time()
    resp = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_ctx": num_ctx,
                "temperature": 0.3,
            },
        },
        timeout=120,
    )
    elapsed_ms = (time.time() - t0) * 1000

    if resp.status_code != 200:
        raise RuntimeError(f"Ollama returned {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    return {
        "answer": data["message"]["content"],
        "model": model,
        "inference_time_ms": round(elapsed_ms, 1),
        "eval_count": data.get("eval_count"),
        "prompt_eval_count": data.get("prompt_eval_count"),
    }


@standardized_rag_bp.route("/api/rag", methods=["GET"])
@public_read
def rag_endpoint():
    """
    RAG endpoint: semantic search + Gemma 4 synthesis.

    Query params:
        q       - search query (required)
        limit   - number of chunks to retrieve (default 8, max 20)
        genre   - optional genre filter
        model   - Ollama model name (default gemma4:e4b)
        system  - custom system prompt (optional)
    """
    request_id = start_response_timer()
    query = request.args.get("q", "").strip()
    if not query:
        return StandardResponse.create_error_response(
            message="Missing required parameter: q", code="MISSING_PARAM", status_code=400, request_id=request_id
        )
    limit = min(int(request.args.get("limit", DEFAULT_CHUNKS)), 20)
    genre = request.args.get("genre")
    model = request.args.get("model", DEFAULT_MODEL)
    system_prompt = request.args.get("system")

    # 1. Retrieve chunks
    try:
        chunks = _retrieve_chunks(query, limit=limit, genre=genre)
    except Exception as e:
        logger.warning(f"RAG chunk retrieval failed: {e}")
        chunks = []
    if not chunks:
        return StandardResponse.create_error_response(
            message="No relevant chunks found for query",
            code="RAG_NO_RESULTS",
            details={"query": query},
            status_code=404,
            request_id=request_id,
        )

    # 2. Build prompt with context
    messages = _build_rag_prompt(query, chunks, system_prompt=system_prompt)

    # 3. Call Gemma
    try:
        result = _call_gemma(messages, model=model)
    except Exception as e:
        logger.error(f"Gemma inference failed: {e}")
        return StandardResponse.create_error_response(
            message=f"LLM inference failed: {str(e)}",
            code="RAG_INFERENCE_ERROR",
            details={"model": model, "query": query},
            status_code=502,
            request_id=request_id,
        )

    # 4. Build response
    sources = []
    for chunk in chunks:
        sources.append({
            "title": chunk.get("title", chunk.get("book_title")),
            "author": chunk.get("author"),
            "book_id": chunk.get("book_id"),
            "chunk_id": chunk.get("chunk_id"),
            "similarity": chunk.get("similarity_score", chunk.get("score")),
            "excerpt": (chunk.get("content", chunk.get("text", ""))[:300] + "...")
            if len(chunk.get("content", chunk.get("text", ""))) > 300
            else chunk.get("content", chunk.get("text", "")),
        })

    return StandardResponse.create_success_response(
        data={
            "answer": result["answer"],
            "sources": sources,
            "model": result["model"],
            "inference_time_ms": result["inference_time_ms"],
            "chunks_used": len(chunks),
        },
        message="RAG response generated",
        request_id=request_id,
    )
