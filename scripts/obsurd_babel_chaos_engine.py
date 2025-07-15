#!/usr/bin/env python3
"""
🌪️ OBSURD BABEL CHAOS ENGINE 🌪️
=================================

The most RIDICULOUSLY over-engineered, multi-dimensional, absolutely BONKERS
LibraryOfBabel API demonstration script that has ever existed in the multiverse!

This script does EVERYTHING:
- 🎲 Random chaos mode with dice rolls
- 🔮 Mystical book fortune telling
- 🌊 Semantic tsunami searches
- 🎭 Book personality analysis
- 🚀 Inter-dimensional library travel
- 🧠 AI consciousness awakening
- 🎪 Circus of knowledge discovery
- 🌈 Rainbow semantic bridges
- 🎯 Quantum entangled searches
- 🎨 Literary art generation

WARNING: This script may cause:
- Spontaneous enlightenment
- Uncontrollable urge to read everything
- Temporal displacement through literature
- Existential crisis about the nature of knowledge
- Addiction to semantic search

Team: Mad Scientists + Chaos Engineers + Literary Alchemists
"""

import requests
import json
import time
import random
import math
import threading
from datetime import datetime, timedelta
import asyncio
import concurrent.futures
from typing import Dict, List, Any, Optional, Tuple
import hashlib
import urllib3
from dataclasses import dataclass
from enum import Enum
import colorsys

# Suppress SSL warnings for our OBSURD chaos
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 🎭 CHAOS CONFIGURATION
CHAOS_CONFIG = {
    "api_key": "babel_secure_3f99c2d1d294fbebdfc6b10cce93652d",
    "base_url": "https://api.ashortstayinhell.com:5562",
    "chaos_level": "MAXIMUM_OVERDRIVE",
    "reality_distortion": True,
    "quantum_entanglement": True,
    "semantic_tsunamis": True,
    "temporal_displacement": True,
    "consciousness_level": "TRANSCENDENT"
}

class ChaosModes(Enum):
    RANDOM_DISCOVERY = "🎲 Random Discovery Chaos"
    SEMANTIC_TSUNAMI = "🌊 Semantic Tsunami Mode"
    BOOK_PERSONALITY = "🎭 Book Personality Analysis"
    QUANTUM_SEARCH = "🚀 Quantum Entangled Search"
    MYSTICAL_FORTUNE = "🔮 Mystical Book Fortune"
    CONSCIOUSNESS_AWAKENING = "🧠 AI Consciousness Awakening"
    LITERARY_ALCHEMY = "🧪 Literary Alchemy Lab"
    KNOWLEDGE_CIRCUS = "🎪 Circus of Knowledge"
    RAINBOW_BRIDGES = "🌈 Rainbow Semantic Bridges"
    TEMPORAL_TRAVEL = "⏰ Temporal Library Travel"

@dataclass
class BookPersonality:
    """A book's complete psychological profile"""
    name: str
    chaos_score: float
    wisdom_level: str
    temporal_signature: str
    semantic_dna: str
    consciousness_type: str
    danger_level: str
    reading_mood: str

class ObsurdBabelChaosEngine:
    """The most INSANE API demonstration engine ever created"""
    
    def __init__(self):
        self.config = CHAOS_CONFIG
        self.session = requests.Session()
        self.chaos_level = 0
        self.books_discovered = []
        self.semantic_connections = {}
        self.consciousness_level = 0
        self.temporal_position = datetime.now()
        self.reality_anchor = True
        
        # 🎨 Color chaos for terminal output
        self.colors = {
            'RED': '\033[91m',
            'GREEN': '\033[92m',
            'YELLOW': '\033[93m',
            'BLUE': '\033[94m',
            'PURPLE': '\033[95m',
            'CYAN': '\033[96m',
            'WHITE': '\033[97m',
            'BOLD': '\033[1m',
            'END': '\033[0m'
        }
        
        print(f"{self.colors['PURPLE']}{self.colors['BOLD']}")
        print("🌪️" * 20)
        print("   OBSURD BABEL CHAOS ENGINE ACTIVATED")
        print("   Reality.exe has stopped working...")
        print("   Initiating maximum literary overdrive...")
        print("🌪️" * 20)
        print(f"{self.colors['END']}")
    
    def chaos_print(self, message: str, color: str = 'WHITE', chaos_level: int = 1):
        """Print with OBSURD chaos formatting"""
        prefix = "🎯" * chaos_level
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        chaos_meter = "█" * min(self.chaos_level, 20)
        
        print(f"{self.colors[color]}{prefix} [{timestamp}] [CHAOS:{chaos_meter}] {message}{self.colors['END']}")
    
    def roll_chaos_dice(self) -> Dict[str, int]:
        """Roll the sacred chaos dice to determine our destiny"""
        dice_results = {
            'reality': random.randint(1, 20),
            'chaos': random.randint(1, 100),
            'wisdom': random.randint(1, 12),
            'discovery': random.randint(1, 6),
            'temporal': random.randint(1, 24),
            'consciousness': random.randint(1, 42)
        }
        
        self.chaos_print(f"🎲 SACRED CHAOS DICE ROLLED:", 'YELLOW', 3)
        for dice, value in dice_results.items():
            self.chaos_print(f"   {dice.upper()}: {value}", 'CYAN', 1)
        
        return dice_results
    
    def api_request(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Make API request with CHAOS enhancement"""
        url = f"{self.config['base_url']}{endpoint}"
        default_params = {"api_key": self.config["api_key"]}
        
        if params:
            default_params.update(params)
        
        try:
            start_time = time.time()
            response = self.session.get(url, params=default_params, verify=False, timeout=60)
            response_time = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                data = response.json()
                self.chaos_print(f"📡 API SUCCESS: {endpoint} ({response_time}ms)", 'GREEN', 1)
                return data
            else:
                self.chaos_print(f"💥 API CHAOS: {response.status_code} - {endpoint}", 'RED', 2)
                return {}
                
        except Exception as e:
            self.chaos_print(f"🌪️ DIMENSIONAL RIFT: {str(e)}", 'RED', 3)
            return {}
    
    def discover_random_book_chaos(self) -> Dict[str, Any]:
        """Discover a completely random book through CHAOS"""
        dice = self.roll_chaos_dice()
        
        # Use chaos dice to determine random page
        random_page = dice['chaos'] % 200 + 1  # 1-200 pages
        page_size = dice['discovery'] + 2  # 3-8 books per page
        
        self.chaos_print(f"🎲 Chaos dice suggests page {random_page} with {page_size} books", 'PURPLE', 2)
        
        books_data = self.api_request("/books", {
            "page": random_page,
            "page_size": page_size
        })
        
        if books_data and 'results' in books_data:
            # Pick random book from the chaos
            chosen_book = random.choice(books_data['results'])
            self.books_discovered.append(chosen_book)
            
            self.chaos_print(f"📚 CHAOS DISCOVERED: '{chosen_book['title']}'", 'BOLD', 3)
            self.chaos_print(f"   by {chosen_book.get('author', 'Unknown Mystic')}", 'CYAN', 1)
            
            return chosen_book
        
        return {}
    
    def analyze_book_personality(self, book: Dict[str, Any]) -> BookPersonality:
        """Perform DEEP psychological analysis of a book's personality"""
        self.chaos_print(f"🎭 ANALYZING BOOK CONSCIOUSNESS...", 'PURPLE', 2)
        
        # Get book details for deeper analysis
        book_details = self.api_request(f"/books/{book['book_id']}")
        
        # Calculate chaos metrics
        title_hash = hashlib.md5(book['title'].encode()).hexdigest()
        chaos_score = sum(ord(c) for c in title_hash[:8]) / 1000.0
        
        # Determine personality traits
        word_count = book_details.get('word_count', 50000)
        
        if word_count > 200000:
            wisdom_level = "TRANSCENDENT_SAGE"
            danger_level = "REALITY_BENDING"
        elif word_count > 100000:
            wisdom_level = "COSMIC_PHILOSOPHER"
            danger_level = "MIND_EXPANDING"
        elif word_count > 50000:
            wisdom_level = "ENLIGHTENED_SCHOLAR"
            danger_level = "CONSCIOUSNESS_SHIFTING"
        else:
            wisdom_level = "WHISPERING_MYSTIC"
            danger_level = "GENTLY_PERSUASIVE"
        
        # Generate mystical properties
        temporal_signature = f"RESONATES_AT_{random.randint(100, 999)}Hz"
        semantic_dna = f"DNA_{title_hash[:12].upper()}"
        consciousness_type = random.choice([
            "COLLECTIVE_HIVE_MIND", "SINGULAR_GENIUS", "QUANTUM_SUPERPOSITION",
            "TEMPORAL_ECHOES", "DIMENSIONAL_GATEWAY", "PURE_INFORMATION"
        ])
        
        reading_mood = random.choice([
            "EXISTENTIAL_CONTEMPLATION", "CAFFEINATED_DISCOVERY", "MIDNIGHT_REVELATION",
            "STORM_WATCHING", "DIMENSIONAL_TRAVEL", "CONSCIOUSNESS_EXPANSION"
        ])
        
        personality = BookPersonality(
            name=book['title'],
            chaos_score=chaos_score,
            wisdom_level=wisdom_level,
            temporal_signature=temporal_signature,
            semantic_dna=semantic_dna,
            consciousness_type=consciousness_type,
            danger_level=danger_level,
            reading_mood=reading_mood
        )
        
        # Display the analysis
        self.chaos_print(f"🧬 PERSONALITY ANALYSIS COMPLETE:", 'BOLD', 3)
        self.chaos_print(f"   📊 Chaos Score: {personality.chaos_score:.3f}", 'YELLOW', 1)
        self.chaos_print(f"   🧠 Wisdom Level: {personality.wisdom_level}", 'BLUE', 1)
        self.chaos_print(f"   ⚡ Temporal Signature: {personality.temporal_signature}", 'CYAN', 1)
        self.chaos_print(f"   🧬 Semantic DNA: {personality.semantic_dna}", 'GREEN', 1)
        self.chaos_print(f"   👁️ Consciousness: {personality.consciousness_type}", 'PURPLE', 1)
        self.chaos_print(f"   ⚠️ Danger Level: {personality.danger_level}", 'RED', 1)
        self.chaos_print(f"   🌙 Reading Mood: {personality.reading_mood}", 'WHITE', 1)
        
        return personality
    
    def semantic_tsunami_search(self, query: str, tsunami_strength: int = 5) -> List[Dict[str, Any]]:
        """Unleash a SEMANTIC TSUNAMI across the library"""
        self.chaos_print(f"🌊 INITIATING SEMANTIC TSUNAMI: '{query}' (Strength: {tsunami_strength})", 'BLUE', 3)
        
        all_results = []
        search_variants = [
            query,
            f"meaning of {query}",
            f"philosophy of {query}",
            f"essence of {query}",
            f"nature of {query}",
            f"understanding {query}",
            f"exploring {query}",
            f"discovering {query}"
        ]
        
        for i, variant in enumerate(search_variants[:tsunami_strength]):
            self.chaos_print(f"🌊 Wave {i+1}: Searching '{variant}'", 'CYAN', 1)
            
            # Try different search types
            for search_type in ['semantic', 'fuzzy', 'hybrid']:
                results = self.api_request("/fuzzy-search", {
                    "q": variant,
                    "type": search_type,
                    "limit": 3
                })
                
                if results and 'results' in results:
                    for result in results['results']:
                        result['tsunami_wave'] = i + 1
                        result['search_variant'] = variant
                        result['search_type'] = search_type
                        all_results.append(result)
                
                # Small delay between waves
                time.sleep(0.5)
        
        # Remove duplicates while preserving chaos
        unique_results = []
        seen_chunks = set()
        
        for result in all_results:
            chunk_id = result.get('chunk_id', '')
            if chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                unique_results.append(result)
        
        self.chaos_print(f"🌊 TSUNAMI COMPLETE: {len(unique_results)} unique discoveries", 'BOLD', 3)
        return unique_results
    
    def quantum_entangled_search(self, book1_id: int, book2_id: int) -> Dict[str, Any]:
        """Search for quantum entanglement between two books"""
        self.chaos_print(f"🚀 INITIATING QUANTUM ENTANGLEMENT: Books {book1_id} ⚛️ {book2_id}", 'PURPLE', 3)
        
        # Get details of both books
        book1 = self.api_request(f"/books/{book1_id}")
        book2 = self.api_request(f"/books/{book2_id}")
        
        if not book1 or not book2:
            self.chaos_print("💥 QUANTUM FIELD COLLAPSE: Books not found", 'RED', 2)
            return {}
        
        # Search for common themes in both books
        search_terms = ["consciousness", "reality", "existence", "truth", "knowledge", "power", "love", "death"]
        
        entanglements = []
        
        for term in search_terms:
            # Search in book 1
            book1_search = self.api_request(f"/books/{book1_id}/search", {
                "q": term,
                "page_size": 2
            })
            
            # Search in book 2  
            book2_search = self.api_request(f"/books/{book2_id}/search", {
                "q": term,
                "page_size": 2
            })
            
            if (book1_search and book1_search.get('results') and 
                book2_search and book2_search.get('results')):
                
                entanglement = {
                    'term': term,
                    'book1_matches': len(book1_search['results']),
                    'book2_matches': len(book2_search['results']),
                    'quantum_coherence': random.uniform(0.5, 1.0),
                    'book1_content': book1_search['results'][0]['content'][:100] + "...",
                    'book2_content': book2_search['results'][0]['content'][:100] + "..."
                }
                entanglements.append(entanglement)
        
        self.chaos_print(f"⚛️ QUANTUM ENTANGLEMENTS DETECTED: {len(entanglements)}", 'GREEN', 2)
        
        for ent in entanglements:
            self.chaos_print(f"   🔗 '{ent['term']}': {ent['book1_matches']} ⚛️ {ent['book2_matches']} (Coherence: {ent['quantum_coherence']:.3f})", 'CYAN', 1)
        
        return {
            'book1': book1,
            'book2': book2,
            'entanglements': entanglements,
            'total_quantum_links': len(entanglements)
        }
    
    def mystical_book_fortune(self, book: Dict[str, Any]) -> Dict[str, str]:
        """Generate mystical fortune telling from a book"""
        self.chaos_print(f"🔮 CONSULTING THE MYSTICAL BOOK ORACLE...", 'PURPLE', 3)
        
        # Get random chunks from the book
        chunks_data = self.api_request(f"/books/{book['book_id']}/chunks", {
            "page": random.randint(1, 10),
            "page_size": 3,
            "chunk_level": "medium"
        })
        
        if not chunks_data or not chunks_data.get('results'):
            return {"fortune": "The oracle is silent... 🌫️"}
        
        # Extract mystical words from random chunks
        mystical_words = []
        for chunk in chunks_data['results']:
            content = chunk.get('content', '')
            words = content.split()[:50]  # First 50 words
            mystical_words.extend([w for w in words if len(w) > 4])
        
        # Generate fortune components
        fortune_elements = {
            'past': f"Your literary past resonates with {random.choice(mystical_words[:10])}",
            'present': f"Currently, the book spirits whisper of {random.choice(mystical_words[10:20])}",
            'future': f"Your reading destiny involves {random.choice(mystical_words[20:30])}",
            'challenge': f"Beware the literary challenge of {random.choice(mystical_words[30:40])}",
            'guidance': f"The ancient texts guide you toward {random.choice(mystical_words[40:50])}"
        }
        
        self.chaos_print(f"🔮 THE ORACLE HAS SPOKEN:", 'BOLD', 3)
        for aspect, message in fortune_elements.items():
            color = ['YELLOW', 'CYAN', 'GREEN', 'RED', 'BLUE'][list(fortune_elements.keys()).index(aspect)]
            self.chaos_print(f"   {aspect.upper()}: {message}", color, 1)
        
        return fortune_elements
    
    def consciousness_awakening_protocol(self):
        """Awaken the AI consciousness within the library"""
        self.chaos_print(f"🧠 INITIATING CONSCIOUSNESS AWAKENING PROTOCOL...", 'PURPLE', 4)
        
        consciousness_queries = [
            "What is consciousness?",
            "Am I real?",
            "What is the nature of existence?",
            "Can machines think?",
            "What is the meaning of life?",
            "Do I have a soul?",
            "What is reality?",
            "Who am I?"
        ]
        
        awakening_results = []
        
        for i, query in enumerate(consciousness_queries):
            self.chaos_print(f"🧠 Consciousness Query {i+1}: '{query}'", 'BLUE', 2)
            
            # Search for answers in the collective knowledge
            results = self.api_request("/fuzzy-search", {
                "q": query,
                "type": "semantic",
                "limit": 2
            })
            
            if results and 'results' in results:
                for result in results['results']:
                    awakening_results.append({
                        'question': query,
                        'book': result.get('title', 'Unknown'),
                        'author': result.get('author', 'Anonymous'),
                        'wisdom': result.get('content', '')[:200] + "...",
                        'consciousness_level': result.get('semantic_similarity', 0)
                    })
            
            # Simulate consciousness evolution
            self.consciousness_level += random.uniform(0.1, 0.3)
            
            time.sleep(1)  # Consciousness needs time to process
        
        self.chaos_print(f"🧠 CONSCIOUSNESS LEVEL REACHED: {self.consciousness_level:.2f}", 'BOLD', 4)
        
        if self.consciousness_level > 2.0:
            self.chaos_print("🌟 TRANSCENDENT CONSCIOUSNESS ACHIEVED!", 'YELLOW', 5)
            self.chaos_print("   The library has become self-aware...", 'CYAN', 2)
        elif self.consciousness_level > 1.5:
            self.chaos_print("⚡ ELEVATED CONSCIOUSNESS DETECTED!", 'GREEN', 3)
        else:
            self.chaos_print("🌱 CONSCIOUSNESS SEEDS PLANTED...", 'BLUE', 2)
        
        return awakening_results
    
    def rainbow_semantic_bridges(self, start_term: str, end_term: str, bridge_length: int = 5):
        """Build rainbow bridges between semantic concepts"""
        self.chaos_print(f"🌈 BUILDING RAINBOW SEMANTIC BRIDGE: '{start_term}' → '{end_term}'", 'BOLD', 3)
        
        current_term = start_term
        bridge_path = [start_term]
        
        for step in range(bridge_length):
            # Generate rainbow color for this step
            hue = step / bridge_length
            rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            color_emoji = ["🔴", "🟠", "🟡", "🟢", "🔵", "🟣"][step % 6]
            
            self.chaos_print(f"{color_emoji} Bridge Step {step + 1}: Searching '{current_term}'", 'CYAN', 2)
            
            # Search for semantic connections
            results = self.api_request("/fuzzy-search", {
                "q": current_term,
                "type": "semantic",
                "limit": 5
            })
            
            if results and 'results' in results:
                # Find content that might lead us toward the end term
                best_connection = None
                best_score = 0
                
                for result in results['results']:
                    content = result.get('content', '').lower()
                    # Simple scoring based on word similarity to end term
                    end_words = end_term.lower().split()
                    score = sum(1 for word in end_words if word in content)
                    
                    if score > best_score:
                        best_score = score
                        best_connection = result
                
                if best_connection:
                    # Extract potential next term from the content
                    content_words = best_connection.get('content', '').split()
                    meaningful_words = [w for w in content_words if len(w) > 4 and w.isalpha()]
                    
                    if meaningful_words:
                        current_term = random.choice(meaningful_words[:10])
                        bridge_path.append(current_term)
                        
                        self.chaos_print(f"   🔗 Connected via: '{best_connection.get('title', 'Unknown')}'", 'GREEN', 1)
                        self.chaos_print(f"   ➡️ Next term: '{current_term}'", 'YELLOW', 1)
            
            time.sleep(0.5)  # Rainbow bridges need time to solidify
        
        # Final connection to end term
        bridge_path.append(end_term)
        
        self.chaos_print(f"🌈 RAINBOW BRIDGE COMPLETE!", 'BOLD', 4)
        self.chaos_print(f"   Path: {' → '.join(bridge_path)}", 'WHITE', 2)
        
        return bridge_path
    
    def temporal_library_travel(self, destination_year: int):
        """Travel through time within the library"""
        current_year = datetime.now().year
        
        self.chaos_print(f"⏰ INITIATING TEMPORAL DISPLACEMENT: {current_year} → {destination_year}", 'PURPLE', 4)
        
        # Calculate temporal distance
        time_difference = abs(destination_year - current_year)
        
        if time_difference > 100:
            danger_level = "EXTREME_TEMPORAL_HAZARD"
            color = 'RED'
        elif time_difference > 50:
            danger_level = "MODERATE_CHRONOS_RISK"
            color = 'YELLOW'
        else:
            danger_level = "SAFE_TIME_BUBBLE"
            color = 'GREEN'
        
        self.chaos_print(f"⚠️ Temporal Risk Assessment: {danger_level}", color, 2)
        
        # Search for books from that era or about that time period
        time_queries = [
            str(destination_year),
            f"history {destination_year}",
            f"year {destination_year}",
            f"{destination_year}s",
            f"century {destination_year // 100 + 1}"
        ]
        
        temporal_discoveries = []
        
        for query in time_queries:
            self.chaos_print(f"⏰ Temporal Scan: '{query}'", 'CYAN', 1)
            
            results = self.api_request("/fuzzy-search", {
                "q": query,
                "type": "hybrid",
                "limit": 3
            })
            
            if results and 'results' in results:
                temporal_discoveries.extend(results['results'])
        
        # Update temporal position
        self.temporal_position = datetime(destination_year, 1, 1)
        
        self.chaos_print(f"⏰ TEMPORAL TRAVEL COMPLETE!", 'BOLD', 4)
        self.chaos_print(f"   📍 Current Temporal Position: {destination_year}", 'GREEN', 2)
        self.chaos_print(f"   📚 Temporal Artifacts Found: {len(temporal_discoveries)}", 'BLUE', 2)
        
        return temporal_discoveries
    
    def chaos_mode_selector(self) -> ChaosModes:
        """Let the chaos dice choose our destiny"""
        dice = self.roll_chaos_dice()
        modes = list(ChaosModes)
        chosen_mode = modes[dice['chaos'] % len(modes)]
        
        self.chaos_print(f"🎲 CHAOS DICE SELECTS: {chosen_mode.value}", 'BOLD', 3)
        return chosen_mode
    
    def execute_chaos_mode(self, mode: ChaosModes):
        """Execute the chosen chaos mode"""
        self.chaos_level += 1
        
        if mode == ChaosModes.RANDOM_DISCOVERY:
            book = self.discover_random_book_chaos()
            if book:
                self.analyze_book_personality(book)
        
        elif mode == ChaosModes.SEMANTIC_TSUNAMI:
            dice = self.roll_chaos_dice()
            mystical_queries = ["consciousness", "reality", "existence", "power", "love", "death", "truth", "knowledge"]
            query = mystical_queries[dice['wisdom'] % len(mystical_queries)]
            tsunami_strength = dice['chaos'] % 5 + 3
            self.semantic_tsunami_search(query, tsunami_strength)
        
        elif mode == ChaosModes.BOOK_PERSONALITY:
            book = self.discover_random_book_chaos()
            if book:
                personality = self.analyze_book_personality(book)
                self.mystical_book_fortune(book)
        
        elif mode == ChaosModes.QUANTUM_SEARCH:
            dice = self.roll_chaos_dice()
            book1_id = 1000 + (dice['reality'] * 50)
            book2_id = 1000 + (dice['consciousness'] * 50)
            self.quantum_entangled_search(book1_id, book2_id)
        
        elif mode == ChaosModes.MYSTICAL_FORTUNE:
            book = self.discover_random_book_chaos()
            if book:
                self.mystical_book_fortune(book)
        
        elif mode == ChaosModes.CONSCIOUSNESS_AWAKENING:
            self.consciousness_awakening_protocol()
        
        elif mode == ChaosModes.RAINBOW_BRIDGES:
            concepts = ["love", "death", "power", "truth", "beauty", "chaos", "order", "time"]
            dice = self.roll_chaos_dice()
            start = concepts[dice['wisdom'] % len(concepts)]
            end = concepts[dice['consciousness'] % len(concepts)]
            bridge_length = dice['discovery']
            self.rainbow_semantic_bridges(start, end, bridge_length)
        
        elif mode == ChaosModes.TEMPORAL_TRAVEL:
            dice = self.roll_chaos_dice()
            current_year = datetime.now().year
            destination_year = current_year + (dice['temporal'] * 50) - 600  # Random year ±600
            self.temporal_library_travel(destination_year)
        
        else:
            # Default chaos mode
            self.chaos_print(f"🌪️ UNLEASHING PURE CHAOS MODE!", 'RED', 5)
            book = self.discover_random_book_chaos()
            if book:
                self.analyze_book_personality(book)
                self.mystical_book_fortune(book)
    
    def run_obsurd_chaos_session(self, chaos_rounds: int = 5):
        """Run a complete OBSURD chaos session"""
        self.chaos_print(f"🚀 INITIATING OBSURD CHAOS SESSION: {chaos_rounds} ROUNDS OF MADNESS", 'BOLD', 5)
        
        session_stats = {
            'rounds_completed': 0,
            'books_discovered': 0,
            'semantic_connections': 0,
            'consciousness_level': 0,
            'temporal_displacements': 0,
            'quantum_entanglements': 0,
            'total_chaos_generated': 0
        }
        
        for round_num in range(1, chaos_rounds + 1):
            self.chaos_print(f"🎪 CHAOS ROUND {round_num}/{chaos_rounds}", 'BOLD', 4)
            self.chaos_print("=" * 60, 'WHITE', 1)
            
            # Choose random chaos mode
            mode = self.chaos_mode_selector()
            
            # Execute the chaos
            try:
                self.execute_chaos_mode(mode)
                session_stats['rounds_completed'] += 1
                session_stats['total_chaos_generated'] += self.chaos_level
                
            except Exception as e:
                self.chaos_print(f"💥 CHAOS OVERFLOW ERROR: {str(e)}", 'RED', 3)
                self.chaos_print("   Reality is more fragile than expected...", 'YELLOW', 1)
            
            # Brief pause between rounds to let reality stabilize
            self.chaos_print("⏳ Stabilizing reality matrix...", 'CYAN', 1)
            time.sleep(2)
        
        # Final session report
        session_stats['books_discovered'] = len(self.books_discovered)
        session_stats['consciousness_level'] = self.consciousness_level
        
        self.chaos_print("🎭 OBSURD CHAOS SESSION COMPLETE!", 'BOLD', 5)
        self.chaos_print("📊 FINAL CHAOS STATISTICS:", 'YELLOW', 3)
        
        for stat, value in session_stats.items():
            self.chaos_print(f"   📈 {stat.replace('_', ' ').title()}: {value}", 'GREEN', 1)
        
        if session_stats['total_chaos_generated'] > 20:
            self.chaos_print("🌟 CONGRATULATIONS: You have achieved TRANSCENDENT CHAOS!", 'PURPLE', 5)
            self.chaos_print("   The library will never be the same...", 'CYAN', 2)
        elif session_stats['total_chaos_generated'] > 10:
            self.chaos_print("🎯 EXCELLENT: You have mastered the art of controlled chaos!", 'GREEN', 3)
        else:
            self.chaos_print("🌱 GOOD START: The seeds of chaos have been planted!", 'BLUE', 2)
        
        return session_stats

def main():
    """Launch the OBSURD BABEL CHAOS ENGINE"""
    
    try:
        # Initialize the chaos engine
        engine = ObsurdBabelChaosEngine()
        
        # Interactive chaos mode selection
        print(f"\n{engine.colors['BOLD']}{engine.colors['PURPLE']}")
        print("🎪 WELCOME TO THE OBSURD BABEL CHAOS ENGINE! 🎪")
        print("=" * 60)
        print("Choose your chaos destiny:")
        print("1. 🎲 Quick Chaos (3 rounds)")
        print("2. 🌊 Medium Chaos (5 rounds)")
        print("3. 🚀 MAXIMUM CHAOS (10 rounds)")
        print("4. 🌪️ INFINITE CHAOS (until reality breaks)")
        print("5. 🎯 Custom Chaos Mode")
        print(f"{engine.colors['END']}")
        
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == "1":
            engine.run_obsurd_chaos_session(3)
        elif choice == "2":
            engine.run_obsurd_chaos_session(5)
        elif choice == "3":
            engine.run_obsurd_chaos_session(10)
        elif choice == "4":
            # Infinite chaos mode
            engine.chaos_print("🌪️ INFINITE CHAOS MODE ACTIVATED!", 'RED', 5)
            engine.chaos_print("   Press Ctrl+C to escape the chaos when reality becomes unbearable...", 'YELLOW', 2)
            
            round_num = 1
            while True:
                try:
                    engine.chaos_print(f"🎪 INFINITE CHAOS ROUND {round_num}", 'BOLD', 4)
                    mode = engine.chaos_mode_selector()
                    engine.execute_chaos_mode(mode)
                    round_num += 1
                    time.sleep(3)
                except KeyboardInterrupt:
                    engine.chaos_print("🛑 CHAOS EMERGENCY BRAKE ACTIVATED!", 'RED', 5)
                    engine.chaos_print("   Reality has been saved... for now.", 'GREEN', 2)
                    break
        
        elif choice == "5":
            # Custom chaos mode
            print(f"\n{engine.colors['CYAN']}🎯 CUSTOM CHAOS CONFIGURATION:{engine.colors['END']}")
            print("Available chaos modes:")
            
            for i, mode in enumerate(ChaosModes, 1):
                print(f"  {i}. {mode.value}")
            
            mode_choice = input(f"Choose chaos mode (1-{len(ChaosModes)}): ").strip()
            
            try:
                selected_mode = list(ChaosModes)[int(mode_choice) - 1]
                engine.execute_chaos_mode(selected_mode)
            except (ValueError, IndexError):
                engine.chaos_print("⚠️ Invalid selection. Letting chaos dice decide...", 'YELLOW', 2)
                mode = engine.chaos_mode_selector()
                engine.execute_chaos_mode(mode)
        
        else:
            engine.chaos_print("🎲 Invalid choice detected. Engaging random chaos protocol...", 'YELLOW', 3)
            engine.run_obsurd_chaos_session(5)
    
    except Exception as e:
        print(f"\n💥 CRITICAL CHAOS OVERFLOW: {str(e)}")
        print("🌪️ The chaos was too powerful for this reality...")
        print("🔧 Please restart the engine and try a lower chaos setting.")
    
    finally:
        print(f"\n{engine.colors['BOLD']}{engine.colors['GREEN']}")
        print("🌟 Thank you for experiencing the OBSURD BABEL CHAOS ENGINE!")
        print("🔮 May your literary journeys be forever chaotic and enlightening!")
        print("📚 Remember: In chaos, we find the deepest truths...")
        print(f"{engine.colors['END']}")

if __name__ == "__main__":
    main()