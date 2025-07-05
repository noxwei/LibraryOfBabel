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
import pickle

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
            'deepseek-r1:8b',   # 8B parameter model - better for creative writing
            'gemma2:9b',        # 9B parameter model - good for essays
            'qwen2.5-coder:14b', # 14B parameter model - analytical writing
            'llama3.1:8b',      # 8B parameter model - fallback
            'llama3.2:latest'   # 3B parameter model - final fallback
        ]
        
        self.selected_model = self.select_best_available_model()
        self.essays_file = "/Users/weixiangzhang/Local Dev/LibraryOfBabel/essays_archive.pkl"
        self.generation_queue = self.load_essays()
        
        # Enhanced processing settings for quality
        self.max_context_length = 32768  # Use full context for larger models
        self.quality_settings = {
            'temperature': 0.7,     # Slightly more focused for essay writing
            'top_p': 0.85,          # More selective token sampling
            'top_k': 30,            # Reduced for higher quality
            'repeat_penalty': 1.1,  # Prevent repetition
            'num_predict': 2000,    # Shorter responses to avoid memory issues
            'num_ctx': 8192,        # Reduced context window
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
    
    def load_essays(self) -> Dict:
        """Load saved essays from file"""
        try:
            if os.path.exists(self.essays_file):
                with open(self.essays_file, 'rb') as f:
                    return pickle.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading essays: {e}")
            return {}
    
    def save_essays(self):
        """Save essays to file"""
        try:
            os.makedirs(os.path.dirname(self.essays_file), exist_ok=True)
            with open(self.essays_file, 'wb') as f:
                pickle.dump(self.generation_queue, f)
        except Exception as e:
            logger.error(f"Error saving essays: {e}")
    
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
        
        # Convert set operations to list operations for safety
        authors_covered = list(set(authors_covered))
        genres_covered = list(set(genres_covered))
        
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
        prompt = f"""You are an academic writer creating an original analytical essay. Using the provided source materials as references and inspiration, write a comprehensive essay on: {topic}

IMPORTANT: This is NOT plagiarism - you are synthesizing information from multiple sources to create original analysis. All sources are properly cited and attributed.

WRITING SPECIFICATIONS:
• Style: {config['tone']}
• Structure: {config['structure']}
• Language: {config['language']}
• Argumentation: {config['argumentation']}

ESSAY REQUIREMENTS:
• Length: 1,500-2,500 words (substantial but manageable for the model)
• Intellectual Depth: Move beyond surface analysis to generate novel theoretical insights
• Cross-Domain Synthesis: Connect insights across the {len(genres_covered)} different genres represented in sources
• Original Framework: Develop a unique theoretical lens or analytical framework
• Contemporary Relevance: Connect historical/theoretical insights to current issues
• Sophisticated Argumentation: Build complex, multi-layered arguments with substantial evidence

SOURCE MATERIAL INTEGRATION:
You have access to {len(passages)} carefully selected sources spanning works by {len(authors_covered)} different authors including {', '.join(authors_covered[:3])}{'...' if len(authors_covered) > 3 else ''}. These sources cover {', '.join(genres_covered)} and provide rich material for synthesis.

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
            unique_authors = list(set(p.get('author', 'Unknown') for p in passages))
            logger.info(f"Using {len(passages)} sources from {len(unique_authors)} authors")
            
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
                'authors_count': len(unique_authors)
            })
            
            # Save essays after successful generation
            self.save_essays()
            
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
ESSAY_MANAGEMENT_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>LibraryOfBabel - Essay Archive</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 20px; background: #0d1117; color: #c9d1d9; line-height: 1.6; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #58a6ff; border-bottom: 2px solid #21262d; padding-bottom: 15px; font-weight: 600; }
        .nav { margin-bottom: 30px; }
        .nav a { color: #58a6ff; text-decoration: none; margin-right: 20px; padding: 10px 15px; border: 1px solid #30363d; border-radius: 6px; display: inline-block; }
        .nav a:hover { background: #21262d; }
        .essay-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; }
        .essay-card { background: #21262d; border-radius: 8px; padding: 20px; border-left: 4px solid #58a6ff; }
        .essay-title { font-size: 18px; font-weight: 600; color: #ffa657; margin-bottom: 10px; }
        .essay-meta { font-size: 14px; color: #8b949e; margin-bottom: 15px; }
        .essay-preview { font-size: 13px; line-height: 1.5; color: #c9d1d9; margin-bottom: 15px; }
        .essay-actions { display: flex; gap: 10px; }
        .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; text-decoration: none; display: inline-block; }
        .btn-primary { background: #238636; color: white; }
        .btn-danger { background: #da3633; color: white; }
        .btn:hover { opacity: 0.9; }
        .empty-state { text-align: center; padding: 60px 20px; color: #8b949e; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; }
        .modal-content { background: #21262d; margin: 5% auto; padding: 30px; width: 90%; max-width: 900px; border-radius: 8px; max-height: 80vh; overflow-y: auto; }
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .modal-title { color: #58a6ff; font-size: 20px; font-weight: 600; }
        .close { background: none; border: none; font-size: 24px; color: #8b949e; cursor: pointer; }
        .essay-content { background: #0d1117; padding: 25px; border-radius: 6px; white-space: pre-wrap; line-height: 1.8; font-family: 'SF Mono', Consolas, monospace; font-size: 14px; }
        .loading { text-align: center; padding: 40px; color: #8b949e; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 LibraryOfBabel Essay Archive</h1>
        
        <div class="nav">
            <a href="/">🏠 Generate New Essay</a>
            <a href="/essays">📖 Essay Archive</a>
            <a href="/api/health">🔍 System Health</a>
            <a href="/api/essays">🔗 API Essays</a>
        </div>
        
        <div id="essayContainer">
            <div class="loading">Loading essays...</div>
        </div>
    </div>

    <!-- Essay Viewer Modal -->
    <div id="essayModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <div class="modal-title" id="modalTitle">Essay Title</div>
                <button class="close" onclick="closeModal()">&times;</button>
            </div>
            <div id="modalContent" class="essay-content">Loading...</div>
        </div>
    </div>

    <script>
        let essays = [];
        
        async function loadEssays() {
            try {
                const response = await fetch('/api/essays');
                const data = await response.json();
                essays = data.essays || [];
                renderEssays();
            } catch (error) {
                document.getElementById('essayContainer').innerHTML = 
                    '<div class="empty-state">❌ Error loading essays: ' + error.message + '</div>';
            }
        }
        
        function renderEssays() {
            const container = document.getElementById('essayContainer');
            
            if (essays.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        📝 No essays generated yet<br>
                        <a href="/" style="color: #58a6ff;">Generate your first essay</a>
                    </div>
                `;
                return;
            }
            
            const grid = essays.map(essay => `
                <div class="essay-card">
                    <div class="essay-title">${essay.topic}</div>
                    <div class="essay-meta">
                        📅 ${new Date(essay.created_at).toLocaleString()}<br>
                        🎨 ${essay.style} • 📊 ${essay.word_count} words • 🤖 ${essay.model_used}
                    </div>
                    <div class="essay-preview">${essay.preview}</div>
                    <div class="essay-actions">
                        <button class="btn btn-primary" onclick="openEssay('${essay.id}')">📖 Read</button>
                        <button class="btn btn-danger" onclick="deleteEssay('${essay.id}')">🗑️ Delete</button>
                    </div>
                </div>
            `).join('');
            
            container.innerHTML = '<div class="essay-grid">' + grid + '</div>';
        }
        
        async function openEssay(essayId) {
            try {
                const response = await fetch('/api/essays/' + essayId);
                const data = await response.json();
                
                document.getElementById('modalTitle').textContent = data.topic;
                document.getElementById('modalContent').textContent = data.essay;
                document.getElementById('essayModal').style.display = 'block';
                
            } catch (error) {
                alert('Error loading essay: ' + error.message);
            }
        }
        
        function closeModal() {
            document.getElementById('essayModal').style.display = 'none';
        }
        
        async function deleteEssay(essayId) {
            if (!confirm('Are you sure you want to delete this essay?')) return;
            
            try {
                const response = await fetch('/api/essays/' + essayId, { method: 'DELETE' });
                if (response.ok) {
                    essays = essays.filter(e => e.id !== essayId);
                    renderEssays();
                } else {
                    alert('Error deleting essay');
                }
            } catch (error) {
                alert('Error deleting essay: ' + error.message);
            }
        }
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('essayModal');
            if (event.target === modal) {
                closeModal();
            }
        }
        
        // Load essays on page load
        loadEssays();
    </script>
</body>
</html>
"""

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
        
        <div class="nav" style="margin-bottom: 30px;">
            <a href="/" style="color: #58a6ff; text-decoration: none; margin-right: 20px; padding: 10px 15px; border: 1px solid #30363d; border-radius: 6px; display: inline-block;">🏠 Generate Essay</a>
            <a href="/essays" style="color: #58a6ff; text-decoration: none; margin-right: 20px; padding: 10px 15px; border: 1px solid #30363d; border-radius: 6px; display: inline-block;">📖 Essay Archive</a>
            <a href="/api/health" style="color: #58a6ff; text-decoration: none; margin-right: 20px; padding: 10px 15px; border: 1px solid #30363d; border-radius: 6px; display: inline-block;">🔍 System Health</a>
            <a href="/api/essays" style="color: #58a6ff; text-decoration: none; margin-right: 20px; padding: 10px 15px; border: 1px solid #30363d; border-radius: 6px; display: inline-block;">🔗 API Essays</a>
        </div>
        
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

@app.route('/api/essays')
def list_essays():
    """List all generated essays"""
    try:
        essays = []
        for essay_id, data in generator.generation_queue.items():
            if data.get('status') == 'completed' and data.get('essay'):
                essays.append({
                    'id': essay_id,
                    'topic': data.get('topic', 'Unknown'),
                    'style': data.get('style', 'Unknown'),
                    'word_count': data.get('word_count', 0),
                    'created_at': data.get('completed_at', data.get('created_at')),
                    'model_used': data.get('model_used', 'Unknown'),
                    'preview': data.get('essay', '')[:200] + '...' if data.get('essay') else ''
                })
        
        # Sort by creation date, newest first
        essays.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return jsonify({'essays': essays})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/essays/<essay_id>')
def get_essay(essay_id):
    """Get full essay content"""
    if essay_id not in generator.generation_queue:
        return jsonify({'error': 'Essay not found'}), 404
    
    data = generator.generation_queue[essay_id]
    if data.get('status') != 'completed':
        return jsonify({'error': 'Essay not completed'}), 400
    
    return jsonify(data)

@app.route('/api/essays/<essay_id>', methods=['DELETE'])
def delete_essay(essay_id):
    """Delete an essay"""
    if essay_id not in generator.generation_queue:
        return jsonify({'error': 'Essay not found'}), 404
    
    del generator.generation_queue[essay_id]
    generator.save_essays()  # Save after deletion
    return jsonify({'message': 'Essay deleted successfully'})

@app.route('/essays')
def essays_page():
    """Essay management page"""
    return render_template_string(ESSAY_MANAGEMENT_PAGE)

@app.route('/api')
def api_docs():
    """API documentation"""
    docs = {
        "LibraryOfBabel Essay Generation API": {
            "version": "1.0",
            "endpoints": {
                "POST /api/generate": {
                    "description": "Generate a new essay",
                    "parameters": {
                        "topic": "Essay topic/title (required)",
                        "style": "Writing style: journalistic, academic, analytical, experimental",
                        "search_query": "Optional search terms for source material"
                    },
                    "returns": "Essay generation ID for status polling"
                },
                "GET /api/status/<essay_id>": {
                    "description": "Check essay generation status",
                    "returns": "Status: queued, analyzing_corpus, crafting_essay, completed, error"
                },
                "GET /api/essays": {
                    "description": "List all completed essays",
                    "returns": "Array of essay metadata with previews"
                },
                "GET /api/essays/<essay_id>": {
                    "description": "Get full essay content",
                    "returns": "Complete essay data including content and metadata"
                },
                "DELETE /api/essays/<essay_id>": {
                    "description": "Delete an essay",
                    "returns": "Success confirmation"
                },
                "GET /api/health": {
                    "description": "System health check",
                    "returns": "Database status, Ollama status, model info, and metrics"
                }
            },
            "example_usage": {
                "curl_generate": "curl -X POST http://localhost:5571/api/generate -H 'Content-Type: application/json' -d '{\"topic\":\"Knowledge systems\",\"style\":\"journalistic\"}'",
                "curl_status": "curl http://localhost:5571/api/status/abc123",
                "curl_list": "curl http://localhost:5571/api/essays",
                "curl_read": "curl http://localhost:5571/api/essays/abc123",
                "curl_delete": "curl -X DELETE http://localhost:5571/api/essays/abc123"
            },
            "current_model": generator.selected_model,
            "total_essays": len([e for e in generator.generation_queue.values() if e.get('status') == 'completed'])
        }
    }
    return jsonify(docs)

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