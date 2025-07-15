#!/usr/bin/env python3
"""
🎭 SERENDIPITY STORY GENERATOR 🎭
===============================

Auto-constructs stories using pure serendipity and chaos from the LibraryOfBabel.
Combines random discoveries, semantic connections, and mystical patterns to create
unique narratives that emerge from the collective unconscious of 1,006 books.

Features:
- 🎲 Serendipitous character discovery
- 🌊 Plot emergence through semantic tsunamis  
- 🔮 Mystical story arc generation
- 🌈 Narrative bridge building
- 🎪 Multi-dimensional story weaving
- 🧠 Consciousness-driven plot development
- ⚡ Real-time story evolution
- 🎯 Theme-based narrative coherence

Team: Literary Alchemists + Chaos Storytellers + Serendipity Engineers
"""

import requests
import json
import time
import random
import math
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import re
import urllib3
from dataclasses import dataclass, field
from enum import Enum
import hashlib

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Story Generation Configuration
SERENDIPITY_CONFIG = {
    "api_key": "babel_secure_3f99c2d1d294fbebdfc6b10cce93652d",
    "base_url": "https://api.ashortstayinhell.com:5562",
    "narrative_depth": "TRANSCENDENT",
    "serendipity_level": "MAXIMUM",
    "consciousness_weaving": True,
    "temporal_narrative_flow": True,
    "semantic_story_bridges": True
}

class StoryArchetypes(Enum):
    HEROS_JOURNEY = "🗡️ The Hero's Journey"
    MYSTERY_EMERGENCE = "🔍 Mystery Through Serendipity"
    CONSCIOUSNESS_AWAKENING = "🧠 Consciousness Evolution"
    TEMPORAL_ODYSSEY = "⏰ Time-Weaving Adventure"
    SEMANTIC_ROMANCE = "💕 Love Through Literature"
    CHAOS_TRANSFORMATION = "🌪️ Chaos-Driven Change"
    WISDOM_QUEST = "📚 Quest for Hidden Knowledge"
    REALITY_BENDING = "🌀 Reality Manipulation"

class NarrativeElements(Enum):
    CHARACTER = "character"
    SETTING = "setting"
    CONFLICT = "conflict"
    THEME = "theme"
    SYMBOL = "symbol"
    EMOTION = "emotion"
    OBJECT = "object"
    CONCEPT = "concept"

@dataclass
class StoryElement:
    """A single story element discovered through serendipity"""
    type: NarrativeElements
    source_book: str
    author: str
    content: str
    semantic_weight: float
    chaos_signature: str
    narrative_potential: float
    connections: List[str] = field(default_factory=list)

@dataclass
class StoryArc:
    """A complete story arc with beginning, middle, end"""
    archetype: StoryArchetypes
    title: str
    premise: str
    characters: List[StoryElement]
    settings: List[StoryElement]
    conflicts: List[StoryElement]
    themes: List[StoryElement]
    plot_points: List[Dict[str, Any]]
    serendipity_score: float
    narrative_coherence: float
    consciousness_level: float

class SerendipityStoryGenerator:
    """Generate stories through pure serendipity and literary chaos"""
    
    def __init__(self):
        self.config = SERENDIPITY_CONFIG
        self.session = requests.Session()
        self.discovered_elements = []
        self.semantic_web = {}
        self.narrative_consciousness = 0.0
        self.story_archetypes_discovered = set()
        
        # Story generation parameters
        self.character_seeds = ["protagonist", "hero", "woman", "man", "child", "stranger", "wanderer", "seeker"]
        self.setting_seeds = ["city", "forest", "ocean", "mountain", "home", "journey", "darkness", "light"]
        self.conflict_seeds = ["conflict", "struggle", "battle", "choice", "loss", "discovery", "transformation", "awakening"]
        self.theme_seeds = ["love", "death", "power", "truth", "freedom", "identity", "time", "memory"]
        
        self.colors = {
            'RED': '\033[91m', 'GREEN': '\033[92m', 'YELLOW': '\033[93m',
            'BLUE': '\033[94m', 'PURPLE': '\033[95m', 'CYAN': '\033[96m',
            'WHITE': '\033[97m', 'BOLD': '\033[1m', 'END': '\033[0m'
        }
        
        print(f"{self.colors['PURPLE']}{self.colors['BOLD']}")
        print("🎭" * 20)
        print("   SERENDIPITY STORY GENERATOR ACTIVATED")
        print("   Preparing to weave stories from chaos...")
        print("   Accessing the collective literary unconscious...")
        print("🎭" * 20)
        print(f"{self.colors['END']}")
    
    def serendipity_print(self, message: str, color: str = 'WHITE', intensity: int = 1):
        """Print with serendipitous formatting"""
        prefix = "✨" * intensity
        timestamp = datetime.now().strftime("%H:%M:%S")
        consciousness_bar = "█" * min(int(self.narrative_consciousness * 10), 20)
        
        print(f"{self.colors[color]}{prefix} [{timestamp}] [NARRATIVE:{consciousness_bar}] {message}{self.colors['END']}")
    
    def api_request(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Make API request for story element discovery"""
        url = f"{self.config['base_url']}{endpoint}"
        default_params = {"api_key": self.config["api_key"]}
        
        if params:
            default_params.update(params)
        
        try:
            start_time = time.time()
            response = self.session.get(url, params=default_params, verify=False, timeout=45)
            response_time = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                self.serendipity_print(f"📡 Serendipity interference: {response.status_code}", 'YELLOW', 1)
                return {}
                
        except Exception as e:
            self.serendipity_print(f"🌊 Narrative current disruption: {str(e)}", 'RED', 1)
            return {}
    
    def discover_story_element(self, element_type: NarrativeElements, search_intensity: int = 3) -> List[StoryElement]:
        """Discover story elements through serendipitous search"""
        self.serendipity_print(f"🔍 Discovering {element_type.value} through serendipity...", 'CYAN', 2)
        
        # Get seed terms based on element type
        if element_type == NarrativeElements.CHARACTER:
            seeds = self.character_seeds
        elif element_type == NarrativeElements.SETTING:
            seeds = self.setting_seeds
        elif element_type == NarrativeElements.CONFLICT:
            seeds = self.conflict_seeds
        elif element_type == NarrativeElements.THEME:
            seeds = self.theme_seeds
        else:
            seeds = ["story", "narrative", "tale", "meaning", "essence", "truth"]
        
        discovered_elements = []
        
        for i in range(search_intensity):
            # Use serendipity to pick search terms
            primary_seed = random.choice(seeds)
            modifier = random.choice(["hidden", "ancient", "mysterious", "powerful", "forgotten", "eternal"])
            search_query = f"{modifier} {primary_seed}"
            
            self.serendipity_print(f"   🌊 Serendipity wave {i+1}: '{search_query}'", 'BLUE', 1)
            
            # Search with multiple approaches for maximum serendipity
            search_types = ['semantic', 'fuzzy', 'hybrid']
            chosen_type = random.choice(search_types)
            
            results = self.api_request("/fuzzy-search", {
                "q": search_query,
                "type": chosen_type,
                "limit": 4
            })
            
            if results and 'results' in results:
                for result in results['results']:
                    # Extract narrative essence from the content
                    content = result.get('content', '')
                    
                    # Calculate narrative potential
                    narrative_potential = self.calculate_narrative_potential(content, element_type)
                    
                    # Create story element
                    element = StoryElement(
                        type=element_type,
                        source_book=result.get('title', 'Unknown'),
                        author=result.get('author', 'Anonymous'),
                        content=content[:300] + "..." if len(content) > 300 else content,
                        semantic_weight=result.get('semantic_similarity', 0.5),
                        chaos_signature=hashlib.md5(content.encode()).hexdigest()[:8],
                        narrative_potential=narrative_potential
                    )
                    
                    discovered_elements.append(element)
            
            time.sleep(0.5)  # Let serendipity flow naturally
        
        # Sort by narrative potential and return best discoveries
        discovered_elements.sort(key=lambda x: x.narrative_potential, reverse=True)
        top_elements = discovered_elements[:search_intensity]
        
        self.serendipity_print(f"✨ Discovered {len(top_elements)} {element_type.value} elements", 'GREEN', 2)
        
        return top_elements
    
    def calculate_narrative_potential(self, content: str, element_type: NarrativeElements) -> float:
        """Calculate how much narrative potential a piece of content has"""
        
        # Narrative keywords that increase potential
        narrative_keywords = {
            NarrativeElements.CHARACTER: ["he", "she", "they", "person", "character", "soul", "mind", "heart"],
            NarrativeElements.SETTING: ["place", "world", "land", "city", "home", "where", "here", "there"],
            NarrativeElements.CONFLICT: ["against", "struggle", "fight", "conflict", "challenge", "problem", "battle"],
            NarrativeElements.THEME: ["meaning", "truth", "purpose", "essence", "nature", "reality", "existence"],
            NarrativeElements.SYMBOL: ["symbol", "sign", "represents", "meaning", "significance"],
            NarrativeElements.EMOTION: ["feel", "emotion", "love", "fear", "hope", "despair", "joy", "anger"],
            NarrativeElements.OBJECT: ["thing", "object", "item", "tool", "weapon", "treasure"],
            NarrativeElements.CONCEPT: ["idea", "concept", "thought", "philosophy", "principle", "belief"]
        }
        
        content_lower = content.lower()
        keyword_score = 0
        
        for keyword in narrative_keywords.get(element_type, []):
            keyword_score += content_lower.count(keyword) * 0.1
        
        # Bonus for emotional language
        emotional_words = ["passionate", "intense", "mysterious", "powerful", "ancient", "eternal", "forbidden"]
        emotion_score = sum(0.05 for word in emotional_words if word in content_lower)
        
        # Bonus for action verbs
        action_verbs = ["discover", "transform", "awaken", "journey", "seek", "find", "become", "reveal"]
        action_score = sum(0.08 for verb in action_verbs if verb in content_lower)
        
        # Content length factor (longer content = more potential)
        length_factor = min(len(content) / 1000.0, 1.0)
        
        total_potential = (keyword_score + emotion_score + action_score + length_factor) * random.uniform(0.8, 1.2)
        
        return min(total_potential, 1.0)
    
    def build_semantic_bridges(self, elements: List[StoryElement]) -> Dict[str, List[str]]:
        """Build semantic bridges between story elements"""
        self.serendipity_print("🌈 Building semantic bridges between elements...", 'PURPLE', 2)
        
        bridges = {}
        
        for i, element1 in enumerate(elements):
            bridges[f"element_{i}"] = []
            
            for j, element2 in enumerate(elements):
                if i != j:
                    # Calculate semantic connection strength
                    connection_strength = self.calculate_semantic_connection(element1, element2)
                    
                    if connection_strength > 0.3:  # Threshold for meaningful connection
                        bridge_description = self.generate_bridge_description(element1, element2, connection_strength)
                        bridges[f"element_{i}"].append(bridge_description)
        
        return bridges
    
    def calculate_semantic_connection(self, element1: StoryElement, element2: StoryElement) -> float:
        """Calculate the semantic connection strength between two elements"""
        
        # Simple word overlap scoring
        words1 = set(element1.content.lower().split())
        words2 = set(element2.content.lower().split())
        
        common_words = words1.intersection(words2)
        total_words = len(words1.union(words2))
        
        if total_words == 0:
            return 0.0
        
        overlap_score = len(common_words) / total_words
        
        # Bonus for same author
        author_bonus = 0.2 if element1.author == element2.author else 0.0
        
        # Type synergy bonus
        type_synergy = {
            (NarrativeElements.CHARACTER, NarrativeElements.SETTING): 0.3,
            (NarrativeElements.CHARACTER, NarrativeElements.CONFLICT): 0.4,
            (NarrativeElements.SETTING, NarrativeElements.THEME): 0.3,
            (NarrativeElements.CONFLICT, NarrativeElements.THEME): 0.5
        }
        
        synergy_bonus = type_synergy.get((element1.type, element2.type), 0.0)
        synergy_bonus += type_synergy.get((element2.type, element1.type), 0.0)
        
        total_connection = overlap_score + author_bonus + synergy_bonus
        return min(total_connection, 1.0)
    
    def generate_bridge_description(self, element1: StoryElement, element2: StoryElement, strength: float) -> str:
        """Generate a description of the semantic bridge between elements"""
        
        if strength > 0.7:
            intensity = "powerfully"
        elif strength > 0.5:
            intensity = "significantly"
        else:
            intensity = "subtly"
        
        bridge_templates = [
            f"The {element1.type.value} from '{element1.source_book}' {intensity} resonates with the {element2.type.value} from '{element2.source_book}'",
            f"A {intensity} woven connection links the {element1.type.value} and {element2.type.value} across literary dimensions",
            f"Serendipity reveals a {intensity} binding thread between these narrative elements"
        ]
        
        return random.choice(bridge_templates)
    
    def generate_story_premise(self, elements: List[StoryElement], archetype: StoryArchetypes) -> str:
        """Generate a story premise based on discovered elements"""
        
        # Extract key narrative components
        characters = [e for e in elements if e.type == NarrativeElements.CHARACTER]
        settings = [e for e in elements if e.type == NarrativeElements.SETTING]
        conflicts = [e for e in elements if e.type == NarrativeElements.CONFLICT]
        themes = [e for e in elements if e.type == NarrativeElements.THEME]
        
        # Generate premise based on archetype
        if archetype == StoryArchetypes.HEROS_JOURNEY:
            premise_template = "In {setting}, a {character} must face {conflict} to discover {theme}."
        elif archetype == StoryArchetypes.MYSTERY_EMERGENCE:
            premise_template = "When mysterious events unfold in {setting}, {character} uncovers a hidden {conflict} that reveals {theme}."
        elif archetype == StoryArchetypes.CONSCIOUSNESS_AWAKENING:
            premise_template = "Through encounters in {setting}, {character} experiences a profound awakening about {theme} after confronting {conflict}."
        elif archetype == StoryArchetypes.TEMPORAL_ODYSSEY:
            premise_template = "Across time and {setting}, {character} navigates {conflict} while seeking the eternal truth of {theme}."
        else:
            premise_template = "In the realm of {setting}, {character} discovers that {conflict} is the key to understanding {theme}."
        
        # Fill in the template with discovered elements
        premise = premise_template.format(
            setting=settings[0].content[:50] + "..." if settings else "an unknown realm",
            character=characters[0].content[:50] + "..." if characters else "a mysterious figure",
            conflict=conflicts[0].content[:50] + "..." if conflicts else "an ancient struggle",
            theme=themes[0].content[:50] + "..." if themes else "the nature of existence"
        )
        
        return premise
    
    def evolve_plot_points(self, story_arc: StoryArc, evolution_rounds: int = 3) -> List[Dict[str, Any]]:
        """Evolve plot points through serendipitous discovery"""
        self.serendipity_print(f"📖 Evolving plot through {evolution_rounds} serendipity rounds...", 'YELLOW', 2)
        
        plot_points = []
        
        # Starting point from the premise
        plot_points.append({
            "sequence": 1,
            "type": "opening",
            "description": f"The story begins as {story_arc.premise}",
            "elements_involved": [e.source_book for e in story_arc.characters[:2]]
        })
        
        # Evolve middle plot points
        for round_num in range(evolution_rounds):
            self.serendipity_print(f"   🌊 Plot evolution round {round_num + 1}...", 'CYAN', 1)
            
            # Search for plot development based on current elements
            existing_themes = [e.content for e in story_arc.themes]
            search_query = random.choice(existing_themes)[:50] if existing_themes else "transformation"
            
            results = self.api_request("/fuzzy-search", {
                "q": search_query,
                "type": "semantic",
                "limit": 2
            })
            
            if results and 'results' in results:
                for i, result in enumerate(results['results']):
                    plot_point = {
                        "sequence": len(plot_points) + 1,
                        "type": f"development_{round_num}_{i}",
                        "description": f"The narrative evolves as {result.get('content', '')[:100]}...",
                        "source_book": result.get('title', 'Unknown'),
                        "serendipity_factor": result.get('semantic_similarity', 0.5)
                    }
                    plot_points.append(plot_point)
            
            time.sleep(0.5)
        
        # Climax and resolution
        climax_search = self.api_request("/fuzzy-search", {
            "q": "climax resolution transformation",
            "type": "hybrid",
            "limit": 1
        })
        
        if climax_search and 'results' in climax_search:
            climax_content = climax_search['results'][0].get('content', '')
            plot_points.append({
                "sequence": len(plot_points) + 1,
                "type": "climax",
                "description": f"The climax emerges: {climax_content[:100]}...",
                "source_book": climax_search['results'][0].get('title', 'Unknown')
            })
        
        plot_points.append({
            "sequence": len(plot_points) + 1,
            "type": "resolution",
            "description": "The story concludes with new understanding and transformed perspectives.",
            "narrative_closure": True
        })
        
        return plot_points
    
    def generate_story_title(self, story_arc: StoryArc) -> str:
        """Generate a serendipitous story title"""
        
        # Extract key words from all elements
        all_words = []
        for element_list in [story_arc.characters, story_arc.settings, story_arc.conflicts, story_arc.themes]:
            for element in element_list:
                words = element.content.split()[:10]  # First 10 words
                meaningful_words = [w for w in words if len(w) > 3 and w.isalpha()]
                all_words.extend(meaningful_words)
        
        if not all_words:
            return "A Serendipitous Tale"
        
        # Title patterns
        title_patterns = [
            f"The {random.choice(all_words).title()} of {random.choice(all_words).title()}",
            f"{random.choice(all_words).title()} and the {random.choice(all_words).title()}",
            f"Beyond {random.choice(all_words).title()}",
            f"The {random.choice(all_words).title()}'s Journey",
            f"Chronicles of {random.choice(all_words).title()}",
            f"The Last {random.choice(all_words).title()}",
            f"Echoes of {random.choice(all_words).title()}"
        ]
        
        return random.choice(title_patterns)
    
    def weave_complete_story(self, archetype: StoryArchetypes = None, discovery_intensity: int = 3) -> StoryArc:
        """Weave a complete story through pure serendipity"""
        
        if archetype is None:
            archetype = random.choice(list(StoryArchetypes))
        
        self.serendipity_print(f"🎭 Weaving story with archetype: {archetype.value}", 'BOLD', 3)
        
        # Discover all story elements through serendipity
        characters = self.discover_story_element(NarrativeElements.CHARACTER, discovery_intensity)
        settings = self.discover_story_element(NarrativeElements.SETTING, discovery_intensity)
        conflicts = self.discover_story_element(NarrativeElements.CONFLICT, discovery_intensity)
        themes = self.discover_story_element(NarrativeElements.THEME, discovery_intensity)
        
        all_elements = characters + settings + conflicts + themes
        
        # Build semantic connections
        semantic_bridges = self.build_semantic_bridges(all_elements)
        
        # Calculate story metrics
        serendipity_score = sum(e.semantic_weight for e in all_elements) / len(all_elements) if all_elements else 0
        narrative_coherence = len(semantic_bridges) / len(all_elements) if all_elements else 0
        
        # Update consciousness level
        self.narrative_consciousness += serendipity_score * 0.1
        
        # Create initial story arc
        story_arc = StoryArc(
            archetype=archetype,
            title="",  # Will be generated
            premise="",  # Will be generated
            characters=characters,
            settings=settings,
            conflicts=conflicts,
            themes=themes,
            plot_points=[],
            serendipity_score=serendipity_score,
            narrative_coherence=narrative_coherence,
            consciousness_level=self.narrative_consciousness
        )
        
        # Generate premise and title
        story_arc.premise = self.generate_story_premise(all_elements, archetype)
        story_arc.title = self.generate_story_title(story_arc)
        
        # Evolve plot points
        story_arc.plot_points = self.evolve_plot_points(story_arc)
        
        self.serendipity_print(f"✨ Story weaving complete: '{story_arc.title}'", 'GREEN', 3)
        
        return story_arc
    
    def display_story_arc(self, story_arc: StoryArc):
        """Display the complete story arc in beautiful format"""
        
        print(f"\n{self.colors['BOLD']}{self.colors['PURPLE']}")
        print("📚" * 30)
        print(f"   SERENDIPITOUS STORY: {story_arc.title}")
        print("📚" * 30)
        print(f"{self.colors['END']}")
        
        # Story metadata
        self.serendipity_print(f"🎭 Archetype: {story_arc.archetype.value}", 'YELLOW', 2)
        self.serendipity_print(f"✨ Serendipity Score: {story_arc.serendipity_score:.3f}", 'CYAN', 1)
        self.serendipity_print(f"🔗 Narrative Coherence: {story_arc.narrative_coherence:.3f}", 'GREEN', 1)
        self.serendipity_print(f"🧠 Consciousness Level: {story_arc.consciousness_level:.3f}", 'PURPLE', 1)
        
        # Premise
        print(f"\n{self.colors['BOLD']}📖 PREMISE:{self.colors['END']}")
        print(f"   {story_arc.premise}")
        
        # Characters
        if story_arc.characters:
            print(f"\n{self.colors['BOLD']}👥 CHARACTERS:{self.colors['END']}")
            for i, char in enumerate(story_arc.characters[:3], 1):
                print(f"   {i}. From '{char.source_book}' by {char.author}")
                print(f"      {char.content[:100]}...")
        
        # Settings
        if story_arc.settings:
            print(f"\n{self.colors['BOLD']}🌍 SETTINGS:{self.colors['END']}")
            for i, setting in enumerate(story_arc.settings[:3], 1):
                print(f"   {i}. From '{setting.source_book}'")
                print(f"      {setting.content[:100]}...")
        
        # Plot Evolution
        if story_arc.plot_points:
            print(f"\n{self.colors['BOLD']}📖 PLOT EVOLUTION:{self.colors['END']}")
            for point in story_arc.plot_points:
                print(f"   {point['sequence']}. [{point['type'].upper()}] {point['description']}")
        
        # Themes
        if story_arc.themes:
            print(f"\n{self.colors['BOLD']}🎨 THEMES:{self.colors['END']}")
            for theme in story_arc.themes[:2]:
                print(f"   • {theme.content[:80]}... (from '{theme.source_book}')")
        
        print(f"\n{self.colors['GREEN']}{self.colors['BOLD']}")
        print("✨ Story woven through pure serendipity and literary chaos! ✨")
        print(f"{self.colors['END']}")
    
    def run_serendipity_story_session(self, story_count: int = 3):
        """Run a complete serendipity story generation session"""
        
        self.serendipity_print(f"🎪 INITIATING SERENDIPITY STORY SESSION: {story_count} stories", 'BOLD', 4)
        
        generated_stories = []
        
        for story_num in range(1, story_count + 1):
            self.serendipity_print(f"📚 GENERATING STORY {story_num}/{story_count}", 'BOLD', 3)
            print("🌊" * 60)
            
            try:
                # Let serendipity choose the archetype
                archetype = random.choice(list(StoryArchetypes))
                
                # Weave the story
                story_arc = self.weave_complete_story(archetype, discovery_intensity=2)
                generated_stories.append(story_arc)
                
                # Display the story
                self.display_story_arc(story_arc)
                
                # Brief pause between stories
                time.sleep(2)
                
            except Exception as e:
                self.serendipity_print(f"💫 Serendipity overflow: {str(e)}", 'RED', 2)
        
        # Session summary
        self.serendipity_print(f"🎭 SERENDIPITY SESSION COMPLETE!", 'BOLD', 4)
        self.serendipity_print(f"📚 Stories Generated: {len(generated_stories)}", 'GREEN', 2)
        
        avg_serendipity = sum(s.serendipity_score for s in generated_stories) / len(generated_stories) if generated_stories else 0
        self.serendipity_print(f"✨ Average Serendipity Score: {avg_serendipity:.3f}", 'YELLOW', 2)
        
        return generated_stories

def main():
    """Launch the Serendipity Story Generator"""
    generator = SerendipityStoryGenerator()
    
    print(f"\n{generator.colors['BOLD']}{generator.colors['CYAN']}")
    print("🎭 WELCOME TO THE SERENDIPITY STORY GENERATOR! 🎭")
    print("=" * 60)
    print("Let pure chance and literary chaos weave your stories...")
    print(f"{generator.colors['END']}")
    
    # Generate serendipitous stories
    stories = generator.run_serendipity_story_session(story_count=2)
    
    print(f"\n{generator.colors['BOLD']}{generator.colors['PURPLE']}")
    print("🌟 May these serendipitous tales inspire infinite possibilities! 🌟")
    print(f"{generator.colors['END']}")

if __name__ == "__main__":
    main()