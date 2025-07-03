#!/usr/bin/env python3
"""
High-Quality Essay Generation API for M4 Mac (24GB RAM)
Optimized for maximum quality using larger models and sophisticated processing
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
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class HighQualityEssayGenerator:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': 5432
        }
        
        # Optimized for M4 Mac with 24GB RAM - use larger, higher quality models
        self.ollama_url = "http://localhost:11434/api/generate"
        
        # Model hierarchy - from highest to lowest quality
        self.model_hierarchy = [
            'qwen2.5:32b',      # 32B parameter model - highest quality
            'llama3.1:70b',     # 70B if available (quantized)
            'qwen2.5:14b',      # 14B parameter model - high quality
            'llama3.1:8b',      # 8B parameter model - good quality
            'qwen2.5:7b'        # 7B parameter model - fallback
        ]
        
        self.selected_model = self.select_best_available_model()
        self.generation_queue = {}
        
        # Enhanced processing settings for quality
        self.max_context_length = 32768  # Use full context for larger models
        self.quality_settings = {
            'temperature': 0.7,     # Slightly more focused for essay writing
            'top_p': 0.85,          # More selective token sampling
            'top_k': 30,            # Reduced for higher quality
            'repeat_penalty': 1.1,  # Prevent repetition
            'num_predict': 6000,    # Allow very long responses
            'num_ctx': 32768,       # Full context window
            'mirostat': 2,          # Advanced sampling for coherence
            'mirostat_eta': 0.1,    # Fine-tuned for essay quality
            'mirostat_tau': 5.0     # Target perplexity for coherence
        }
    
    def select_best_available_model(self) -> str:
        """Select the highest quality model available locally"""
        try:
            # Get list of available models
            response = requests.get("http://localhost:11434/api/tags", timeout=10)
            if response.status_code == 200:
                available_models = [model['name'] for model in response.json().get('models', [])]
                
                # Find the best available model from our hierarchy
                for model in self.model_hierarchy:
                    if model in available_models:
                        logger.info(f"Selected high-quality model: {model}")
                        return model
                
                # If none of our preferred models are available, use the first available
                if available_models:
                    model = available_models[0]
                    logger.warning(f"Using fallback model: {model}")
                    return model
            
        except Exception as e:
            logger.error(f"Error checking available models: {e}")
        
        # Ultimate fallback
        return 'llama3.1:8b'
    
    def get_sophisticated_sources(self, query: str, limit: int = 12) -> List[Dict]:
        """Get high-quality sources with simplified approach"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Simplified but reliable search
            cursor.execute("""
                SELECT 
                    c.content,
                    c.word_count,
                    c.chapter_number,
                    b.title,
                    b.author,
                    b.publication_year,
                    b.genre,
                    COALESCE(b.genre_confidence, 0.5) as genre_confidence
                FROM chunks c
                JOIN books b ON c.book_id = b.book_id
                WHERE c.search_vector @@ plainto_tsquery('english', %s)
                AND c.word_count > 150
                AND c.word_count < 2000
                ORDER BY ts_rank_cd(c.search_vector, plainto_tsquery('english', %s)) DESC
                LIMIT %s
            """, (query, query, limit))
            
            results = cursor.fetchall()
            conn.close()
            
            # Convert to dict list with safety checks
            safe_results = []
            for row in results:
                if row and hasattr(row, 'keys'):
                    safe_results.append(dict(row))
            
            logger.info(f"Source search returned {len(safe_results)} results")
            return safe_results
            
        except Exception as e:
            logger.error(f"Source search error: {e}")
            return []
    
    def create_advanced_essay_prompt(self, topic: str, style: str, passages: List[Dict]) -> str:
        """Create sophisticated prompt optimized for large language models"""
        
        # Enhanced source material preparation
        high_quality_sources = ""
        authors_covered = []
        genres_covered = []
        
        for i, passage in enumerate(passages, 1):
            authors_covered.append(passage['author'])
            if passage.get('genre'):
                genres_covered.append(passage['genre'])
            
            high_quality_sources += f"\n═══ SOURCE {i} ═══\n"
            high_quality_sources += f"Author: {passage['author']}\n"
            high_quality_sources += f"Work: {passage['title']}\n"
            high_quality_sources += f"Genre: {passage.get('genre', 'Unknown')}\n"
            high_quality_sources += f"Chapter: {passage.get('chapter_number', 'N/A')}\n"
            high_quality_sources += f"Quality Indicators: {passage['word_count']} words"
            if passage.get('genre_confidence'):
                high_quality_sources += f", {passage['genre_confidence']:.1%} genre confidence"
            high_quality_sources += f"\n\nCONTENT:\n{passage['content']}\n"
        
        # Advanced style configurations
        style_configurations = {
            "academic": {
                "tone": "Rigorous academic discourse with sophisticated theoretical engagement",
                "structure": "Traditional academic essay with thesis, body paragraphs with topic sentences, and substantive conclusion",
                "language": "Formal academic register with discipline-specific terminology and complex syntactic structures",
                "argumentation": "Systematic logical progression with extensive evidence and scholarly reasoning"
            },
            "journalistic": {
                "tone": "Engaging narrative journalism that weaves complex ideas into compelling story",
                "structure": "Feature article structure with hook, narrative development, and powerful conclusion",
                "language": "Sophisticated but accessible prose that builds complexity gradually",
                "argumentation": "Evidence-driven storytelling that reveals insights through concrete examples"
            },
            "experimental": {
                "tone": "Innovative, boundary-pushing intellectual exploration",
                "structure": "Non-traditional organization that mirrors the complexity of the ideas explored",
                "language": "Creative prose that uses form to enhance meaning",
                "argumentation": "Dialectical reasoning that embraces paradox and multiple perspectives"
            },
            "analytical": {
                "tone": "Precise, systematic analytical examination",
                "structure": "Clear analytical framework with methodical progression through evidence",
                "language": "Precise, technical language optimized for clarity and logical flow",
                "argumentation": "Deductive reasoning with careful attention to logical validity"
            }
        }
        
        config = style_configurations.get(style, style_configurations["journalistic"])
        
        # Create sophisticated prompt
        prompt = f"""You are an exceptional intellectual writer with deep expertise across philosophy, social theory, technology studies, and cultural criticism. You have been commissioned to write a substantial essay on: {topic}

WRITING SPECIFICATIONS:
• Style: {config['tone']}
• Structure: {config['structure']}
• Language: {config['language']}
• Argumentation: {config['argumentation']}

ESSAY REQUIREMENTS:
• Length: 3,500-4,500 words (substantial intellectual treatment)
• Intellectual Depth: Move beyond surface analysis to generate novel theoretical insights
• Cross-Domain Synthesis: Connect insights across the {len(set(genres_covered))} different genres represented in sources
• Original Framework: Develop a unique theoretical lens or analytical framework
• Contemporary Relevance: Connect historical/theoretical insights to current issues
• Sophisticated Argumentation: Build complex, multi-layered arguments with substantial evidence

SOURCE MATERIAL INTEGRATION:
You have access to {len(passages)} carefully selected sources spanning works by {len(set(authors_covered))} different authors including {', '.join(set(authors_covered)[:3])}{'...' if len(set(authors_covered)) > 3 else ''}. These sources cover {', '.join(set(genres_covered))} and provide rich material for synthesis.

INTELLECTUAL APPROACH:
1. Identify unexpected connections and tensions between sources
2. Develop original theoretical insights that emerge from synthesis
3. Apply historical/philosophical frameworks to contemporary phenomena
4. Generate novel hypotheses or frameworks for understanding the topic
5. Create compelling narrative that guides readers through complex ideas

QUALITY STANDARDS:
• Every paragraph should advance the argument in a meaningful way
• Ideas should be developed with sufficient depth and nuance
• Transitions should create intellectual momentum and logical flow
• Conclusion should offer genuine insights rather than mere summary
• Overall essay should make a significant intellectual contribution

SOURCE MATERIALS:
{high_quality_sources}

EXECUTION INSTRUCTIONS:
Begin writing immediately with a compelling opening that establishes intellectual stakes. Develop your argument systematically while maintaining narrative engagement. Draw connections that illuminate both the sources and the contemporary relevance of your topic. Aim for intellectual sophistication that respects the complexity of the material while remaining accessible to educated readers.

Write the complete essay now:"""

        return prompt
    
    def generate_with_ollama_optimized(self, prompt: str) -> str:
        """Generate essay using optimized settings for quality"""
        try:
            logger.info(f"Generating with high-quality model: {self.selected_model}")
            logger.info("Quality settings: Maximum context, optimized sampling for coherence")
            
            payload = {
                "model": self.selected_model,
                "prompt": prompt,
                "stream": False,
                "options": self.quality_settings
            }
            
            # Increased timeout for quality generation
            response = requests.post(self.ollama_url, json=payload, timeout=600)  # 10 minutes
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', 'No response generated')
                
                # Log generation statistics
                if 'eval_count' in result:
                    logger.info(f"Generated {result['eval_count']} tokens")
                if 'eval_duration' in result:
                    duration_seconds = result['eval_duration'] / 1e9
                    logger.info(f"Generation time: {duration_seconds:.1f} seconds")
                
                return generated_text
            else:
                logger.error(f"Ollama error: {response.status_code} - {response.text}")
                return f"Error: Ollama returned status {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "Error: Generation timed out (10 minutes) - this may indicate the model is working on a very high-quality response"
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return f"Error: {str(e)}"
    
    def generate_essay_async(self, essay_id: str, topic: str, style: str, use_search: bool = True, search_query: str = None):
        """Generate high-quality essay asynchronously"""
        try:
            # Update status
            self.generation_queue[essay_id]['status'] = 'analyzing_corpus'
            
            # Sophisticated source gathering
            if use_search and search_query:
                passages = self.get_sophisticated_sources(search_query, limit=10)
            else:
                # For non-search requests, get high-quality diverse sources
                passages = self.get_sophisticated_sources(topic, limit=8)
            
            if len(passages) < 3:
                # Fallback to ensure sufficient material
                conn = psycopg2.connect(**self.db_config)
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute("""
                    SELECT c.content, c.word_count, c.chapter_number, b.title, b.author, b.genre
                    FROM chunks c JOIN books b ON c.book_id = b.book_id
                    WHERE c.word_count > 300 AND b.genre IN ('Philosophy', 'Non-Fiction', 'Politics/Social Science')
                    ORDER BY RANDOM() LIMIT 6
                """)
                passages.extend([dict(row) for row in cursor.fetchall()])
                conn.close()
            
            self.generation_queue[essay_id]['sources_found'] = len(passages)
            self.generation_queue[essay_id]['status'] = 'crafting_essay'
            
            # Create sophisticated prompt
            prompt = self.create_advanced_essay_prompt(topic, style, passages)
            
            # Log prompt statistics for debugging
            logger.info(f"Prompt length: {len(prompt)} characters")
            logger.info(f"Using {len(passages)} sources from {len(set(p['author'] for p in passages))} authors")
            
            # Generate with optimized settings
            essay_content = self.generate_with_ollama_optimized(prompt)
            
            # Store comprehensive results
            self.generation_queue[essay_id].update({
                'status': 'completed',
                'essay': essay_content,
                'sources': passages,
                'completed_at': datetime.now().isoformat(),
                'word_count': len(essay_content.split()),
                'model_used': self.selected_model,
                'prompt_length': len(prompt),
                'sources_count': len(passages),
                'authors_count': len(set(p['author'] for p in passages))
            })
            
        except Exception as e:
            logger.error(f"Essay generation error: {e}")
            self.generation_queue[essay_id].update({
                'status': 'error',
                'error': str(e),
                'completed_at': datetime.now().isoformat()
            })

# Initialize generator
generator = HighQualityEssayGenerator()

# Enhanced web interface for quality generation
QUALITY_WEB_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <title>LibraryOfBabel Quality Essay Generator</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 20px; background: #0d1117; color: #c9d1d9; line-height: 1.6; }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { color: #58a6ff; border-bottom: 2px solid #21262d; padding-bottom: 15px; font-weight: 600; }
        .subtitle { color: #8b949e; margin-bottom: 30px; font-size: 16px; }
        .form-group { margin-bottom: 25px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #ffa657; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; }
        input, select, textarea { width: 100%; padding: 12px 16px; border: 1px solid #30363d; background: #21262d; color: #c9d1d9; border-radius: 6px; box-sizing: border-box; font-size: 16px; }
        input:focus, select:focus, textarea:focus { outline: none; border-color: #58a6ff; box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.1); }
        button { background: linear-gradient(135deg, #58a6ff, #1f6feb); color: white; padding: 14px 28px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: 600; transition: all 0.2s; }
        button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(88, 166, 255, 0.3); }
        .status { margin-top: 25px; padding: 20px; background: #21262d; border-radius: 8px; border-left: 4px solid #ffa657; }
        .essay-output { margin-top: 25px; padding: 25px; background: #0d1117; border: 1px solid #30363d; border-radius: 8px; white-space: pre-wrap; line-height: 1.8; font-family: 'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace; font-size: 14px; }
        .error { border-left-color: #f85149; }
        .success { border-left-color: #3fb950; }
        .loading { border-left-color: #d29922; }
        .model-info { background: #21262d; padding: 15px; border-radius: 6px; margin-bottom: 20px; border-left: 3px solid #58a6ff; }
        .quality-badge { display: inline-block; background: #238636; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; margin-left: 10px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-top: 15px; }
        .stat { background: #161b22; padding: 12px; border-radius: 6px; text-align: center; }
        .stat-value { font-size: 20px; font-weight: 600; color: #58a6ff; }
        .stat-label { font-size: 12px; color: #8b949e; text-transform: uppercase; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 LibraryOfBabel Quality Essay Generator</h1>
        <div class="subtitle">High-quality intellectual essays generated using your personal knowledge corpus and advanced language models</div>
        
        <div class="model-info">
            <strong>🤖 Current Model:</strong> <span id="currentModel">{{ current_model }}</span>
            <span class="quality-badge">24GB RAM OPTIMIZED</span>
            <div style="margin-top: 8px; font-size: 14px; color: #8b949e;">
                Advanced sampling • Extended context • Quality-focused generation
            </div>
        </div>
        
        <form id="essayForm">
            <div class="form-group">
                <label for="topic">Essay Topic</label>
                <input type="text" id="topic" placeholder="e.g., The epistemology of algorithmic knowledge systems" required>
            </div>
            
            <div class="form-group">
                <label for="style">Writing Style</label>
                <select id="style">
                    <option value="journalistic">Journalistic — Narrative-driven, engaging prose with complex arguments</option>
                    <option value="academic">Academic — Rigorous theoretical analysis with scholarly discourse</option>
                    <option value="analytical">Analytical — Systematic logical examination with precise reasoning</option>
                    <option value="experimental">Experimental — Innovative, boundary-pushing intellectual exploration</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="searchQuery">Focus Query (Optional)</label>
                <input type="text" id="searchQuery" placeholder="e.g., power knowledge surveillance foucault">
                <small style="color: #8b949e; font-size: 13px; margin-top: 5px; display: block;">
                    Leave blank for serendipitous source discovery across your entire corpus
                </small>
            </div>
            
            <button type="submit">🚀 Generate High-Quality Essay</button>
            <div style="margin-top: 10px; font-size: 13px; color: #8b949e;">
                ⏱️ Quality generation may take 5-15 minutes depending on complexity
            </div>
        </form>
        
        <div id="status" style="display: none;"></div>
        <div id="output" style="display: none;"></div>
    </div>

    <script>
        let currentEssayId = null;
        
        // Update current model on page load
        fetch('/api/health')
            .then(r => r.json())
            .then(data => {
                document.getElementById('currentModel').textContent = data.model || 'Unknown';
            })
            .catch(() => {});
        
        document.getElementById('essayForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const topic = document.getElementById('topic').value;
            const style = document.getElementById('style').value;
            const searchQuery = document.getElementById('searchQuery').value;
            
            const statusDiv = document.getElementById('status');
            const outputDiv = document.getElementById('output');
            
            statusDiv.style.display = 'block';
            statusDiv.className = 'status loading';
            statusDiv.innerHTML = '🔄 Initiating high-quality essay generation...';
            outputDiv.style.display = 'none';
            
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ topic, style, search_query: searchQuery })
                });
                
                const data = await response.json();
                currentEssayId = data.essay_id;
                
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
                
                if (data.status === 'analyzing_corpus') {
                    statusDiv.innerHTML = '📚 Analyzing corpus and selecting high-quality sources...';
                } else if (data.status === 'crafting_essay') {
                    statusDiv.innerHTML = `🤖 Generating sophisticated essay using ${data.model_used || 'advanced model'}<br>Sources: ${data.sources_found || 0} passages selected for maximum quality`;
                } else if (data.status === 'completed') {
                    statusDiv.className = 'status success';
                    statusDiv.innerHTML = `
                        ✅ High-quality essay completed!
                        <div class="stats">
                            <div class="stat">
                                <div class="stat-value">${data.word_count || 0}</div>
                                <div class="stat-label">Words</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">${data.sources_count || 0}</div>
                                <div class="stat-label">Sources</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">${data.authors_count || 0}</div>
                                <div class="stat-label">Authors</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">${data.model_used || 'N/A'}</div>
                                <div class="stat-label">Model</div>
                            </div>
                        </div>
                    `;
                    
                    outputDiv.style.display = 'block';
                    outputDiv.className = 'essay-output';
                    outputDiv.innerHTML = data.essay;
                    
                    return;
                } else if (data.status === 'error') {
                    statusDiv.className = 'status error';
                    statusDiv.innerHTML = '❌ Error: ' + data.error;
                    return;
                }
                
                setTimeout(pollStatus, 3000);
                
            } catch (error) {
                console.error('Polling error:', error);
                setTimeout(pollStatus, 5000);
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the enhanced web interface"""
    return render_template_string(QUALITY_WEB_INTERFACE.replace('{{ current_model }}', generator.selected_model))

@app.route('/api/generate', methods=['POST'])
def generate_essay():
    """Start high-quality essay generation"""
    try:
        data = request.json
        topic = data.get('topic', '').strip()
        style = data.get('style', 'journalistic')
        search_query = data.get('search_query', '').strip()
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        # Generate unique essay ID
        essay_id = hashlib.md5(f"{topic}{time.time()}".encode()).hexdigest()[:8]
        
        # Initialize queue entry with enhanced metadata
        generator.generation_queue[essay_id] = {
            'topic': topic,
            'style': style,
            'search_query': search_query,
            'status': 'queued',
            'created_at': datetime.now().isoformat(),
            'model_used': generator.selected_model,
            'quality_mode': True
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
            'message': 'High-quality essay generation started',
            'model': generator.selected_model
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

@app.route('/api/health')
def health_check():
    """Enhanced health check with model information"""
    try:
        # Test database connection
        conn = psycopg2.connect(**generator.db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chunks")
        chunk_count = cursor.fetchone()[0]
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"
        chunk_count = 0
    
    try:
        # Test Ollama connection and get model info
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        if response.status_code == 200:
            ollama_status = "connected"
            
            # Get model size info
            model_response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if model_response.status_code == 200:
                models = model_response.json().get('models', [])
                selected_model_info = next((m for m in models if m['name'] == generator.selected_model), None)
            else:
                selected_model_info = None
        else:
            ollama_status = "error"
            selected_model_info = None
    except Exception as e:
        ollama_status = f"error: {e}"
        selected_model_info = None
    
    return jsonify({
        'status': 'healthy' if db_status == 'connected' and ollama_status == 'connected' else 'degraded',
        'database': db_status,
        'ollama': ollama_status,
        'model': generator.selected_model,
        'model_info': selected_model_info,
        'chunk_count': chunk_count,
        'queue_size': len(generator.generation_queue),
        'quality_settings': generator.quality_settings,
        'available_models': generator.model_hierarchy
    })

if __name__ == '__main__':
    print("🚀 LibraryOfBabel High-Quality Essay Generation API")
    print("=" * 60)
    print(f"🌐 Web interface: http://localhost:5571")
    print(f"🔗 API endpoint: http://localhost:5571/api/generate")
    print(f"📊 Health check: http://localhost:5571/api/health")
    print(f"🤖 Selected model: {generator.selected_model}")
    print(f"🧠 RAM optimization: 24GB M4 Mac configuration")
    print(f"⚙️ Quality settings: Extended context, advanced sampling")
    print("📱 Mobile accessible - bookmark for phone access!")
    print("⏱️ Quality mode: 5-15 minute generation time")
    print()
    
    app.run(host='0.0.0.0', port=5571, debug=False)