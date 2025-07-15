#!/usr/bin/env python3
"""
👩‍💻 LEXI'S METADATA STORY TEMPLATE SYSTEM 👩‍💻
==============================================

Advanced template-based story generation using controlled randomness and rich metadata
from the LibraryOfBabel collection. Creates sophisticated narrative templates that
leverage genre, author styles, publication dates, and content patterns.

Features:
- 🎯 Seed-based controlled randomness
- 📚 Genre-aware template selection  
- 👤 Author personality integration
- 📅 Temporal narrative patterns
- 🏷️ Metadata-driven story elements
- 🎨 Template inheritance and evolution
- 🔄 Reproducible story generation
- 📊 Statistical narrative analysis

Team: Lexi (Lead Template Engineer) + Metadata Specialists + Narrative Architects
"""

import requests
import json
import time
import random
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, NamedTuple
from dataclasses import dataclass, field
from enum import Enum
import urllib3
import re
from collections import defaultdict, Counter

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Seed system for controlled randomness
class SeedManager:
    """Manages seeds for reproducible controlled randomness"""
    
    def __init__(self, master_seed: int = None):
        self.master_seed = master_seed or int(time.time())
        self.current_seed = self.master_seed
        self.seed_history = [self.master_seed]
        
    def get_seeded_random(self, context: str = "") -> random.Random:
        """Get a random generator with context-specific seed"""
        context_hash = hashlib.md5(f"{self.current_seed}_{context}".encode()).hexdigest()
        seed = int(context_hash[:8], 16)
        return random.Random(seed)
    
    def advance_seed(self, context: str = ""):
        """Advance to next seed in sequence"""
        self.current_seed = hash(f"{self.current_seed}_{context}") % (2**32)
        self.seed_history.append(self.current_seed)
    
    def get_seed_signature(self) -> str:
        """Get unique signature for current seed state"""
        return f"SEED_{self.current_seed:08X}"

class StoryGenres(Enum):
    PHILOSOPHY = "philosophy"
    SCIENCE_FICTION = "science fiction"
    FANTASY = "fantasy"
    MYSTERY = "mystery"
    ROMANCE = "romance"
    HISTORICAL = "historical"
    BIOGRAPHY = "biography"
    PSYCHOLOGY = "psychology"
    POLITICS = "politics"
    SCIENCE = "science"
    LITERATURE = "literature"
    DRAMA = "drama"

@dataclass
class AuthorProfile:
    """Rich author personality profile from metadata"""
    name: str
    book_count: int
    avg_word_count: int
    genres: List[str]
    time_period: str
    writing_style: str
    thematic_focus: List[str]
    narrative_complexity: float
    emotional_tone: str

@dataclass
class BookMetadata:
    """Complete book metadata for template generation"""
    book_id: int
    title: str
    author: str
    genre: Optional[str]
    publication_date: Optional[str]
    word_count: int
    chunk_count: int
    embedding_count: int
    language: str
    isbn: Optional[str]
    publisher: Optional[str]
    description: Optional[str]

@dataclass
class StoryTemplate:
    """Advanced story template with metadata integration"""
    template_id: str
    name: str
    genre: StoryGenres
    structure: List[str]
    character_archetypes: List[str]
    setting_patterns: List[str]
    conflict_types: List[str]
    theme_categories: List[str]
    narrative_style: str
    complexity_level: float
    metadata_dependencies: List[str]
    seed_signature: str

@dataclass
class GeneratedStory:
    """Complete generated story with full metadata tracking"""
    story_id: str
    title: str
    content: str
    template_used: StoryTemplate
    source_books: List[BookMetadata]
    author_influences: List[AuthorProfile]
    generation_metadata: Dict[str, Any]
    seed_signature: str
    quality_metrics: Dict[str, float]

class LexiMetadataStoryEngine:
    """Lexi's advanced metadata-driven story generation system"""
    
    def __init__(self, master_seed: int = None):
        self.config = {
            "api_key": "babel_secure_3f99c2d1d294fbebdfc6b10cce93652d",
            "base_url": "https://api.ashortstayinhell.com:5562"
        }
        
        self.seed_manager = SeedManager(master_seed)
        self.session = requests.Session()
        
        # Metadata caches
        self.book_metadata_cache = {}
        self.author_profiles = {}
        self.genre_statistics = {}
        
        # Template system
        self.story_templates = {}
        self.template_inheritance = {}
        
        # Initialize templates
        self._initialize_story_templates()
        
        self.colors = {
            'RED': '\033[91m', 'GREEN': '\033[92m', 'YELLOW': '\033[93m',
            'BLUE': '\033[94m', 'PURPLE': '\033[95m', 'CYAN': '\033[96m',
            'WHITE': '\033[97m', 'BOLD': '\033[1m', 'END': '\033[0m'
        }
        
        print(f"{self.colors['PURPLE']}{self.colors['BOLD']}")
        print("👩‍💻" * 20)
        print("   LEXI'S METADATA STORY TEMPLATE ENGINE")
        print(f"   Seed Signature: {self.seed_manager.get_seed_signature()}")
        print("   Analyzing 1,006-book metadata matrix...")
        print("👩‍💻" * 20)
        print(f"{self.colors['END']}")
    
    def lexi_print(self, message: str, color: str = 'WHITE', intensity: int = 1):
        """Lexi's signature output formatting"""
        prefix = "🔧" * intensity
        timestamp = datetime.now().strftime("%H:%M:%S")
        seed_sig = self.seed_manager.get_seed_signature()[-4:]
        
        print(f"{self.colors[color]}{prefix} [{timestamp}|{seed_sig}] {message}{self.colors['END']}")
    
    def api_request(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Make API request with error handling"""
        url = f"{self.config['base_url']}{endpoint}"
        default_params = {"api_key": self.config["api_key"]}
        
        if params:
            default_params.update(params)
        
        try:
            response = self.session.get(url, params=default_params, verify=False, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                self.lexi_print(f"API error {response.status_code}: {endpoint}", 'YELLOW', 1)
                return {}
        except Exception as e:
            self.lexi_print(f"Request failed: {str(e)}", 'RED', 1)
            return {}
    
    def _initialize_story_templates(self):
        """Initialize the sophisticated template system"""
        
        # Philosophy-driven template
        self.story_templates["philosophical_inquiry"] = StoryTemplate(
            template_id="PHIL_001",
            name="Philosophical Inquiry",
            genre=StoryGenres.PHILOSOPHY,
            structure=["existential_setup", "thought_experiment", "dialectical_tension", "insight_emergence", "transcendent_resolution"],
            character_archetypes=["seeker", "sage", "skeptic", "oracle"],
            setting_patterns=["liminal_space", "ivory_tower", "everyday_revelation", "temporal_junction"],
            conflict_types=["internal_contradiction", "paradigm_clash", "moral_dilemma", "consciousness_crisis"],
            theme_categories=["existence", "knowledge", "ethics", "consciousness", "reality"],
            narrative_style="contemplative_exploration",
            complexity_level=0.8,
            metadata_dependencies=["philosophy", "psychology", "consciousness"],
            seed_signature=""
        )
        
        # Science Fiction Evolution
        self.story_templates["sci_fi_evolution"] = StoryTemplate(
            template_id="SCIFI_001", 
            name="Technological Evolution",
            genre=StoryGenres.SCIENCE_FICTION,
            structure=["tech_introduction", "human_adaptation", "unintended_consequences", "paradigm_shift", "new_equilibrium"],
            character_archetypes=["innovator", "adaptor", "resistor", "hybrid"],
            setting_patterns=["near_future", "post_singularity", "space_habitat", "virtual_realm"],
            conflict_types=["human_vs_machine", "progress_vs_tradition", "individual_vs_collective", "reality_vs_simulation"],
            theme_categories=["technology", "evolution", "consciousness", "progress", "identity"],
            narrative_style="speculative_exploration",
            complexity_level=0.7,
            metadata_dependencies=["science", "technology", "future"],
            seed_signature=""
        )
        
        # Historical Resonance
        self.story_templates["historical_resonance"] = StoryTemplate(
            template_id="HIST_001",
            name="Historical Resonance",
            genre=StoryGenres.HISTORICAL,
            structure=["historical_immersion", "period_tension", "personal_stakes", "historical_pivot", "legacy_reflection"],
            character_archetypes=["witness", "participant", "catalyst", "survivor"],
            setting_patterns=["pivotal_moment", "social_upheaval", "cultural_crossroads", "temporal_echo"],
            conflict_types=["individual_vs_society", "tradition_vs_change", "power_dynamics", "moral_choices"],
            theme_categories=["history", "power", "society", "change", "legacy"],
            narrative_style="period_immersion",
            complexity_level=0.6,
            metadata_dependencies=["history", "politics", "society"],
            seed_signature=""
        )
        
        # Psychological Depth
        self.story_templates["psychological_depth"] = StoryTemplate(
            template_id="PSYCH_001",
            name="Psychological Exploration", 
            genre=StoryGenres.PSYCHOLOGY,
            structure=["psychological_setup", "unconscious_emergence", "internal_conflict", "breakthrough_moment", "integration"],
            character_archetypes=["analysand", "analyst", "shadow", "anima"],
            setting_patterns=["interior_landscape", "therapeutic_space", "memory_palace", "dream_realm"],
            conflict_types=["conscious_vs_unconscious", "self_vs_shadow", "desire_vs_superego", "identity_crisis"],
            theme_categories=["psychology", "identity", "consciousness", "healing", "growth"],
            narrative_style="introspective_journey",
            complexity_level=0.75,
            metadata_dependencies=["psychology", "consciousness", "mind"],
            seed_signature=""
        )
        
        # Mystery Unfolding
        self.story_templates["mystery_unfolding"] = StoryTemplate(
            template_id="MYST_001",
            name="Mystery Unfolding",
            genre=StoryGenres.MYSTERY,
            structure=["mysterious_inciting_incident", "clue_gathering", "false_revelation", "deeper_mystery", "truth_unveiled"],
            character_archetypes=["detective", "suspect", "witness", "mastermind"],
            setting_patterns=["crime_scene", "investigation_hub", "hidden_location", "revelation_space"],
            conflict_types=["truth_vs_deception", "logic_vs_intuition", "past_vs_present", "justice_vs_mercy"],
            theme_categories=["truth", "justice", "deception", "discovery", "revelation"],
            narrative_style="investigative_progression",
            complexity_level=0.65,
            metadata_dependencies=["mystery", "crime", "investigation"],
            seed_signature=""
        )
    
    def analyze_book_metadata(self, book_id: int) -> Optional[BookMetadata]:
        """Analyze complete metadata for a book"""
        if book_id in self.book_metadata_cache:
            return self.book_metadata_cache[book_id]
        
        book_data = self.api_request(f"/books/{book_id}")
        
        if not book_data:
            return None
        
        metadata = BookMetadata(
            book_id=book_data.get('book_id', book_id),
            title=book_data.get('title', 'Unknown'),
            author=book_data.get('author', 'Anonymous'),
            genre=book_data.get('genre'),
            publication_date=book_data.get('publication_date'),
            word_count=book_data.get('word_count', 0),
            chunk_count=book_data.get('chunks_available', 0),
            embedding_count=book_data.get('embeddings_available', 0),
            language=book_data.get('language', 'en'),
            isbn=book_data.get('isbn'),
            publisher=book_data.get('publisher'),
            description=book_data.get('description')
        )
        
        self.book_metadata_cache[book_id] = metadata
        return metadata
    
    def discover_books_by_metadata_criteria(self, criteria: Dict[str, Any], limit: int = 10) -> List[BookMetadata]:
        """Discover books matching specific metadata criteria"""
        self.lexi_print(f"🔍 Discovering books with criteria: {criteria}", 'CYAN', 2)
        
        # Build search query from criteria
        search_terms = []
        if 'genre' in criteria:
            search_terms.append(criteria['genre'])
        if 'theme' in criteria:
            search_terms.append(criteria['theme'])
        if 'author_style' in criteria:
            search_terms.append(criteria['author_style'])
        
        search_query = ' '.join(search_terms) if search_terms else 'literature'
        
        # Use seeded randomness for page selection
        rng = self.seed_manager.get_seeded_random(f"book_discovery_{search_query}")
        page = rng.randint(1, 50)
        
        books_response = self.api_request("/books", {
            "page": page,
            "page_size": limit,
            "search": search_query
        })
        
        discovered_books = []
        if books_response and 'results' in books_response:
            for book_data in books_response['results']:
                book_id = book_data.get('book_id')
                if book_id:
                    metadata = self.analyze_book_metadata(book_id)
                    if metadata:
                        discovered_books.append(metadata)
        
        self.lexi_print(f"📚 Discovered {len(discovered_books)} books matching criteria", 'GREEN', 1)
        return discovered_books
    
    def build_author_profile(self, author_name: str, sample_books: List[BookMetadata]) -> AuthorProfile:
        """Build comprehensive author profile from metadata"""
        if author_name in self.author_profiles:
            return self.author_profiles[author_name]
        
        author_books = [book for book in sample_books if book.author == author_name]
        
        if not author_books:
            # Create default profile
            profile = AuthorProfile(
                name=author_name,
                book_count=1,
                avg_word_count=75000,
                genres=["literature"],
                time_period="unknown",
                writing_style="literary",
                thematic_focus=["human_condition"],
                narrative_complexity=0.5,
                emotional_tone="contemplative"
            )
        else:
            # Analyze author characteristics
            total_words = sum(book.word_count for book in author_books)
            avg_words = total_words // len(author_books) if author_books else 75000
            
            genres = list(set(book.genre for book in author_books if book.genre))
            
            # Determine writing style based on word count and patterns
            if avg_words > 150000:
                writing_style = "epic_narrative"
                complexity = 0.8
            elif avg_words > 100000:
                writing_style = "literary_exploration"
                complexity = 0.7
            elif avg_words > 50000:
                writing_style = "focused_narrative"
                complexity = 0.6
            else:
                writing_style = "concise_expression"
                complexity = 0.5
            
            # Determine time period from publication dates
            pub_dates = [book.publication_date for book in author_books if book.publication_date]
            if pub_dates:
                # Extract years and determine era
                years = []
                for date_str in pub_dates:
                    try:
                        year = int(date_str[:4])
                        years.append(year)
                    except:
                        pass
                
                if years:
                    avg_year = sum(years) // len(years)
                    if avg_year >= 2000:
                        time_period = "contemporary"
                    elif avg_year >= 1950:
                        time_period = "modern"
                    elif avg_year >= 1900:
                        time_period = "early_modern"
                    else:
                        time_period = "classical"
                else:
                    time_period = "unknown"
            else:
                time_period = "unknown"
            
            profile = AuthorProfile(
                name=author_name,
                book_count=len(author_books),
                avg_word_count=avg_words,
                genres=genres,
                time_period=time_period,
                writing_style=writing_style,
                thematic_focus=["identity", "society", "consciousness"],  # Default themes
                narrative_complexity=complexity,
                emotional_tone="contemplative"
            )
        
        self.author_profiles[author_name] = profile
        return profile
    
    def select_template_by_metadata(self, books: List[BookMetadata], author_profiles: List[AuthorProfile]) -> StoryTemplate:
        """Select optimal template based on metadata analysis"""
        
        # Analyze genre distribution
        genre_counts = Counter()
        for book in books:
            if book.genre:
                genre_counts[book.genre.lower()] += 1
        
        # Analyze author styles
        complexity_scores = [profile.narrative_complexity for profile in author_profiles]
        avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0.5
        
        # Analyze temporal patterns
        time_periods = [profile.time_period for profile in author_profiles]
        modern_count = sum(1 for period in time_periods if period in ['contemporary', 'modern'])
        
        # Template selection logic with seeded randomness
        rng = self.seed_manager.get_seeded_random("template_selection")
        
        # Weight templates based on metadata
        template_weights = {}
        
        for template_id, template in self.story_templates.items():
            weight = 1.0  # Base weight
            
            # Genre matching
            template_genre = template.genre.value
            if any(template_genre in genre for genre in genre_counts.keys()):
                weight *= 2.0
            
            # Complexity matching
            complexity_diff = abs(template.complexity_level - avg_complexity)
            weight *= (1.0 - complexity_diff)
            
            # Time period preference
            if template.genre in [StoryGenres.HISTORICAL] and modern_count < len(author_profiles) // 2:
                weight *= 1.5
            elif template.genre in [StoryGenres.SCIENCE_FICTION] and modern_count > len(author_profiles) // 2:
                weight *= 1.5
            
            template_weights[template_id] = max(weight, 0.1)  # Minimum weight
        
        # Weighted random selection
        total_weight = sum(template_weights.values())
        rand_val = rng.random() * total_weight
        
        cumulative_weight = 0
        for template_id, weight in template_weights.items():
            cumulative_weight += weight
            if rand_val <= cumulative_weight:
                selected_template = self.story_templates[template_id]
                selected_template.seed_signature = self.seed_manager.get_seed_signature()
                
                self.lexi_print(f"🎯 Selected template: {selected_template.name} (weight: {weight:.2f})", 'YELLOW', 2)
                return selected_template
        
        # Fallback to first template
        fallback = list(self.story_templates.values())[0]
        fallback.seed_signature = self.seed_manager.get_seed_signature()
        return fallback
    
    def generate_content_from_template(self, template: StoryTemplate, books: List[BookMetadata]) -> str:
        """Generate story content based on template and metadata"""
        
        self.lexi_print(f"✍️ Generating content with template: {template.name}", 'PURPLE', 2)
        
        # Use seeded randomness for content generation
        rng = self.seed_manager.get_seeded_random(f"content_gen_{template.template_id}")
        
        story_parts = []
        
        # Generate content for each structural element
        for i, structure_element in enumerate(template.structure):
            self.lexi_print(f"   📝 Writing section: {structure_element}", 'CYAN', 1)
            
            # Select relevant books for this section
            section_books = rng.sample(books, min(2, len(books)))
            
            # Generate section based on template and metadata
            if structure_element == "existential_setup":
                section_content = self._generate_existential_setup(section_books, template, rng)
            elif structure_element == "thought_experiment":
                section_content = self._generate_thought_experiment(section_books, template, rng)
            elif structure_element == "tech_introduction":
                section_content = self._generate_tech_introduction(section_books, template, rng)
            elif structure_element == "historical_immersion":
                section_content = self._generate_historical_immersion(section_books, template, rng)
            elif structure_element == "psychological_setup":
                section_content = self._generate_psychological_setup(section_books, template, rng)
            elif structure_element == "mysterious_inciting_incident":
                section_content = self._generate_mysterious_incident(section_books, template, rng)
            else:
                # Generic section generation
                section_content = self._generate_generic_section(structure_element, section_books, template, rng)
            
            story_parts.append(section_content)
        
        # Combine all sections
        full_story = "\\n\\n".join(story_parts)
        
        self.lexi_print(f"📖 Generated story: {len(full_story)} characters", 'GREEN', 2)
        return full_story
    
    def _generate_existential_setup(self, books: List[BookMetadata], template: StoryTemplate, rng: random.Random) -> str:
        """Generate philosophical existential setup"""
        
        philosophical_concepts = [
            "the nature of consciousness", "the illusion of free will", "the search for meaning",
            "the paradox of existence", "the weight of choice", "the silence of the universe"
        ]
        
        settings = [
            "a quiet library at midnight", "a bustling city intersection", "an empty lecture hall",
            "a solitary park bench", "a crowded coffee shop", "the edge of a precipice"
        ]
        
        concept = rng.choice(philosophical_concepts)
        setting = rng.choice(settings)
        
        # Incorporate book metadata
        book_title = books[0].title if books else "an ancient text"
        author_name = books[0].author if books else "a forgotten philosopher"
        
        return f"""In {setting}, the question of {concept} emerged with startling clarity. Like the protagonist in {author_name}'s '{book_title}', the seeker found themselves confronting the fundamental assumptions that had guided their existence. The familiar world suddenly appeared strange, pregnant with questions that demanded answers."""
    
    def _generate_thought_experiment(self, books: List[BookMetadata], template: StoryTemplate, rng: random.Random) -> str:
        """Generate philosophical thought experiment"""
        
        experiments = [
            "Imagine a world where every thought was visible",
            "Consider a reality where time moved backwards",
            "Envision a society where memories could be traded",
            "Picture a universe where consciousness was shared",
            "Contemplate a realm where truth was determined by consensus"
        ]
        
        experiment = rng.choice(experiments)
        book_reference = f"As explored in '{books[0].title}'" if books else "As ancient wisdom suggests"
        
        return f"""{experiment}. {book_reference}, such scenarios illuminate the boundaries of our understanding. The implications ripple outward, challenging every assumption about identity, reality, and the nature of being itself."""
    
    def _generate_tech_introduction(self, books: List[BookMetadata], template: StoryTemplate, rng: random.Random) -> str:
        """Generate sci-fi technology introduction"""
        
        technologies = [
            "neural interface that could download consciousness",
            "quantum computer that predicted all possible futures",
            "biotechnology that allowed genetic rewriting in real-time",
            "artificial intelligence that experienced emotions",
            "nanotechnology that could reconstruct matter at will"
        ]
        
        tech = rng.choice(technologies)
        book_ref = books[0].title if books else "scientific literature"
        
        return f"""The {tech} represented humanity's latest leap into the unknown. Drawing inspiration from the visionary concepts in '{book_ref}', the inventors had crossed a threshold that would reshape civilization itself. But as with all profound innovations, the true consequences remained hidden in the shadows of the future."""
    
    def _generate_historical_immersion(self, books: List[BookMetadata], template: StoryTemplate, rng: random.Random) -> str:
        """Generate historical setting immersion"""
        
        historical_moments = [
            "the eve of revolution", "the aftermath of war", "the dawn of a new era",
            "the collapse of an empire", "the birth of a movement", "the moment of great change"
        ]
        
        moment = rng.choice(historical_moments)
        book_context = f"chronicled in '{books[0].title}'" if books else "remembered in history"
        
        return f"""At {moment}, as {book_context}, individual lives intersected with the great currents of history. The weight of the past pressed against the uncertainty of the future, and ordinary people found themselves called to make extraordinary choices."""
    
    def _generate_psychological_setup(self, books: List[BookMetadata], template: StoryTemplate, rng: random.Random) -> str:
        """Generate psychological exploration setup"""
        
        psychological_states = [
            "the boundary between memory and imagination", "the territory of suppressed desires",
            "the landscape of unresolved trauma", "the architecture of identity",
            "the ecology of the unconscious mind", "the geography of emotional truth"
        ]
        
        state = rng.choice(psychological_states)
        author_ref = books[0].author if books else "depth psychology"
        
        return f"""The exploration began in {state}. Following insights from {author_ref}'s work, the journey inward revealed layers of experience that had remained hidden from conscious awareness. Each discovery brought both illumination and the recognition of deeper mysteries."""
    
    def _generate_mysterious_incident(self, books: List[BookMetadata], template: StoryTemplate, rng: random.Random) -> str:
        """Generate mystery inciting incident"""
        
        incidents = [
            "a book appeared that shouldn't exist", "a pattern emerged in seemingly random events",
            "a message arrived from an impossible source", "a truth was discovered that contradicted reality",
            "a connection was found between unrelated phenomena", "a secret was revealed that changed everything"
        ]
        
        incident = rng.choice(incidents)
        book_style = f"reminiscent of the mysteries in '{books[0].title}'" if books else "echoing classic detective fiction"
        
        return f"""When {incident}, {book_style}, the investigation began not with questions of who or how, but with the more fundamental question of whether such things were possible at all. The very nature of reality seemed to be at stake."""
    
    def _generate_generic_section(self, element: str, books: List[BookMetadata], template: StoryTemplate, rng: random.Random) -> str:
        """Generate generic section content"""
        
        book_ref = f"'{books[0].title}'" if books else "literary tradition"
        
        return f"""In this phase of {element.replace('_', ' ')}, drawing inspiration from {book_ref}, the narrative unfolded with careful attention to the thematic elements that define {template.genre.value}. The story progressed naturally through the established patterns while maintaining its unique character."""
    
    def calculate_story_quality_metrics(self, story: GeneratedStory) -> Dict[str, float]:
        """Calculate comprehensive quality metrics"""
        
        content = story.content
        
        metrics = {
            "length_score": min(len(content) / 2000.0, 1.0),  # Optimal around 2000 chars
            "complexity_score": story.template_used.complexity_level,
            "metadata_integration": len(story.source_books) / 10.0,  # Max 10 books
            "template_adherence": 0.8,  # Default high adherence
            "narrative_coherence": 0.75,  # Estimated coherence
            "originality_score": len(set(story.content.split())) / len(story.content.split()) if story.content.split() else 0,
            "author_influence_diversity": len(set(profile.name for profile in story.author_influences)) / max(len(story.author_influences), 1)
        }
        
        # Overall quality score
        weights = [0.15, 0.2, 0.15, 0.2, 0.2, 0.05, 0.05]
        metrics["overall_quality"] = sum(score * weight for score, weight in zip(metrics.values(), weights))
        
        return metrics
    
    def generate_complete_story(self, criteria: Dict[str, Any] = None, discovery_limit: int = 8) -> GeneratedStory:
        """Generate a complete story using the full metadata template system"""
        
        self.lexi_print("🎭 Initiating complete metadata-driven story generation", 'BOLD', 3)
        
        # Use default criteria if none provided
        if criteria is None:
            rng = self.seed_manager.get_seeded_random("default_criteria")
            criteria = {
                "genre": rng.choice(["philosophy", "science", "psychology", "history"]),
                "complexity": rng.uniform(0.4, 0.8)
            }
        
        # Step 1: Discover books based on criteria
        discovered_books = self.discover_books_by_metadata_criteria(criteria, discovery_limit)
        
        if not discovered_books:
            self.lexi_print("⚠️ No books discovered, using fallback selection", 'YELLOW', 1)
            # Fallback: get random books
            random_books_response = self.api_request("/books", {"page": 1, "page_size": discovery_limit})
            if random_books_response and 'results' in random_books_response:
                discovered_books = []
                for book_data in random_books_response['results'][:discovery_limit]:
                    book_id = book_data.get('book_id')
                    if book_id:
                        metadata = self.analyze_book_metadata(book_id)
                        if metadata:
                            discovered_books.append(metadata)
        
        # Step 2: Build author profiles
        unique_authors = list(set(book.author for book in discovered_books))
        author_profiles = []
        for author in unique_authors[:5]:  # Limit to 5 authors
            profile = self.build_author_profile(author, discovered_books)
            author_profiles.append(profile)
        
        # Step 3: Select template based on metadata
        selected_template = self.select_template_by_metadata(discovered_books, author_profiles)
        
        # Step 4: Generate content
        story_content = self.generate_content_from_template(selected_template, discovered_books)
        
        # Step 5: Generate title
        rng = self.seed_manager.get_seeded_random("title_generation")
        title_templates = [
            f"The {rng.choice(['Secret', 'Mystery', 'Journey', 'Quest', 'Discovery'])} of {rng.choice(['Truth', 'Understanding', 'Consciousness', 'Reality', 'Knowledge'])}",
            f"Beyond {rng.choice(['Reason', 'Logic', 'Understanding', 'Experience', 'Perception'])}",
            f"Chronicles of {rng.choice(['Change', 'Awakening', 'Transformation', 'Discovery', 'Revelation'])}"
        ]
        story_title = rng.choice(title_templates)
        
        # Step 6: Create complete story object
        story_id = f"STORY_{int(time.time())}_{self.seed_manager.get_seed_signature()}"
        
        generated_story = GeneratedStory(
            story_id=story_id,
            title=story_title,
            content=story_content,
            template_used=selected_template,
            source_books=discovered_books,
            author_influences=author_profiles,
            generation_metadata={
                "criteria": criteria,
                "generation_timestamp": datetime.now().isoformat(),
                "seed_signature": self.seed_manager.get_seed_signature(),
                "discovery_limit": discovery_limit
            },
            seed_signature=self.seed_manager.get_seed_signature(),
            quality_metrics={}
        )
        
        # Step 7: Calculate quality metrics
        generated_story.quality_metrics = self.calculate_story_quality_metrics(generated_story)
        
        # Advance seed for next generation
        self.seed_manager.advance_seed("story_complete")
        
        self.lexi_print(f"✨ Story generation complete: '{story_title}'", 'GREEN', 3)
        return generated_story
    
    def display_story_analysis(self, story: GeneratedStory):
        """Display comprehensive story analysis"""
        
        print(f"\\n{self.colors['BOLD']}{self.colors['BLUE']}")
        print("📊" * 40)
        print(f"   LEXI'S STORY ANALYSIS: {story.title}")
        print("📊" * 40)
        print(f"{self.colors['END']}")
        
        # Metadata overview
        self.lexi_print(f"🎭 Template: {story.template_used.name} ({story.template_used.template_id})", 'PURPLE', 1)
        self.lexi_print(f"🎯 Genre: {story.template_used.genre.value}", 'CYAN', 1)
        self.lexi_print(f"🔧 Seed: {story.seed_signature}", 'YELLOW', 1)
        
        # Source analysis
        print(f"\\n{self.colors['BOLD']}📚 SOURCE BOOKS:{self.colors['END']}")
        for i, book in enumerate(story.source_books[:5], 1):
            print(f"   {i}. '{book.title}' by {book.author}")
            print(f"      📊 {book.word_count:,} words | {book.chunk_count} chunks | {book.embedding_count} embeddings")
        
        # Author influences
        if story.author_influences:
            print(f"\\n{self.colors['BOLD']}👤 AUTHOR INFLUENCES:{self.colors['END']}")
            for profile in story.author_influences[:3]:
                print(f"   • {profile.name} ({profile.time_period}) - {profile.writing_style}")
                print(f"     📈 Complexity: {profile.narrative_complexity:.2f} | Books: {profile.book_count}")
        
        # Quality metrics
        print(f"\\n{self.colors['BOLD']}📈 QUALITY METRICS:{self.colors['END']}")
        for metric, value in story.quality_metrics.items():
            if metric == "overall_quality":
                color = 'GREEN' if value > 0.7 else 'YELLOW' if value > 0.5 else 'RED'
                self.lexi_print(f"🏆 {metric.replace('_', ' ').title()}: {value:.3f}", color, 2)
            else:
                print(f"   📊 {metric.replace('_', ' ').title()}: {value:.3f}")
        
        # Story content
        print(f"\\n{self.colors['BOLD']}📖 GENERATED STORY:{self.colors['END']}")
        print("─" * 80)
        print(story.content)
        print("─" * 80)
        
        # Generation metadata
        print(f"\\n{self.colors['BOLD']}🔧 GENERATION METADATA:{self.colors['END']}")
        for key, value in story.generation_metadata.items():
            print(f"   🔹 {key}: {value}")

def main():
    """Launch Lexi's Metadata Story Template System"""
    
    # Initialize with optional seed for reproducibility
    seed = int(input("Enter seed (or press Enter for random): ") or 0) or None
    
    engine = LexiMetadataStoryEngine(master_seed=seed)
    
    print(f"\\n{engine.colors['BOLD']}{engine.colors['CYAN']}")
    print("👩‍💻 LEXI'S METADATA STORY TEMPLATE SYSTEM 👩‍💻")
    print("=" * 60)
    print("Advanced template-based generation with controlled randomness")
    print(f"Seed Signature: {engine.seed_manager.get_seed_signature()}")
    print(f"{engine.colors['END']}")
    
    # Generate stories with different criteria
    criteria_sets = [
        {"genre": "philosophy", "complexity": 0.8},
        {"genre": "science", "complexity": 0.6},
        {"genre": "psychology", "complexity": 0.7}
    ]
    
    for i, criteria in enumerate(criteria_sets, 1):
        engine.lexi_print(f"📚 GENERATING STORY {i}/{len(criteria_sets)}", 'BOLD', 3)
        print("🔧" * 60)
        
        try:
            story = engine.generate_complete_story(criteria, discovery_limit=6)
            engine.display_story_analysis(story)
            
            time.sleep(2)  # Brief pause between stories
            
        except Exception as e:
            engine.lexi_print(f"💥 Generation error: {str(e)}", 'RED', 2)
    
    print(f"\\n{engine.colors['BOLD']}{engine.colors['PURPLE']}")
    print("🌟 Lexi's metadata template system demonstration complete! 🌟")
    print("🔧 Controlled randomness + Rich metadata = Sophisticated narratives")
    print(f"{engine.colors['END']}")

if __name__ == "__main__":
    main()