#!/usr/bin/env python3
"""
LibraryOfBabel Essay Generation API
Interfaces with local Ollama for essay generation using vector database content
Mobile-accessible API for generating sophisticated analyses
"""

from flask import Flask, request, jsonify, render_template_string
import psycopg2
import psycopg2.extras
import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import hashlib
import os
from threading import Thread
import queue

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class EssayGenerator:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': 5432
        }
        
        # Ollama configuration
        self.ollama_url = "http://localhost:11434/api/generate"
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'llama3.1:8b')
        
        # Essay generation queue for async processing
        self.generation_queue = {}
        
    def search_database(self, query: str, limit: int = 8) -> List[Dict]:
        """Search database for relevant passages"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Use full-text search with ranking
            cursor.execute("""
                SELECT 
                    c.content,
                    c.word_count,
                    c.chapter_number,
                    b.title,
                    b.author,
                    b.publication_year,
                    b.genre,
                    ts_rank_cd(c.search_vector, plainto_tsquery('english', %s)) as rank
                FROM chunks c
                JOIN books b ON c.book_id = b.book_id
                WHERE c.search_vector @@ plainto_tsquery('english', %s)
                AND c.word_count > 100
                ORDER BY rank DESC, c.word_count DESC
                LIMIT %s
            """, (query, query, limit))
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Database search error: {e}")
            return []
    
    def get_random_passages(self, limit: int = 4) -> List[Dict]:
        """Get random passages for serendipitous discovery"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cursor.execute("""
                SELECT 
                    c.content,
                    c.word_count,
                    c.chapter_number,
                    b.title,
                    b.author,
                    b.publication_year,
                    b.genre
                FROM chunks c
                JOIN books b ON c.book_id = b.book_id
                WHERE c.word_count > 200
                ORDER BY RANDOM()
                LIMIT %s
            """, (limit,))
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Random passage error: {e}")
            return []
    
    def generate_essay_prompt(self, topic: str, style: str, passages: List[Dict]) -> str:
        """Generate comprehensive essay prompt for Ollama"""
        
        # Prepare source material
        source_material = ""
        for i, passage in enumerate(passages, 1):
            source_material += f"\n**Source {i}:** {passage['author']} - {passage['title']}\n"
            source_material += f"Genre: {passage.get('genre', 'Unknown')}\n"
            source_material += f"Content: {passage['content'][:1000]}...\n"
        
        # Style-specific instructions
        style_instructions = {
            "academic": "Write in formal academic prose with sophisticated argumentation and theoretical framework. Use scholarly tone with complex sentence structures.",
            "journalistic": "Write in engaging journalistic style with narrative flow, concrete examples, and accessible language that builds complex arguments through storytelling.",
            "experimental": "Write in experimental, boundary-pushing prose that challenges conventional forms. Use unconventional structures and innovative approaches.",
            "analytical": "Write in precise analytical style focusing on logical argumentation, evidence-based reasoning, and systematic analysis."
        }
        
        style_instruction = style_instructions.get(style, style_instructions["journalistic"])
        
        prompt = f"""You are a brilliant intellectual writer tasked with creating a sophisticated essay on the topic: {topic}

WRITING STYLE: {style_instruction}

TASK: Create a 2000-3000 word essay that synthesizes insights from the provided source materials. Your essay should:

1. Develop original arguments that go beyond summarizing sources
2. Find unexpected connections between different authors and ideas  
3. Apply theoretical frameworks to contemporary issues
4. Generate novel insights through cross-domain synthesis
5. Maintain intellectual rigor while being engaging to read

REQUIRED ELEMENTS:
- Clear thesis and argumentation structure
- Integration of all provided sources
- Original theoretical framework or perspective
- Contemporary applications and implications
- Sophisticated analysis that advances understanding

SOURCE MATERIALS:
{source_material}

INSTRUCTIONS:
- Begin writing immediately - no preamble or meta-commentary
- Focus on generating genuine insights rather than summarizing
- Use the sources as launching points for original thinking
- Create compelling narrative flow that builds toward significant conclusions
- Aim for intellectual sophistication without academic jargon

Write the complete essay now:"""

        return prompt
    
    def generate_with_ollama(self, prompt: str) -> str:
        """Generate essay using local Ollama instance"""
        try:
            logger.info(f"Sending request to Ollama: {self.ollama_model}")
            
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.8,
                    "top_p": 0.9,
                    "top_k": 40,
                    "num_predict": 4000  # Allow longer responses
                }
            }
            
            response = requests.post(self.ollama_url, json=payload, timeout=300)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No response generated')
            else:
                logger.error(f"Ollama error: {response.status_code} - {response.text}")
                return f"Error: Ollama returned status {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "Error: Generation timed out (5 minutes)"
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return f"Error: {str(e)}"
    
    def generate_essay_async(self, essay_id: str, topic: str, style: str, use_search: bool = True, search_query: str = None):
        """Generate essay asynchronously"""
        try:
            # Update status
            self.generation_queue[essay_id]['status'] = 'gathering_sources'
            
            # Gather source material
            if use_search and search_query:
                passages = self.search_database(search_query, limit=6)
                if len(passages) < 3:  # If search yields few results, add random passages
                    passages.extend(self.get_random_passages(limit=4))
            else:
                passages = self.get_random_passages(limit=6)
            
            self.generation_queue[essay_id]['sources_found'] = len(passages)
            self.generation_queue[essay_id]['status'] = 'generating_essay'
            
            # Generate essay prompt
            prompt = self.generate_essay_prompt(topic, style, passages)
            
            # Generate with Ollama
            essay_content = self.generate_with_ollama(prompt)
            
            # Store results
            self.generation_queue[essay_id].update({
                'status': 'completed',
                'essay': essay_content,
                'sources': passages,
                'completed_at': datetime.now().isoformat(),
                'word_count': len(essay_content.split())
            })
            
        except Exception as e:
            self.generation_queue[essay_id].update({
                'status': 'error',
                'error': str(e),
                'completed_at': datetime.now().isoformat()
            })

# Initialize generator
generator = EssayGenerator()

# Web interface template
WEB_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <title>LibraryOfBabel Essay Generator</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 20px; background: #1a1a1a; color: #e0e0e0; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #ff6b6b; border-bottom: 2px solid #333; padding-bottom: 10px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; color: #ffd93d; }
        input, select, textarea { width: 100%; padding: 10px; border: 1px solid #444; background: #2a2a2a; color: #e0e0e0; border-radius: 4px; box-sizing: border-box; }
        button { background: #ff6b6b; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        button:hover { background: #e55555; }
        .status { margin-top: 20px; padding: 15px; background: #2a2a2a; border-radius: 4px; border-left: 4px solid #ffd93d; }
        .essay-output { margin-top: 20px; padding: 20px; background: #2a2a2a; border-radius: 4px; white-space: pre-wrap; line-height: 1.6; }
        .error { border-left-color: #ff4757; }
        .success { border-left-color: #2ed573; }
        .loading { border-left-color: #ffa502; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 LibraryOfBabel Essay Generator</h1>
        <p>Generate sophisticated essays using your personal knowledge corpus and local Ollama.</p>
        
        <form id="essayForm">
            <div class="form-group">
                <label for="topic">Essay Topic:</label>
                <input type="text" id="topic" placeholder="e.g., The epistemology of digital surveillance" required>
            </div>
            
            <div class="form-group">
                <label for="style">Writing Style:</label>
                <select id="style">
                    <option value="journalistic">Journalistic (Narrative-driven, accessible)</option>
                    <option value="academic">Academic (Formal, theoretical)</option>
                    <option value="analytical">Analytical (Logic-focused, systematic)</option>
                    <option value="experimental">Experimental (Boundary-pushing, innovative)</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="searchQuery">Search Query (optional):</label>
                <input type="text" id="searchQuery" placeholder="e.g., power knowledge surveillance">
                <small style="color: #888;">Leave blank for serendipitous source selection</small>
            </div>
            
            <button type="submit">🚀 Generate Essay</button>
        </form>
        
        <div id="status" style="display: none;"></div>
        <div id="output" style="display: none;"></div>
    </div>

    <script>
        let currentEssayId = null;
        
        document.getElementById('essayForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const topic = document.getElementById('topic').value;
            const style = document.getElementById('style').value;
            const searchQuery = document.getElementById('searchQuery').value;
            
            const statusDiv = document.getElementById('status');
            const outputDiv = document.getElementById('output');
            
            statusDiv.style.display = 'block';
            statusDiv.className = 'status loading';
            statusDiv.innerHTML = '🔄 Starting essay generation...';
            outputDiv.style.display = 'none';
            
            try {
                // Start generation
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ topic, style, search_query: searchQuery })
                });
                
                const data = await response.json();
                currentEssayId = data.essay_id;
                
                // Poll for status
                pollStatus();
                
            } catch (error) {
                statusDiv.className = 'status error';
                statusDiv.innerHTML = '❌ Error: ' + error.message;
            }
        });
        
        async function pollStatus() {
            if (!currentEssayId) return;
            
            try {
                const response = await fetch(`/api/status/${currentEssayId}`);
                const data = await response.json();
                
                const statusDiv = document.getElementById('status');
                const outputDiv = document.getElementById('output');
                
                if (data.status === 'gathering_sources') {
                    statusDiv.innerHTML = '📚 Gathering relevant sources from knowledge base...';
                } else if (data.status === 'generating_essay') {
                    statusDiv.innerHTML = `🤖 Generating essay with Ollama (found ${data.sources_found || 0} relevant sources)...`;
                } else if (data.status === 'completed') {
                    statusDiv.className = 'status success';
                    statusDiv.innerHTML = `✅ Essay completed! Word count: ${data.word_count || 'unknown'}`;
                    
                    outputDiv.style.display = 'block';
                    outputDiv.className = 'essay-output';
                    outputDiv.innerHTML = data.essay;
                    
                    return; // Stop polling
                } else if (data.status === 'error') {
                    statusDiv.className = 'status error';
                    statusDiv.innerHTML = '❌ Error: ' + data.error;
                    return; // Stop polling
                }
                
                // Continue polling
                setTimeout(pollStatus, 2000);
                
            } catch (error) {
                console.error('Polling error:', error);
                setTimeout(pollStatus, 5000); // Retry after longer delay
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the web interface"""
    return render_template_string(WEB_INTERFACE)

@app.route('/api/generate', methods=['POST'])
def generate_essay():
    """Start essay generation"""
    try:
        data = request.json
        topic = data.get('topic', '').strip()
        style = data.get('style', 'journalistic')
        search_query = data.get('search_query', '').strip()
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        # Generate unique essay ID
        essay_id = hashlib.md5(f"{topic}{time.time()}".encode()).hexdigest()[:8]
        
        # Initialize queue entry
        generator.generation_queue[essay_id] = {
            'topic': topic,
            'style': style,
            'search_query': search_query,
            'status': 'queued',
            'created_at': datetime.now().isoformat()
        }
        
        # Start generation in background thread
        use_search = bool(search_query)
        thread = Thread(target=generator.generate_essay_async, 
                       args=(essay_id, topic, style, use_search, search_query))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'essay_id': essay_id,
            'status': 'queued',
            'message': 'Essay generation started'
        })
        
    except Exception as e:
        logger.error(f"Generation start error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<essay_id>')
def get_status(essay_id):
    """Get essay generation status"""
    if essay_id not in generator.generation_queue:
        return jsonify({'error': 'Essay ID not found'}), 404
    
    return jsonify(generator.generation_queue[essay_id])

@app.route('/api/essays')
def list_essays():
    """List all generated essays"""
    essays = []
    for essay_id, data in generator.generation_queue.items():
        essays.append({
            'essay_id': essay_id,
            'topic': data.get('topic'),
            'status': data.get('status'),
            'created_at': data.get('created_at'),
            'completed_at': data.get('completed_at'),
            'word_count': data.get('word_count')
        })
    
    return jsonify({'essays': essays})

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        conn = psycopg2.connect(**generator.db_config)
        conn.close()
        db_status = "connected"
    except:
        db_status = "error"
    
    try:
        # Test Ollama connection
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        ollama_status = "connected" if response.status_code == 200 else "error"
    except:
        ollama_status = "error"
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'ollama': ollama_status,
        'model': generator.ollama_model,
        'queue_size': len(generator.generation_queue)
    })

if __name__ == '__main__':
    print("🚀 LibraryOfBabel Essay Generation API")
    print("=" * 50)
    print(f"🌐 Web interface: http://localhost:5570")
    print(f"🔗 API endpoint: http://localhost:5570/api/generate")
    print(f"📊 Health check: http://localhost:5570/api/health")
    print(f"🤖 Ollama model: {generator.ollama_model}")
    print("📱 Mobile accessible - bookmark the URL!")
    print()
    
    app.run(host='0.0.0.0', port=5570, debug=False)