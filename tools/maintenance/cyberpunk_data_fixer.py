#!/usr/bin/env python3
"""
🔥 CYBERPUNK DATA FIXER'S BUILD BOOK API 🔥
Advanced book synthesis and reconstruction engine
"""
from flask import Flask, request, jsonify, send_file
import psycopg2
import os
import json
import re
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional
import hashlib

app = Flask(__name__)

class CyberpunkDataFixer:
    """The main data manipulation engine"""
    
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'database': 'knowledge_base',
            'user': os.getenv('USER'),
            'port': 5432
        }
    
    def get_connection(self):
        """Establish neural link to the data matrix"""
        return psycopg2.connect(**self.db_config)
    
    def build_book(self, book_identifier: str, format_type: str = "full") -> Dict[str, Any]:
        """
        🔧 CORE FUNCTION: Build/reconstruct a book from chunks
        
        Args:
            book_identifier: Title, author, or book_id
            format_type: "full", "summary", "outline", "quotes"
        """
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # Find the target book
            search_sql = """
            SELECT book_id, title, author 
            FROM books 
            WHERE title ILIKE %s OR author ILIKE %s OR book_id::text = %s
            """
            cur.execute(search_sql, (f"%{book_identifier}%", f"%{book_identifier}%", book_identifier))
            books = cur.fetchall()
            
            if not books:
                return {"error": "Book not found in the data matrix", "identifier": book_identifier}
            
            if len(books) > 1:
                return {
                    "multiple_matches": True,
                    "books": [{"id": bid, "title": title, "author": author} for bid, title, author in books],
                    "message": "Multiple targets detected. Specify exact book_id."
                }
            
            book_id, title, author = books[0]
            
            # Extract and reconstruct based on format
            if format_type == "full":
                result = self._build_full_book(cur, book_id, title, author)
            elif format_type == "summary":
                result = self._build_summary(cur, book_id, title, author)
            elif format_type == "outline":
                result = self._build_outline(cur, book_id, title, author)
            elif format_type == "quotes":
                result = self._extract_key_quotes(cur, book_id, title, author)
            else:
                result = {"error": f"Unknown format: {format_type}"}
            
            conn.close()
            return result
            
        except Exception as e:
            return {"error": f"Data corruption detected: {str(e)}"}
    
    def _build_full_book(self, cur, book_id: int, title: str, author: str) -> Dict[str, Any]:
        """Reconstruct complete book with overlap removal"""
        cur.execute("""
        SELECT chunk_id, chunk_type, chapter_number, section_number, content, word_count
        FROM chunks 
        WHERE book_id = %s
        ORDER BY 
            COALESCE(chapter_number, 0),
            COALESCE(section_number, 0),
            chunk_id
        """, (book_id,))
        
        chunks = cur.fetchall()
        
        # Smart overlap removal and reconstruction
        reconstructed_content = []
        previous_content = ""
        total_words = 0
        current_chapter = None
        
        for chunk_id, chunk_type, chapter_num, section_num, content, word_count in chunks:
            # Chapter boundaries
            if chapter_num and chapter_num != current_chapter:
                if current_chapter is not None:
                    reconstructed_content.append("\n" + "="*60 + "\n")
                reconstructed_content.append(f"CHAPTER {chapter_num}\n")
                current_chapter = chapter_num
            
            # Remove 50-word overlap (your chunking method)
            cleaned_content = self._remove_overlap(content, previous_content)
            reconstructed_content.append(cleaned_content + "\n\n")
            previous_content = content
            total_words += word_count or 0
        
        return {
            "book_id": book_id,
            "title": title,
            "author": author,
            "format": "full",
            "content": ''.join(reconstructed_content),
            "metadata": {
                "total_words": total_words,
                "chapters": len(set(c[2] for c in chunks if c[2])),
                "chunks_processed": len(chunks),
                "build_timestamp": datetime.now().isoformat()
            }
        }
    
    def _build_summary(self, cur, book_id: int, title: str, author: str) -> Dict[str, Any]:
        """Generate executive summary from key passages"""
        cur.execute("""
        SELECT content, word_count
        FROM chunks 
        WHERE book_id = %s AND chunk_type = 'chapter'
        ORDER BY word_count DESC
        LIMIT 10
        """, (book_id,))
        
        key_chunks = cur.fetchall()
        summary_content = []
        
        for i, (content, word_count) in enumerate(key_chunks, 1):
            # Extract first meaningful paragraph
            paragraphs = content.split('\n\n')
            meaningful_para = next((p for p in paragraphs if len(p) > 100), paragraphs[0] if paragraphs else "")
            summary_content.append(f"## Key Insight {i}\n{meaningful_para[:300]}...\n")
        
        return {
            "book_id": book_id,
            "title": title,
            "author": author,
            "format": "summary",
            "content": '\n'.join(summary_content),
            "metadata": {
                "summary_length": len(summary_content),
                "source_chunks": len(key_chunks)
            }
        }
    
    def _build_outline(self, cur, book_id: int, title: str, author: str) -> Dict[str, Any]:
        """Generate structured outline"""
        cur.execute("""
        SELECT DISTINCT chapter_number, content
        FROM chunks 
        WHERE book_id = %s AND chapter_number IS NOT NULL
        ORDER BY chapter_number
        """, (book_id,))
        
        chapters = cur.fetchall()
        outline = []
        
        for chapter_num, content in chapters:
            # Extract chapter title/topic
            first_line = content.split('\n')[0][:100]
            outline.append(f"{chapter_num}. {first_line}")
        
        return {
            "book_id": book_id,
            "title": title,
            "author": author,
            "format": "outline",
            "content": '\n'.join(outline),
            "metadata": {"chapters": len(outline)}
        }
    
    def _extract_key_quotes(self, cur, book_id: int, title: str, author: str) -> Dict[str, Any]:
        """Extract quotable passages"""
        cur.execute("""
        SELECT content
        FROM chunks 
        WHERE book_id = %s AND LENGTH(content) BETWEEN 100 AND 500
        ORDER BY RANDOM()
        LIMIT 20
        """, (book_id,))
        
        chunks = cur.fetchall()
        quotes = []
        
        for (content,) in chunks:
            # Find sentence-like structures
            sentences = re.split(r'[.!?]+', content)
            meaningful_sentences = [s.strip() for s in sentences if 50 < len(s.strip()) < 200]
            if meaningful_sentences:
                quotes.append(f'"{meaningful_sentences[0]}"')
        
        return {
            "book_id": book_id,
            "title": title,
            "author": author,
            "format": "quotes",
            "content": '\n\n'.join(quotes[:10]),
            "metadata": {"quotes_extracted": len(quotes)}
        }
    
    def _remove_overlap(self, current_content: str, previous_content: str) -> str:
        """Remove 50-word overlap between chunks"""
        if not previous_content:
            return current_content
        
        # Get last 50 words of previous content
        prev_words = previous_content.split()[-50:]
        curr_words = current_content.split()
        
        # Find overlap and remove
        overlap_found = False
        for i in range(min(50, len(curr_words))):
            if curr_words[:i+1] == prev_words[-(i+1):]:
                return ' '.join(curr_words[i+1:])
        
        return current_content
    
    def fusion_search(self, query: str, books: List[str] = None) -> Dict[str, Any]:
        """
        🔥 FUSION SEARCH: Cross-book knowledge synthesis
        """
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # Build search across specified books or all books
            if books:
                book_filter = "AND b.title = ANY(%s)"
                params = (query, query, books)
            else:
                book_filter = ""
                params = (query, query)
            
            fusion_sql = f"""
            SELECT 
                b.title,
                b.author,
                c.content,
                ts_rank_cd(to_tsvector('english', c.content), plainto_tsquery('english', %s)) as rank
            FROM chunks c 
            JOIN books b ON c.book_id = b.book_id 
            WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
            {book_filter}
            ORDER BY rank DESC
            LIMIT 15
            """
            
            cur.execute(fusion_sql, params)
            results = cur.fetchall()
            
            # Synthesize cross-book insights
            synthesis = {}
            for title, author, content, rank in results:
                if title not in synthesis:
                    synthesis[title] = {
                        "author": author,
                        "passages": [],
                        "relevance_score": 0
                    }
                synthesis[title]["passages"].append(content[:300])
                synthesis[title]["relevance_score"] += rank
            
            conn.close()
            
            return {
                "query": query,
                "cross_book_synthesis": synthesis,
                "total_sources": len(synthesis),
                "fusion_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Fusion matrix error: {str(e)}"}

# Initialize the fixer
fixer = CyberpunkDataFixer()

# 🔥 REST API ENDPOINTS 🔥

@app.route('/api/build', methods=['GET', 'POST'])
def build_book_endpoint():
    """
    🎯 PRIMARY ENDPOINT: Build/reconstruct any book
    
    GET /api/build?book=psalm&format=full
    POST /api/build {"book": "foucault", "format": "summary"}
    """
    if request.method == 'GET':
        book = request.args.get('book', '')
        format_type = request.args.get('format', 'full')
    else:
        data = request.get_json() or {}
        book = data.get('book', '')
        format_type = data.get('format', 'full')
    
    if not book:
        return jsonify({"error": "Book identifier required"}), 400
    
    result = fixer.build_book(book, format_type)
    return jsonify(result)

@app.route('/api/fusion', methods=['POST'])
def fusion_search_endpoint():
    """
    🔥 FUSION SEARCH: Cross-book knowledge synthesis
    
    POST /api/fusion {"query": "power", "books": ["Foucault", "Deleuze"]}
    """
    data = request.get_json() or {}
    query = data.get('query', '')
    books = data.get('books', None)
    
    if not query:
        return jsonify({"error": "Query required"}), 400
    
    result = fixer.fusion_search(query, books)
    return jsonify(result)

@app.route('/api/quick/<operation>', methods=['GET'])
def quick_operations(operation):
    """
    ⚡ QUICK SHORTCUTS for rapid access
    
    /api/quick/list - List all books
    /api/quick/random - Random book
    /api/quick/philosophy - Philosophy books
    """
    try:
        conn = fixer.get_connection()
        cur = conn.cursor()
        
        if operation == 'list':
            cur.execute("SELECT title, author FROM books ORDER BY title")
            books = [{"title": title, "author": author} for title, author in cur.fetchall()]
            return jsonify({"books": books, "count": len(books)})
        
        elif operation == 'random':
            cur.execute("SELECT title, author FROM books ORDER BY RANDOM() LIMIT 1")
            result = cur.fetchone()
            if result:
                title, author = result
                return jsonify({"random_pick": {"title": title, "author": author}})
            return jsonify({"error": "No books found"})
        
        elif operation == 'philosophy':
            cur.execute("""
            SELECT title, author FROM books 
            WHERE author ILIKE '%foucault%' OR author ILIKE '%deleuze%' 
               OR author ILIKE '%heidegger%' OR title ILIKE '%philosophy%'
            """)
            philosophy_books = [{"title": title, "author": author} for title, author in cur.fetchall()]
            return jsonify({"philosophy_collection": philosophy_books})
        
        else:
            return jsonify({"error": f"Unknown operation: {operation}"}), 404
        
        conn.close()
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download/<book_identifier>')
def download_book(book_identifier):
    """
    📥 DOWNLOAD: Get reconstructed book as file
    """
    result = fixer.build_book(book_identifier, "full")
    
    if "error" in result:
        return jsonify(result), 404
    
    # Create temporary file
    content = f"""CYBERPUNK DATA EXTRACTION
Title: {result['title']}
Author: {result['author']}
Extraction Time: {result['metadata']['build_timestamp']}
Total Words: {result['metadata']['total_words']:,}

{'='*80}

{result['content']}"""
    
    # Write to temp file
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8')
    temp_file.write(content)
    temp_file.close()
    
    filename = f"{result['title'].replace(' ', '_').replace('/', '_')}_extracted.txt"
    
    return send_file(temp_file.name, as_attachment=True, download_name=filename)

@app.route('/')
def index():
    """Main interface"""
    return jsonify({
        "status": "🔥 CYBERPUNK DATA FIXER ONLINE 🔥",
        "endpoints": {
            "build": "/api/build?book=<name>&format=<full|summary|outline|quotes>",
            "fusion": "/api/fusion (POST with query and books)",
            "quick": "/api/quick/<list|random|philosophy>",
            "download": "/api/download/<book_name>"
        },
        "example_shortcuts": [
            "curl 'http://localhost:8888/api/build?book=psalm&format=summary'",
            "curl 'http://localhost:8888/api/quick/philosophy'",
            "curl 'http://localhost:8888/api/quick/random'"
        ]
    })

if __name__ == '__main__':
    print("🔥" * 20)
    print("  CYBERPUNK DATA FIXER INITIALIZING...")
    print("  Neural link established: localhost:8888")
    print("  Status: READY TO JACK IN")
    print("🔥" * 20)
    app.run(host='0.0.0.0', port=8888, debug=True)