"""
LibraryOfBabel Standardized Upload API
=====================================

Dr. Sarah Chen (陈雪芳) - REST API Standardization
LEVEL 2 RESOURCE: /api/upload

Handles EPUB file uploads with processing pipeline:
1. File validation & storage
2. EPUB processing (metadata + content extraction)
3. Text chunking (hierarchical)
4. Database ingestion (books + chunks)
5. Embedding queue (background nomic embedding)

PRODUCTION READY
"""

import os
import sys
import uuid
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .auth import require_auth_unless_localhost
from .response_helpers import create_success_response, create_error_response, init_response_timing

logger = logging.getLogger(__name__)
standardized_upload_bp = Blueprint('standardized_upload', __name__)

# Configuration
UPLOAD_FOLDER = Path('ebooks/uploads')
PROCESSED_FOLDER = Path('ebooks/processed')
ALLOWED_EXTENSIONS = {'epub'}
MAX_FILE_SIZE_MB = 100

# Ensure folders exist
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)

# Track processing jobs
processing_jobs: Dict[str, Dict[str, Any]] = {}
processing_jobs_lock = threading.Lock()

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size_mb(file_path: Path) -> float:
    """Get file size in MB"""
    try:
        return file_path.stat().st_size / (1024 * 1024)
    except:
        return 0.0

@standardized_upload_bp.before_request
def before_request():
    """Initialize response timing"""
    init_response_timing()

@standardized_upload_bp.route('/api/upload', methods=['POST', 'GET'])
@require_auth_unless_localhost
def upload_endpoint():
    """
    LEVEL 2: Standardized Upload API

    POST: Upload EPUB file(s) for processing
    - Files: multipart/form-data with 'files' field
    - Returns: job_id for tracking processing status

    GET: Check processing status
    - job_id: string (required)
    - Returns: processing status and progress
    """
    try:
        if request.method == 'GET':
            return _handle_status()
        else:
            return _handle_upload()
    except Exception as e:
        logger.error(f"Upload endpoint error: {e}")
        return create_error_response(str(e), 500)


def _handle_upload():
    """Handle file upload"""
    if 'files' not in request.files:
        return create_error_response('No files provided', 400)

    files = request.files.getlist('files')
    if not files or all(f.filename == '' for f in files):
        return create_error_response('No files selected', 400)

    # Create job
    job_id = str(uuid.uuid4())[:8]
    job_timestamp = datetime.now().isoformat()

    uploaded_files = []
    errors = []

    for file in files:
        if file.filename == '':
            continue

        if not allowed_file(file.filename):
            errors.append(f"{file.filename}: Only EPUB files allowed")
            continue

        filename = secure_filename(file.filename)
        # Add timestamp to avoid collisions
        unique_filename = f"{job_id}_{filename}"
        file_path = UPLOAD_FOLDER / unique_filename

        try:
            file.save(str(file_path))

            # Check file size
            size_mb = get_file_size_mb(file_path)
            if size_mb > MAX_FILE_SIZE_MB:
                file_path.unlink()  # Delete oversized file
                errors.append(f"{filename}: File too large ({size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB)")
                continue

            uploaded_files.append({
                'filename': filename,
                'path': str(file_path),
                'size_mb': round(size_mb, 2),
                'status': 'uploaded'
            })

        except Exception as e:
            errors.append(f"{filename}: Upload failed - {str(e)}")

    if not uploaded_files:
        return create_error_response(f'No valid files uploaded. Errors: {errors}', 400)

    # Create job record
    with processing_jobs_lock:
        processing_jobs[job_id] = {
            'job_id': job_id,
            'created_at': job_timestamp,
            'status': 'queued',
            'files': uploaded_files,
            'errors': errors,
            'progress': {
                'total': len(uploaded_files),
                'processed': 0,
                'current_file': None,
                'current_stage': None
            },
            'results': []
        }

    # Start processing in background
    thread = threading.Thread(target=_process_job, args=(job_id,))
    thread.daemon = True
    thread.start()

    return create_success_response({
        'job_id': job_id,
        'files_uploaded': len(uploaded_files),
        'files': uploaded_files,
        'errors': errors if errors else None,
        'status': 'processing_started',
        'status_url': f'/api/upload?job_id={job_id}'
    })


def _handle_status():
    """Handle status check"""
    job_id = request.args.get('job_id')

    if not job_id:
        # Return list of recent jobs
        with processing_jobs_lock:
            recent_jobs = [
                {
                    'job_id': j['job_id'],
                    'created_at': j['created_at'],
                    'status': j['status'],
                    'files_count': len(j['files'])
                }
                for j in list(processing_jobs.values())[-10:]
            ]
            total_jobs = len(processing_jobs)
        return create_success_response({
            'jobs': recent_jobs,
            'total_jobs': total_jobs
        })

    with processing_jobs_lock:
        if job_id not in processing_jobs:
            return create_error_response(f'Job {job_id} not found', code="JOB_NOT_FOUND", status_code=404)
        job = processing_jobs[job_id]
    return create_success_response(job)


def _chunk_to_dict(chunk) -> Dict:
    """Convert TextChunk dataclass to dictionary for database insertion"""
    return {
        'chunk_id': chunk.chunk_id,
        'chunk_type': chunk.chunk_type.value if hasattr(chunk.chunk_type, 'value') else str(chunk.chunk_type),
        'title': chunk.title,
        'content': chunk.content,
        'word_count': chunk.word_count,
        'character_count': chunk.character_count,
        'chapter_number': chunk.chapter_number,
        'section_number': chunk.section_number,
        'paragraph_number': chunk.paragraph_number,
        'start_position': chunk.start_position,
        'end_position': chunk.end_position,
        'parent_chunk_id': chunk.parent_chunk_id
    }


def _ingest_book_direct(db_config: Dict, book_data: Dict, chunks: list) -> Optional[int]:
    """Direct database ingestion without using DatabaseIngestor class"""
    import psycopg2

    conn = None
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Extract publication year
        publication_year = None
        pub_date = book_data.get('publication_date', '')
        if pub_date:
            try:
                publication_year = int(pub_date[:4]) if len(pub_date) >= 4 else None
            except (ValueError, TypeError):
                pass

        # Insert author first if provided
        author_id = None
        author = book_data.get('author', '')
        if author:
            cursor.execute("SELECT author_id FROM authors WHERE name = %s", (author,))
            result = cursor.fetchone()
            if result:
                author_id = result[0]
            else:
                cursor.execute("INSERT INTO authors (name) VALUES (%s) RETURNING author_id", (author,))
                author_id = cursor.fetchone()[0]

        # Insert book
        cursor.execute("""
            INSERT INTO books (
                title, author, author_id, publisher, publication_date,
                publication_year, language, isbn, description, word_count,
                source_location, import_source
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING book_id
        """, (
            book_data.get('title', 'Unknown'),
            author,
            author_id,
            book_data.get('publisher', ''),
            book_data.get('publication_date', ''),
            publication_year,
            book_data.get('language', 'english'),
            book_data.get('isbn', ''),
            book_data.get('description', ''),
            book_data.get('word_count', 0),
            book_data.get('source_file', ''),
            'frontend_upload'
        ))
        book_id = cursor.fetchone()[0]
        conn.commit()  # Commit book first

        # Insert chunks with ON CONFLICT to handle duplicates gracefully
        chunks_inserted = 0
        for chunk in chunks:
            chunk_dict = _chunk_to_dict(chunk) if hasattr(chunk, 'chunk_id') else chunk
            # Generate unique chunk_id with book_id prefix to avoid collisions
            chunk_id = f"book{book_id}_{chunk_dict.get('chunk_id', '')}"
            try:
                cursor.execute("""
                    INSERT INTO chunks (
                        chunk_id, book_id, chunk_type, title, content,
                        word_count, character_count, chapter_number,
                        section_number, paragraph_number, start_position,
                        end_position, parent_chunk_id
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (chunk_id) DO NOTHING
                """, (
                    chunk_id,
                    book_id,
                    chunk_dict.get('chunk_type'),
                    chunk_dict.get('title', ''),
                    chunk_dict.get('content', ''),
                    chunk_dict.get('word_count', 0),
                    chunk_dict.get('character_count', 0),
                    chunk_dict.get('chapter_number'),
                    chunk_dict.get('section_number'),
                    chunk_dict.get('paragraph_number'),
                    chunk_dict.get('start_position', 0),
                    chunk_dict.get('end_position', 0),
                    chunk_dict.get('parent_chunk_id')
                ))
                if cursor.rowcount > 0:
                    chunks_inserted += 1
            except Exception as e:
                logger.warning(f"Failed to insert chunk: {e}")
                conn.rollback()  # Rollback just this chunk
                continue

        conn.commit()
        conn.close()

        logger.info(f"Ingested book_id={book_id} with {chunks_inserted} chunks")
        return book_id

    except Exception as e:
        logger.error(f"Database ingestion failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        raise


def _embed_book_chunks(db_config: Dict, book_id: int, total_chunks: int, job_id: str) -> int:
    """Generate embeddings for all chunks of a book using Ollama"""
    import requests as http_requests
    import psycopg2

    ollama_base = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434" if os.getenv("RUNNING_IN_CONTAINER") == "true" else "http://localhost:11434")
    ollama_url = f"{ollama_base}/api/embed"
    model = "nomic-embed-text-v2-moe"
    embedded = 0

    conn = psycopg2.connect(**db_config)
    try:
        cur = conn.cursor()
        # Get all chunks for this book that don't have embeddings yet
        cur.execute("""
            SELECT c.chunk_id, c.content
            FROM chunks c
            LEFT JOIN chunk_embeddings ce ON c.chunk_id = ce.chunk_id AND ce.embedding_model = %s
            WHERE c.book_id = %s AND ce.chunk_id IS NULL AND c.content IS NOT NULL
        """, (model, book_id))
        rows = cur.fetchall()

        for chunk_id, content in rows:
            if not content or len(content.strip()) < 10:
                continue
            try:
                # Truncate to model max length
                text = content[:8000]
                resp = http_requests.post(ollama_url, json={"model": model, "input": text}, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                embedding = data.get("embeddings", [[]])[0]
                if not embedding:
                    continue

                cur.execute("""
                    INSERT INTO chunk_embeddings (chunk_id, book_id, embedding_model, embedding_dimension, embedding_vector)
                    VALUES (%s, %s, %s, %s, %s::vector)
                    ON CONFLICT (chunk_id, embedding_model) DO NOTHING
                """, (chunk_id, book_id, model, len(embedding), str(embedding)))
                embedded += 1

                if embedded % 20 == 0:
                    conn.commit()
                    logger.info(f"[{job_id}] Embedded {embedded}/{len(rows)} chunks")

            except Exception as e:
                logger.warning(f"[{job_id}] Embedding failed for chunk {chunk_id}: {e}")
                continue

        conn.commit()
    finally:
        conn.close()

    logger.info(f"[{job_id}] Embedding complete: {embedded} chunks embedded for book_id={book_id}")
    return embedded


def _process_job(job_id: str):
    """Process uploaded files in background"""
    with processing_jobs_lock:
        if job_id not in processing_jobs:
            return
        job = processing_jobs[job_id]
    job['status'] = 'processing'

    try:
        # Import processing components
        from epub_processor import EPUBProcessor
        from text_chunker import TextChunker

        # Initialize processors
        epub_processor = EPUBProcessor()
        chunker = TextChunker()

        db_config = {
            'host': 'localhost',
            'database': 'knowledge_base',
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': 5432
        }

        for i, file_info in enumerate(job['files']):
            file_path = Path(file_info['path'])
            filename = file_info['filename']

            job['progress']['current_file'] = filename
            job['progress']['current_stage'] = 'extracting'

            result = {
                'filename': filename,
                'status': 'processing',
                'stages': {}
            }

            try:
                # Stage 1: EPUB Processing
                logger.info(f"[{job_id}] Processing EPUB: {filename}")
                job['progress']['current_stage'] = 'extracting'

                metadata, chapters = epub_processor.process_epub(str(file_path))
                result['stages']['extraction'] = {
                    'status': 'complete',
                    'title': metadata.title,
                    'author': metadata.author,
                    'chapters': len(chapters),
                    'words': metadata.total_words
                }

                # Stage 2: Chunking
                logger.info(f"[{job_id}] Chunking: {metadata.title}")
                job['progress']['current_stage'] = 'chunking'

                chunks = chunker.chunk_book(metadata, chapters)
                result['stages']['chunking'] = {
                    'status': 'complete',
                    'chunks_created': len(chunks)
                }

                # Stage 3: Database Ingestion
                logger.info(f"[{job_id}] Ingesting: {metadata.title}")
                job['progress']['current_stage'] = 'ingesting'

                book_data = {
                    'title': metadata.title,
                    'author': metadata.author,
                    'publisher': metadata.publisher,
                    'publication_date': metadata.publication_date,
                    'language': metadata.language,
                    'isbn': metadata.isbn,
                    'description': metadata.description,
                    'word_count': metadata.total_words,
                    'source_file': filename
                }

                book_id = _ingest_book_direct(db_config, book_data, chunks)

                result['stages']['ingestion'] = {
                    'status': 'complete',
                    'book_id': book_id,
                    'chunks_ingested': len(chunks)
                }

                # Stage 4: Generate embeddings inline
                logger.info(f"[{job_id}] Embedding: {metadata.title}")
                job['progress']['current_stage'] = 'embedding'
                result['stages']['embedding'] = {
                    'status': 'in_progress',
                    'model': 'nomic-embed-text-v2-moe',
                    'chunks_embedded': 0,
                    'chunks_total': len(chunks)
                }

                try:
                    embedded_count = _embed_book_chunks(db_config, book_id, len(chunks), job_id)
                    result['stages']['embedding'] = {
                        'status': 'complete',
                        'model': 'nomic-embed-text-v2-moe',
                        'chunks_embedded': embedded_count,
                        'chunks_total': len(chunks)
                    }
                except Exception as embed_err:
                    logger.warning(f"[{job_id}] Embedding failed (book still ingested): {embed_err}")
                    result['stages']['embedding'] = {
                        'status': 'failed',
                        'model': 'nomic-embed-text-v2-moe',
                        'error': str(embed_err),
                        'message': 'Book ingested but embedding failed — daemon will retry'
                    }

                result['status'] = 'complete'
                result['book_id'] = book_id

                # Move to processed folder
                processed_path = PROCESSED_FOLDER / file_path.name
                file_path.rename(processed_path)

            except Exception as e:
                logger.error(f"[{job_id}] Error processing {filename}: {e}")
                result['status'] = 'failed'
                result['error'] = str(e)
                job['errors'].append(f"{filename}: {str(e)}")

            job['results'].append(result)
            job['progress']['processed'] = i + 1

        # Update final status
        successful = sum(1 for r in job['results'] if r['status'] == 'complete')
        failed = sum(1 for r in job['results'] if r['status'] == 'failed')

        if failed == 0:
            job['status'] = 'complete'
        elif successful == 0:
            job['status'] = 'failed'
        else:
            job['status'] = 'partial'

        job['progress']['current_file'] = None
        job['progress']['current_stage'] = None

        logger.info(f"[{job_id}] Job complete: {successful} successful, {failed} failed")

        # Cleanup: keep only the last 100 jobs
        with processing_jobs_lock:
            if len(processing_jobs) > 100:
                sorted_jobs = sorted(processing_jobs.keys())
                for old_job in sorted_jobs[:-100]:
                    del processing_jobs[old_job]

    except Exception as e:
        logger.error(f"[{job_id}] Job failed: {e}")
        job['status'] = 'failed'
        job['errors'].append(f"Processing error: {str(e)}")
