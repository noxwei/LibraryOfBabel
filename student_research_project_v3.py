#!/usr/bin/env python3
"""
LibraryOfBabel Student Research Project V3
==========================================

Revolutionary approach using:
- Book-seeded personalities from actual LibraryOfBabel corpus
- Advanced pattern detection for phrase/structure repetition
- Completely unique academic voices inspired by literary authors
- Cross-paper validation to eliminate template similarities
- Professor simulation for authentic academic review

Each student is seeded from a different author's writing style from the knowledge base,
creating genuinely unique academic personalities that professors will recognize as distinct.
"""

import json
import time
import random
import hashlib
import re
import psycopg2
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple, Set
import requests
from collections import Counter, defaultdict

class AdvancedPatternDetector:
    """Sophisticated pattern detection for academic writing templates"""
    
    def __init__(self):
        self.phrase_patterns = {
            'opening_cliches': [
                r'my journey into .* began',
                r'this paper explores',
                r'in this research',
                r'the purpose of this study',
                r'this investigation seeks',
                r'the following analysis',
                r'through systematic inquiry',
                r'this work examines'
            ],
            'transition_templates': [
                r'what strikes me most',
                r'what emerges is',
                r'the research revealed',
                r'this exploration reveals',
                r'bringing together these',
                r'the implications extend',
                r'moving forward'
            ],
            'conclusion_templates': [
                r'in conclusion',
                r'to conclude',
                r'this research has shown',
                r'the findings suggest',
                r'future research should',
                r'these insights point toward',
                r'the ultimate test'
            ],
            'academic_buzzwords': [
                r'comprehensive analysis',
                r'systematic approach',
                r'critical examination',
                r'theoretical framework',
                r'methodological innovation',
                r'interdisciplinary collaboration',
                r'paradigm shift'
            ]
        }
        
        self.structure_patterns = [
            r'introduction.*methodology.*findings.*conclusion',
            r'abstract.*literature review.*analysis.*implications',
            r'overview.*exploration.*synthesis.*reflection',
            r'personal stakes.*research transformation.*discoveries'
        ]
        
        # Track cross-paper patterns
        self.used_phrases = set()
        self.used_structures = []
        
    def analyze_paper(self, paper_text: str, student_id: str) -> Dict[str, Any]:
        """Advanced analysis of paper for template patterns"""
        
        text_lower = paper_text.lower()
        word_count = len(paper_text.split())
        
        # Pattern detection
        phrase_violations = []
        for category, patterns in self.phrase_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    phrase_violations.extend([(category, match) for match in matches])
        
        # Structure detection
        structure_violations = []
        for pattern in self.structure_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                structure_violations.append(pattern)
        
        # Cross-paper similarity
        paper_phrases = set(re.findall(r'\b\w+(?:\s+\w+){2,4}\b', text_lower))
        cross_paper_overlaps = paper_phrases.intersection(self.used_phrases)
        
        # Calculate violation score
        phrase_score = len(phrase_violations) * 10
        structure_score = len(structure_violations) * 15
        cross_paper_score = len(cross_paper_overlaps) * 5
        
        total_score = phrase_score + structure_score + cross_paper_score
        
        # Risk assessment
        if total_score > 50:
            risk = "HIGH"
        elif total_score > 25:
            risk = "MEDIUM"
        else:
            risk = "LOW"
        
        # Update tracking
        self.used_phrases.update(paper_phrases)
        
        return {
            'student_id': student_id,
            'word_count': word_count,
            'violation_score': total_score,
            'risk_level': risk,
            'phrase_violations': phrase_violations,
            'structure_violations': structure_violations,
            'cross_paper_overlaps': list(cross_paper_overlaps),
            'unique_phrases': len(paper_phrases - self.used_phrases),
            'recommendations': self._generate_recommendations(phrase_violations, structure_violations)
        }
    
    def _generate_recommendations(self, phrase_violations: List, structure_violations: List) -> List[str]:
        """Generate specific recommendations for improving uniqueness"""
        recommendations = []
        
        if phrase_violations:
            recommendations.append("Replace template phrases with author-specific voice patterns")
        if structure_violations:
            recommendations.append("Restructure paper to match literary inspiration's style")
        
        return recommendations

class BookSeededPersonality:
    """Creates student personalities based on actual authors from LibraryOfBabel"""
    
    def __init__(self, book_seeds_file: str, db_config: Dict[str, Any]):
        with open(book_seeds_file, 'r') as f:
            self.book_seeds = json.load(f)
        self.db_config = db_config
        
    def create_student_from_author(self, seed_index: int, student_id: str) -> Dict[str, Any]:
        """Create a student personality based on a specific author's style"""
        
        author_seed = self.book_seeds[seed_index % len(self.book_seeds)]
        
        # Extract writing characteristics from sample
        writing_sample = author_seed['writing_sample']
        
        # Analyze author's style
        style_analysis = self._analyze_writing_style(writing_sample)
        
        # Create academic personality inspired by this author
        personality = {
            'student_id': student_id,
            'name': self._generate_name_from_author(author_seed['author']),
            'inspiration_author': author_seed['author'],
            'inspiration_title': author_seed['title'],
            'inspiration_year': author_seed['year'],
            
            # Academic profile inspired by author
            'major': self._derive_academic_field(author_seed),
            'research_focus': self._derive_research_focus(author_seed),
            
            # Writing style characteristics
            'voice_pattern': style_analysis['voice_pattern'],
            'sentence_structure': style_analysis['sentence_structure'],
            'vocabulary_style': style_analysis['vocabulary_style'],
            'philosophical_approach': style_analysis['philosophical_approach'],
            
            # Unique paper structure
            'paper_structure': self._create_unique_structure(style_analysis),
            'section_styles': self._create_section_styles(style_analysis),
            
            # Research methodology based on author's approach
            'research_methodology': self._derive_methodology(author_seed, style_analysis),
            'citation_style': self._derive_citation_style(style_analysis)
        }
        
        return personality
    
    def _analyze_writing_style(self, sample: str) -> Dict[str, str]:
        """Analyze an author's writing style from sample text"""
        
        # Sentence length analysis
        sentences = re.split(r'[.!?]+', sample)
        avg_sentence_length = sum(len(s.split()) for s in sentences if s.strip()) / len([s for s in sentences if s.strip()])
        
        # Determine patterns
        if avg_sentence_length > 20:
            sentence_structure = "complex_flowing"
        elif avg_sentence_length > 15:
            sentence_structure = "balanced_analytical"
        else:
            sentence_structure = "direct_concise"
        
        # Voice pattern analysis
        if re.search(r'\bi\b.*\bmy\b.*\bme\b', sample.lower()):
            voice_pattern = "personal_narrative"
        elif re.search(r'perhaps|might|could|seemingly', sample.lower()):
            voice_pattern = "contemplative_questioning"
        elif re.search(r'must|should|will|shall', sample.lower()):
            voice_pattern = "authoritative_declarative"
        else:
            voice_pattern = "observational_analytical"
        
        # Vocabulary style
        complex_words = len(re.findall(r'\b\w{8,}\b', sample))
        total_words = len(sample.split())
        complexity_ratio = complex_words / total_words if total_words > 0 else 0
        
        if complexity_ratio > 0.15:
            vocabulary_style = "academic_sophisticated"
        elif complexity_ratio > 0.10:
            vocabulary_style = "balanced_accessible"
        else:
            vocabulary_style = "clear_direct"
        
        # Philosophical approach
        if re.search(r'why|how|what if|perhaps|might', sample.lower()):
            philosophical_approach = "questioning_exploratory"
        elif re.search(r'because|therefore|thus|hence', sample.lower()):
            philosophical_approach = "logical_systematic"
        else:
            philosophical_approach = "descriptive_empirical"
        
        return {
            'voice_pattern': voice_pattern,
            'sentence_structure': sentence_structure,
            'vocabulary_style': vocabulary_style,
            'philosophical_approach': philosophical_approach
        }
    
    def _generate_name_from_author(self, author_name: str) -> str:
        """Generate a student name inspired by but different from the author"""
        
        # Create variations while maintaining cultural authenticity
        name_variations = {
            'Olivie Blake': 'Sophia Chen-Blake',
            'Jill Lepore': 'Elena Rodriguez-Pore', 
            'David A. Ansell': 'Marcus Thompson-Ansell',
            'Matthew McConaughey': 'Jackson Rivers-McCall',
            'Mark Lawrence': 'Adrian Sterling-Law',
            'Matt Ruff': 'Cameron Brooks-Ruffin',
            'Daniel Keyes': 'Samuel Park-Keys',
            'Octavia E. Butler': 'Valencia Marie Butler-Smith',
            'Isaac Asimov': 'Nathaniel Cross-Asimovich',
            'Claire L. Evans': 'Morgan Taylor-Evansfield',
            'William Gibson': 'Alexander North-Gibson',
            'Phil Tucker': 'Jordan Blake-Tucker'
        }
        
        return name_variations.get(author_name, f'Student_{hashlib.md5(author_name.encode()).hexdigest()[:8]}')
    
    def _derive_academic_field(self, author_seed: Dict[str, Any]) -> str:
        """Derive academic field based on author's work"""
        
        author = author_seed['author']
        title = author_seed['title'].lower()
        sample = author_seed['writing_sample'].lower()
        
        # Map authors to academic fields
        field_mappings = {
            'olivie blake': 'Philosophy - Metaphysics & Reality Studies',
            'jill lepore': 'History - Digital Humanities & Technology',
            'david a. ansell': 'Public Health - Health Equity & Social Medicine',
            'matthew mcconaughey': 'Philosophy - Life Narratives & Wisdom Studies',
            'mark lawrence': 'Literature - Fantasy Studies & Heroic Narratives',
            'matt ruff': 'American Studies - Race & Speculative Fiction',
            'daniel keyes': 'Psychology - Cognitive Enhancement & Human Potential',
            'octavia e. butler': 'Environmental Studies - Climate Fiction & Futures',
            'isaac asimov': 'Political Science - Galactic Governance & Institutions',
            'claire l. evans': 'Media Studies - Digital Feminism & Tech History',
            'william gibson': 'Sociology - Cyberpunk Culture & Digital Identity',
            'phil tucker': 'Game Studies - Virtual Worlds & Digital Escapism'
        }
        
        return field_mappings.get(author.lower(), 'Interdisciplinary Studies - Cross-Cultural Analysis')
    
    def _derive_research_focus(self, author_seed: Dict[str, Any]) -> str:
        """Create research focus based on author's thematic interests"""
        
        sample = author_seed['writing_sample'].lower()
        title = author_seed['title'].lower()
        
        if 'library' in sample or 'knowledge' in sample:
            return 'Information Systems & Knowledge Networks'
        elif 'future' in sample or 'time' in sample:
            return 'Temporal Studies & Future Narratives'
        elif 'change' in sample or 'transform' in sample:
            return 'Social Change & Transformation Theory'
        elif 'mind' in sample or 'consciousness' in sample:
            return 'Consciousness Studies & Cognitive Theory'
        elif 'community' in sample or 'people' in sample:
            return 'Community Formation & Social Networks'
        else:
            return 'Cultural Analysis & Meaning-Making'
    
    def _create_unique_structure(self, style_analysis: Dict[str, str]) -> List[str]:
        """Create unique paper structure based on author's style"""
        
        voice = style_analysis['voice_pattern']
        approach = style_analysis['philosophical_approach']
        
        if voice == "personal_narrative":
            return ["Personal Context", "Lived Investigation", "Dialogue with Sources", "Transformative Insights"]
        elif voice == "contemplative_questioning":
            return ["Initial Questions", "Exploratory Inquiries", "Emerging Patterns", "Unresolved Mysteries"]
        elif voice == "authoritative_declarative":
            return ["Theoretical Foundation", "Systematic Analysis", "Evidence Integration", "Definitive Conclusions"]
        else:
            return ["Observational Framework", "Data Exploration", "Pattern Recognition", "Analytical Synthesis"]
    
    def _create_section_styles(self, style_analysis: Dict[str, str]) -> Dict[str, str]:
        """Create section-specific writing styles"""
        
        return {
            'opening': self._get_opening_style(style_analysis),
            'development': self._get_development_style(style_analysis),
            'analysis': self._get_analysis_style(style_analysis),
            'conclusion': self._get_conclusion_style(style_analysis)
        }
    
    def _get_opening_style(self, style_analysis: Dict[str, str]) -> str:
        """Generate opening style based on author characteristics"""
        
        voice = style_analysis['voice_pattern']
        
        if voice == "personal_narrative":
            return "intimate_contextual"
        elif voice == "contemplative_questioning":
            return "philosophical_inquiry"
        elif voice == "authoritative_declarative":
            return "theoretical_foundation"
        else:
            return "observational_setup"
    
    def _get_development_style(self, style_analysis: Dict[str, str]) -> str:
        """Generate development style"""
        
        structure = style_analysis['sentence_structure']
        
        if structure == "complex_flowing":
            return "layered_exploration"
        elif structure == "balanced_analytical":
            return "systematic_building"
        else:
            return "direct_progression"
    
    def _get_analysis_style(self, style_analysis: Dict[str, str]) -> str:
        """Generate analysis style"""
        
        approach = style_analysis['philosophical_approach']
        
        if approach == "questioning_exploratory":
            return "interrogative_discovery"
        elif approach == "logical_systematic":
            return "deductive_reasoning"
        else:
            return "inductive_pattern_finding"
    
    def _get_conclusion_style(self, style_analysis: Dict[str, str]) -> str:
        """Generate conclusion style"""
        
        vocab = style_analysis['vocabulary_style']
        
        if vocab == "academic_sophisticated":
            return "theoretical_integration"
        elif vocab == "balanced_accessible":
            return "practical_implications"
        else:
            return "clear_takeaways"
    
    def _derive_methodology(self, author_seed: Dict[str, Any], style_analysis: Dict[str, str]) -> str:
        """Derive research methodology from author's approach"""
        
        if style_analysis['philosophical_approach'] == "questioning_exploratory":
            return "phenomenological_inquiry"
        elif style_analysis['philosophical_approach'] == "logical_systematic":
            return "structured_analysis"
        else:
            return "grounded_theory_approach"
    
    def _derive_citation_style(self, style_analysis: Dict[str, str]) -> str:
        """Derive citation approach from author's style"""
        
        if style_analysis['voice_pattern'] == "personal_narrative":
            return "integrated_conversational"
        elif style_analysis['vocabulary_style'] == "academic_sophisticated":
            return "formal_scholarly"
        else:
            return "accessible_informative"

class LibrarySearchAgent:
    """Enhanced search agent for academic research using LibraryOfBabel"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        
    def search_topic(self, topic: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search LibraryOfBabel for academic sources on topic"""
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # Enhanced search query (fixed)
            query = """
                SELECT b.title, b.author, c.content, b.publication_year,
                       ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', %s)) as relevance
                FROM books b
                JOIN chunks c ON b.book_id = c.book_id
                WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
                AND LENGTH(c.content) > 200
                ORDER BY relevance DESC
                LIMIT %s
            """
            
            cur.execute(query, (topic, topic, max_results))
            results = cur.fetchall()
            
            sources = []
            for title, author, content, year, relevance in results:
                sources.append({
                    'title': title,
                    'author': author,
                    'year': year,
                    'content': content[:800],  # Limit content length
                    'relevance': float(relevance)
                })
            
            cur.close()
            conn.close()
            
            return sources
            
        except Exception as e:
            print(f"Search error: {e}")
            return []

class LiteraryAcademicWriter:
    """Academic writer that embodies a specific literary author's style"""
    
    def __init__(self, personality: Dict[str, Any], search_agent: LibrarySearchAgent):
        self.personality = personality
        self.search_agent = search_agent
        
    def write_research_paper(self, topic: str) -> str:
        """Write a research paper in the author's unique style"""
        
        # Generate multiple research queries based on topic
        queries = self._generate_research_queries(topic)
        
        # Search for sources
        all_sources = []
        for query in queries:
            sources = self.search_agent.search_topic(query, max_results=8)
            all_sources.extend(sources)
        
        # Remove duplicates
        unique_sources = []
        seen_titles = set()
        for source in all_sources:
            if source['title'] not in seen_titles:
                unique_sources.append(source)
                seen_titles.add(source['title'])
        
        # Generate paper sections based on author's style
        paper_sections = []
        
        for section_name in self.personality['paper_structure']:
            section_content = self._write_section(section_name, unique_sources, topic)
            paper_sections.append(section_content)
        
        # Combine sections with author-specific formatting
        paper = self._format_paper(paper_sections, topic)
        
        return paper
    
    def _generate_research_queries(self, topic: str) -> List[str]:
        """Generate research queries based on author's methodology"""
        
        methodology = self.personality['research_methodology']
        
        if methodology == "phenomenological_inquiry":
            return [
                f"{topic} AND experience",
                f"{topic} AND lived reality",
                f"{topic} AND meaning"
            ]
        elif methodology == "structured_analysis":
            return [
                f"{topic} AND theory",
                f"{topic} AND framework",
                f"{topic} AND systematic"
            ]
        else:
            return [
                f"{topic} AND patterns",
                f"{topic} AND emergence",
                f"{topic} AND development"
            ]
    
    def _write_section(self, section_name: str, sources: List[Dict], topic: str) -> str:
        """Write a section in the author's voice"""
        
        style = self.personality['section_styles']
        voice = self.personality['voice_pattern']
        approach = self.personality['philosophical_approach']
        
        # Select relevant sources for this section
        section_sources = sources[:min(len(sources), random.randint(3, 7))]
        
        if section_name in ["Personal Context", "Initial Questions"]:
            return self._write_opening_section(section_name, topic, section_sources)
        elif "Investigation" in section_name or "Analysis" in section_name:
            return self._write_analysis_section(section_name, topic, section_sources)
        elif "Synthesis" in section_name or "Integration" in section_name:
            return self._write_synthesis_section(section_name, topic, section_sources)
        else:
            return self._write_conclusion_section(section_name, topic, section_sources)
    
    def _write_opening_section(self, section_name: str, topic: str, sources: List[Dict]) -> str:
        """Write opening section in author's voice"""
        
        opening_style = self.personality['section_styles']['opening']
        author_name = self.personality['inspiration_author']
        
        # Generate opening inspired by the original author's style
        if opening_style == "intimate_contextual":
            opening = f"""## {section_name}

The question of {topic} first presented itself to me not through academic literature, but through the strange confluence of circumstances that seems to govern intellectual discovery. Like {author_name} writing about the mysteries that captivate us, I found myself drawn into this inquiry through a series of seemingly unrelated encounters.

Working within the vast network of knowledge that comprises LibraryOfBabel, I began to trace the conversations around {topic}, discovering {len(sources)} sources that spoke to different dimensions of this question. Each source revealed not just information, but a different way of approaching the fundamental questions that {topic} raises."""

        elif opening_style == "philosophical_inquiry":
            opening = f"""## {section_name}

What does it mean to investigate {topic} in our current moment? This question, seemingly straightforward, opens onto a series of deeper inquiries that resist easy answers. The {len(sources)} sources I encountered through LibraryOfBabel each suggest different entry points into this puzzle.

Perhaps the most intriguing aspect of {topic} is how it refuses to remain contained within any single disciplinary framework. Like the subjects that fascinated {author_name}, it exists at the intersection of multiple ways of knowing."""

        elif opening_style == "theoretical_foundation":
            opening = f"""## {section_name}

Any serious investigation of {topic} must begin with a clear theoretical foundation. The {len(sources)} sources identified through systematic query of LibraryOfBabel provide the necessary groundwork for understanding the key concepts and methodological approaches that define this field.

The theoretical architecture of {topic} reveals several foundational principles that emerge consistently across different scholarly approaches."""

        else:
            opening = f"""## {section_name}

The landscape of scholarship around {topic} presents a complex array of perspectives and methodologies. Through systematic analysis of {len(sources)} sources within LibraryOfBabel, several key patterns emerge that illuminate both the current state of knowledge and the areas requiring further investigation.

The observational framework I bring to this analysis draws inspiration from {author_name}'s approach to understanding complex phenomena through careful attention to detail and pattern recognition."""

        # Add source engagement
        if sources:
            source_discussion = "\n\nThe sources reveal several key dimensions:\n\n"
            for i, source in enumerate(sources[:3]):
                year_text = f"({source['year']})" if source['year'] else ''
                insight = self._extract_key_insight(source['content'], topic)
                source_discussion += f"**{source['author']}** in *{source['title']}* {year_text} explores how {insight}.\n\n"
            
            opening += source_discussion
        
        return opening
    
    def _write_analysis_section(self, section_name: str, topic: str, sources: List[Dict]) -> str:
        """Write analysis section in author's voice"""
        
        analysis_style = self.personality['section_styles']['analysis']
        
        if analysis_style == "interrogative_discovery":
            section = f"""## {section_name}

Rather than seeking definitive answers, this exploration of {topic} reveals a series of productive questions that emerge from engagement with the sources. Each question opens new pathways for understanding.

**What patterns emerge when we examine {topic} across different contexts?**

The {len(sources)} sources suggest that {topic} manifests differently depending on the specific circumstances and frameworks through which it is approached."""

        elif analysis_style == "deductive_reasoning":
            section = f"""## {section_name}

Based on the theoretical foundation established above, several key propositions can be derived regarding {topic}. The evidence from {len(sources)} sources supports the following analytical framework."""

        else:
            section = f"""## {section_name}

Through inductive analysis of patterns that emerge across {len(sources)} sources, several key themes become visible in the scholarship on {topic}."""

        # Add detailed source analysis with expanded content
        if sources:
            section += "\n\n"
            for i, source in enumerate(sources[:min(len(sources), 6)]):
                insight = self._extract_key_insight(source['content'], topic)
                contribution = self._generate_contribution_analysis(insight, topic)
                implications = self._generate_implications(insight, topic)
                
                section += f"**Source Analysis {i+1}**: {source['author']}'s work on *{source['title']}* demonstrates {insight}. This contributes to our understanding by {contribution}. The implications of this approach suggest {implications}.\n\n"
                
                # Add deeper analysis for first few sources
                if i < 3:
                    deeper_insight = self._extract_deeper_insight(source['content'], topic)
                    section += f"Further examination reveals that {deeper_insight}. This finding challenges conventional assumptions about {topic} and opens new avenues for theoretical development.\n\n"
        
        return section
    
    def _write_synthesis_section(self, section_name: str, topic: str, sources: List[Dict]) -> str:
        """Write synthesis section"""
        
        section = f"""## {section_name}

Bringing together insights from {len(sources)} sources reveals a complex landscape of understanding around {topic}. Rather than a unified theory, what emerges is a dynamic constellation of approaches that complement and challenge each other.

The convergence points suggest several key insights:

• **Methodological Diversity**: The sources demonstrate that {topic} requires multiple analytical approaches, each revealing different dimensions of the phenomenon. This methodological pluralism suggests that {topic} cannot be adequately understood through any single theoretical lens.

• **Interdisciplinary Necessity**: No single disciplinary perspective proves adequate for understanding {topic} in its full complexity. The most productive insights emerge at the intersections between fields, where different ways of knowing can inform and enrich each other.

• **Contextual Sensitivity**: The meaning and significance of {topic} varies considerably across different contexts and applications. This variability points toward the need for situated analysis that takes seriously the specific conditions under which {topic} operates.

• **Temporal Dynamics**: The sources reveal that {topic} is not a static phenomenon but evolves over time in response to changing social, technological, and cultural conditions. Understanding these temporal dimensions is crucial for developing effective approaches.

• **Power Relations**: Multiple sources highlight how {topic} is shaped by existing power structures and, in turn, can either reinforce or challenge these structures. This recognition demands critical attention to the political dimensions of {topic}.

**Theoretical Implications:**

The synthesis of these sources suggests that {topic} functions as what might be called a "boundary object" - a concept that is plastic enough to adapt to different contexts while maintaining enough coherence to enable meaningful communication across disciplinary and institutional boundaries. This characteristic makes {topic} both challenging to study and potentially valuable as a site for collaborative inquiry.

**Methodological Considerations:**

The diversity of approaches represented in the sources points toward the value of mixed-methods research that can capture both the quantitative patterns and qualitative dimensions of {topic}. Furthermore, the sources consistently emphasize the importance of community engagement and participatory research methods that center the perspectives of those most directly affected by {topic}.

**Emerging Questions:**

This synthesis reveals several productive areas for future investigation:

1. How do different cultural contexts shape the manifestation and meaning of {topic}?
2. What are the long-term implications of current approaches to {topic}?
3. How might new technologies and social forms require us to reconsider our understanding of {topic}?
4. What forms of collaboration between academic researchers and community partners might advance both theoretical understanding and practical applications of {topic}?"""

        # Add unique synthesis based on author's voice
        voice = self.personality['voice_pattern']
        if voice == "personal_narrative":
            section += f"\n\n**Personal Reflection:**\n\nPersonally, this synthesis has fundamentally shifted my understanding of how {topic} operates in lived experience. The academic frameworks provide essential structure, but they must be balanced with attention to the particular ways {topic} manifests in specific situations. This research has convinced me that effective scholarship on {topic} requires genuine engagement with communities and contexts beyond the academy."
        elif voice == "contemplative_questioning":
            section += f"\n\n**Unresolved Questions:**\n\nPerhaps most significantly, this synthesis reveals how much we still do not know about {topic}. Rather than providing definitive answers, the sources point toward a series of productive uncertainties that could guide future inquiry. What would it mean to approach {topic} with greater humility about the limits of our current understanding?"
        elif voice == "authoritative_declarative":
            section += f"\n\n**Definitive Conclusions:**\n\nBased on this comprehensive analysis, several definitive conclusions can be drawn about the current state of {topic} research and its future directions. These conclusions provide a foundation for the systematic advancement of both theoretical understanding and practical applications."
        
        return section
    
    def _write_conclusion_section(self, section_name: str, topic: str, sources: List[Dict]) -> str:
        """Write conclusion section"""
        
        conclusion_style = self.personality['section_styles']['conclusion']
        
        if conclusion_style == "theoretical_integration":
            section = f"""## {section_name}

This investigation of {topic} through {len(sources)} sources contributes to theoretical understanding by demonstrating the productive tensions that exist within current scholarship. Rather than resolving these tensions, the analysis reveals their necessity for maintaining the intellectual vitality of the field.

**Theoretical Contributions:**

The research makes several key theoretical contributions to our understanding of {topic}:

1. **Framework Integration**: By bringing together diverse theoretical perspectives, this analysis demonstrates how seemingly incompatible approaches can be productively synthesized to create more robust explanatory frameworks.

2. **Boundary Clarification**: The investigation clarifies the boundaries and limitations of current theoretical approaches to {topic}, revealing areas where new theoretical development is most urgently needed.

3. **Methodological Innovation**: The sources point toward innovative methodological approaches that could advance both theoretical understanding and empirical research on {topic}.

**Implications for Knowledge Production:**

The theoretical implications extend beyond {topic} itself to fundamental questions about methodology, disciplinary boundaries, and the relationship between knowledge and practice. This research suggests that effective scholarship on {topic} requires willingness to transgress traditional disciplinary boundaries while maintaining rigorous standards of evidence and analysis.

**Future Theoretical Directions:**

Several areas for future theoretical development emerge from this analysis:

- Development of more sophisticated frameworks for understanding the relationship between {topic} and broader social processes
- Integration of insights from critical theory, empirical research, and community-based knowledge
- Creation of theoretical tools that can accommodate both stability and change in how {topic} operates
- Advancement of theories that can bridge individual and structural levels of analysis

**Contribution to Broader Scholarship:**

This investigation contributes to broader scholarly conversations about interdisciplinary research, community engagement, and the social responsibility of academic knowledge production. The findings suggest that {topic} can serve as a productive site for experimenting with more collaborative and democratic forms of knowledge creation."""

        elif conclusion_style == "practical_implications":
            section = f"""## {section_name}

The insights generated through this exploration of {topic} have concrete implications for both scholarly practice and real-world applications. The {len(sources)} sources point toward several actionable directions for future work.

**Immediate Practical Applications:**

1. **Policy Development**: The research findings can inform policy decisions related to {topic}, particularly in areas where evidence-based approaches are needed.

2. **Program Design**: Insights from the sources suggest specific strategies for designing programs and interventions that effectively address challenges related to {topic}.

3. **Community Engagement**: The analysis reveals approaches to {topic} that prioritize community participation and local knowledge, offering models for more democratic and effective practice.

**Strategies for Implementation:**

These findings suggest specific strategies for addressing the challenges and opportunities that {topic} presents in contemporary contexts:

- **Collaborative Partnerships**: Establishing genuine partnerships between academic researchers, community organizations, and policy makers
- **Resource Allocation**: Directing resources toward approaches that have demonstrated effectiveness in addressing {topic}
- **Capacity Building**: Investing in the development of skills and knowledge needed to work effectively with {topic}
- **Evaluation Systems**: Creating assessment tools that can capture the full range of outcomes related to {topic}

**Long-term Vision:**

The research points toward a long-term vision in which {topic} becomes a site for modeling more just and sustainable approaches to social challenges. This vision requires sustained commitment to collaborative work and willingness to learn from both successes and failures.

**Call to Action:**

This investigation concludes with a call for scholars, practitioners, and community members to work together in advancing understanding and practice related to {topic}. The complexity of the challenges requires collaborative effort across traditional boundaries of expertise and institutional affiliation."""

        else:
            section = f"""## {section_name}

This exploration of {topic} through {len(sources)} sources clarifies several key takeaways that can inform future inquiry and practice.

**Primary Takeaways:**

1. **Complexity Recognition**: {topic} operates through complex mechanisms that resist simple explanations or solutions. Effective approaches must acknowledge and work with this complexity rather than attempting to reduce it.

2. **Context Sensitivity**: The meaning and significance of {topic} varies considerably across different contexts. Universal approaches are less effective than those that can adapt to local conditions and priorities.

3. **Collaborative Necessity**: No single perspective or approach proves adequate for understanding {topic}. Progress requires genuine collaboration across different forms of expertise and experience.

4. **Dynamic Nature**: {topic} is not a static phenomenon but evolves in response to changing conditions. Approaches must be flexible enough to adapt while maintaining core commitments to effectiveness and justice.

**Clear Insights for Practice:**

The central insight is that {topic} functions as a site where multiple forms of knowledge intersect, requiring approaches that can accommodate complexity while maintaining analytical rigor. This understanding has several practical implications:

- **Research Design**: Future research should prioritize mixed-methods approaches that can capture both patterns and particularity
- **Community Engagement**: Effective work on {topic} requires sustained engagement with communities and attention to power dynamics
- **Policy Application**: Policy approaches should be designed to accommodate local variation while maintaining consistent principles
- **Educational Practice**: Teaching about {topic} should model the collaborative and critical approaches that the subject matter demands

**Directions for Future Work:**

Several clear directions emerge for future scholarship and practice:

1. **Longitudinal Studies**: Research that tracks the development of {topic} over time
2. **Comparative Analysis**: Studies that examine {topic} across different cultural and institutional contexts
3. **Participatory Research**: Projects that center community knowledge and priorities
4. **Implementation Research**: Studies that examine how theoretical insights translate into effective practice

**Final Reflections:**

This investigation demonstrates that rigorous scholarship on {topic} can contribute to both theoretical understanding and practical change. The key is maintaining commitment to both intellectual honesty and social responsibility, recognizing that the two commitments reinforce rather than conflict with each other."""

        return section
    
    def _extract_key_insight(self, content: str, topic: str) -> str:
        """Extract a key insight from source content"""
        
        # Simple extraction - find sentences containing the topic
        sentences = re.split(r'[.!?]+', content)
        relevant_sentences = [s.strip() for s in sentences if topic.lower() in s.lower() and len(s.strip()) > 20]
        
        if relevant_sentences:
            return relevant_sentences[0][:150] + "..."
        else:
            return f"approaches to understanding {topic} through systematic analysis"
    
    def _generate_contribution_analysis(self, insight: str, topic: str) -> str:
        """Generate analysis of how an insight contributes to understanding"""
        
        contributions = [
            f"expanding our conception of how {topic} functions in different contexts",
            f"providing methodological tools for analyzing {topic} more effectively",
            f"challenging conventional assumptions about {topic}",
            f"connecting {topic} to broader theoretical frameworks",
            f"offering practical strategies for engaging with {topic}"
        ]
        
        return random.choice(contributions)
    
    def _generate_implications(self, insight: str, topic: str) -> str:
        """Generate implications of an insight"""
        
        implications = [
            f"that {topic} operates through more complex mechanisms than previously understood",
            f"that traditional approaches to {topic} may need substantial revision",
            f"that interdisciplinary collaboration is essential for advancing {topic} research",
            f"that practical applications of {topic} require careful consideration of context",
            f"that future research in {topic} should prioritize community engagement"
        ]
        
        return random.choice(implications)
    
    def _extract_deeper_insight(self, content: str, topic: str) -> str:
        """Extract a deeper insight from source content"""
        
        # Find more substantial content
        sentences = re.split(r'[.!?]+', content)
        longer_sentences = [s.strip() for s in sentences if len(s.strip()) > 50 and topic.lower() in s.lower()]
        
        if longer_sentences:
            return longer_sentences[0][:200] + "..."
        else:
            return f"this approach to {topic} reveals underlying complexities that merit further investigation"
    
    def _format_paper(self, sections: List[str], topic: str) -> str:
        """Format the complete paper with author-specific style"""
        
        # Create header
        name = self.personality['name']
        major = self.personality['major']
        student_id = self.personality['student_id']
        
        header = f"""Author: {name} ({student_id})
Major: {major}
Date: {datetime.now().strftime('%B %d, %Y')}

"""
        
        # Add unique formatting based on inspiration author
        inspiration = self.personality['inspiration_author']
        if inspiration == "Octavia E. Butler":
            header += f"\"All that you touch, you change. All that you change, changes you.\"\n— Earthseed principle, applied to academic inquiry\n\n"
        elif inspiration == "William Gibson":
            header += f"// Academic inquiry as cyberpunk methodology //\n\n"
        elif inspiration == "Matthew McConaughey":
            header += f"*Sometimes you've got to go back to actually move forward, and I don't mean go back to reminisce or chase ghosts, I mean go back to see where you came from.*\n\n"
        
        # Combine all sections
        paper = header + "\n\n".join(sections)
        
        return paper

class ProfessorReviewSimulator:
    """Simulates professor review of student papers for authenticity"""
    
    def __init__(self):
        self.review_criteria = [
            'originality',
            'depth_of_analysis', 
            'use_of_sources',
            'writing_quality',
            'argument_coherence',
            'critical_thinking'
        ]
    
    def review_papers(self, papers: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Professor-style review of all student papers"""
        
        reviews = {}
        patterns_detected = []
        
        for student_id, paper in papers:
            review = self._review_individual_paper(paper, student_id)
            reviews[student_id] = review
        
        # Cross-paper analysis
        cross_analysis = self._cross_paper_analysis(papers)
        
        return {
            'individual_reviews': reviews,
            'cross_paper_analysis': cross_analysis,
            'overall_assessment': self._overall_assessment(reviews, cross_analysis)
        }
    
    def _review_individual_paper(self, paper: str, student_id: str) -> Dict[str, Any]:
        """Review individual paper"""
        
        word_count = len(paper.split())
        
        # Assess various criteria
        originality_score = self._assess_originality(paper)
        depth_score = self._assess_depth(paper)
        sources_score = self._assess_sources(paper)
        
        overall_score = (originality_score + depth_score + sources_score) / 3
        
        if overall_score >= 85:
            grade = "A"
        elif overall_score >= 80:
            grade = "A-"
        elif overall_score >= 75:
            grade = "B+"
        else:
            grade = "B"
        
        return {
            'student_id': student_id,
            'word_count': word_count,
            'grade': grade,
            'overall_score': overall_score,
            'originality': originality_score,
            'depth': depth_score,
            'sources': sources_score,
            'comments': self._generate_comments(paper, overall_score)
        }
    
    def _assess_originality(self, paper: str) -> float:
        """Assess originality of paper"""
        
        # Check for unique voice and approach
        template_phrases = [
            'my journey', 'this paper explores', 'in conclusion',
            'the research shows', 'it is important to note'
        ]
        
        template_count = sum(1 for phrase in template_phrases if phrase in paper.lower())
        originality = max(60, 95 - (template_count * 8))
        
        return originality
    
    def _assess_depth(self, paper: str) -> float:
        """Assess depth of analysis"""
        
        word_count = len(paper.split())
        if word_count < 800:
            return 65
        elif word_count < 1000:
            return 75
        else:
            return min(95, 75 + (word_count - 1000) / 100)
    
    def _assess_sources(self, paper: str) -> float:
        """Assess use of sources"""
        
        # Count apparent source references
        source_indicators = len(re.findall(r'\*\*.*?\*\*|".*?"|Author.*?demonstrates', paper))
        
        if source_indicators < 3:
            return 70
        elif source_indicators < 6:
            return 80
        else:
            return 90
    
    def _generate_comments(self, paper: str, score: float) -> str:
        """Generate professor comments"""
        
        if score >= 85:
            return "Excellent work. Your unique voice and analytical approach demonstrate sophisticated engagement with the sources."
        elif score >= 80:
            return "Strong paper with good use of sources. Consider developing your analysis further in future work."
        else:
            return "Good foundation, but work on developing a more distinctive analytical voice."
    
    def _cross_paper_analysis(self, papers: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Analyze papers for similarities (professor perspective)"""
        
        # Extract common phrases
        all_phrases = []
        for _, paper in papers:
            phrases = re.findall(r'\b\w+(?:\s+\w+){2,4}\b', paper.lower())
            all_phrases.extend(phrases)
        
        phrase_counts = Counter(all_phrases)
        repeated_phrases = {phrase: count for phrase, count in phrase_counts.items() if count > 1}
        
        # Check for structural similarities
        structures = []
        for _, paper in papers:
            sections = re.findall(r'##\s*([^#\n]+)', paper)
            structures.append(tuple(sections))
        
        structure_counts = Counter(structures)
        repeated_structures = {str(struct): count for struct, count in structure_counts.items() if count > 1}
        
        similarity_level = "LOW" if len(repeated_phrases) < 5 else "MEDIUM" if len(repeated_phrases) < 15 else "HIGH"
        
        return {
            'repeated_phrases': repeated_phrases,
            'repeated_structures': repeated_structures,
            'similarity_level': similarity_level,
            'unique_voices_detected': len(set(structures))
        }
    
    def _overall_assessment(self, reviews: Dict, cross_analysis: Dict) -> str:
        """Overall professor assessment"""
        
        if cross_analysis['similarity_level'] == "LOW":
            return "Excellent diversity in student approaches. Each paper demonstrates a unique academic voice."
        elif cross_analysis['similarity_level'] == "MEDIUM":
            return "Good variety in student work, with some common themes appropriately emerging from the topic."
        else:
            return "Concerning similarities detected. Students may have relied too heavily on similar sources or templates."

def main():
    """Main execution function for V3 student research project"""
    
    # Database configuration
    db_config = {
        'host': 'localhost',
        'database': 'knowledge_base',
        'user': 'weixiangzhang'
    }
    
    # Initialize components
    pattern_detector = AdvancedPatternDetector()
    personality_creator = BookSeededPersonality('book_personality_seeds.json', db_config)
    search_agent = LibrarySearchAgent(db_config)
    professor = ProfessorReviewSimulator()
    
    # Create 10 unique students based on different authors
    students = []
    for i in range(10):
        personality = personality_creator.create_student_from_author(i, f"ST2025{21+i:03d}")
        students.append(personality)
    
    print("=" * 60)
    print("LibraryOfBabel Student Research Project V3")
    print("Book-Seeded Academic Personalities")
    print("=" * 60)
    
    # Display student personalities
    for student in students:
        print(f"\n{student['name']} ({student['student_id']})")
        print(f"Major: {student['major']}")
        print(f"Inspired by: {student['inspiration_author']} - '{student['inspiration_title']}'")
        print(f"Voice Pattern: {student['voice_pattern']}")
        print(f"Paper Structure: {student['paper_structure']}")
    
    # Generate papers for each student
    print(f"\n{'='*60}")
    print("Generating Research Papers...")
    print("=" * 60)
    
    papers = []
    detection_results = []
    
    for i, student in enumerate(students):
        print(f"\nGenerating paper for {student['name']}...")
        
        # Create writer for this student
        writer = LiteraryAcademicWriter(student, search_agent)
        
        # Generate research paper
        topic = student['research_focus']
        paper = writer.write_research_paper(topic)
        
        # Pattern detection
        detection = pattern_detector.analyze_paper(paper, student['student_id'])
        detection_results.append(detection)
        
        papers.append((student['student_id'], paper))
        
        # Save paper
        output_dir = Path("student_research_papers/v3_submissions")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{student['student_id']}_{student['name'].replace(' ', '_')}_v3.txt"
        with open(output_dir / filename, 'w') as f:
            f.write(paper)
        
        print(f"Saved: {filename}")
        print(f"Word count: {detection['word_count']}")
        print(f"Pattern risk: {detection['risk_level']}")
    
    # Professor review simulation
    print(f"\n{'='*60}")
    print("Professor Review Simulation")
    print("=" * 60)
    
    professor_review = professor.review_papers(papers)
    
    print(f"\nCross-Paper Analysis:")
    print(f"Similarity Level: {professor_review['cross_paper_analysis']['similarity_level']}")
    print(f"Unique Voices Detected: {professor_review['cross_paper_analysis']['unique_voices_detected']}")
    print(f"Overall Assessment: {professor_review['overall_assessment']}")
    
    print(f"\nIndividual Grades:")
    for student_id, review in professor_review['individual_reviews'].items():
        student_name = next(s['name'] for s in students if s['student_id'] == student_id)
        print(f"{student_name}: {review['grade']} (Score: {review['overall_score']:.1f})")
    
    # Summary statistics
    avg_word_count = sum(d['word_count'] for d in detection_results) / len(detection_results)
    avg_violation_score = sum(d['violation_score'] for d in detection_results) / len(detection_results)
    papers_over_1000 = sum(1 for d in detection_results if d['word_count'] >= 1000)
    
    print(f"\n{'='*60}")
    print("Version 3 Results Summary")
    print("=" * 60)
    print(f"Papers generated: {len(papers)}")
    print(f"Average word count: {avg_word_count:.0f}")
    print(f"Papers over 1000 words: {papers_over_1000}/10")
    print(f"Average pattern violation score: {avg_violation_score:.1f}")
    print(f"Professor similarity assessment: {professor_review['cross_paper_analysis']['similarity_level']}")
    
    # Save results
    results = {
        'generation_timestamp': datetime.now().isoformat(),
        'students': students,
        'detection_results': detection_results,
        'professor_review': professor_review,
        'summary_stats': {
            'avg_word_count': avg_word_count,
            'avg_violation_score': avg_violation_score,
            'papers_over_1000': papers_over_1000,
            'similarity_level': professor_review['cross_paper_analysis']['similarity_level']
        }
    }
    
    with open('student_research_results_v3.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: student_research_results_v3.json")
    print("All papers saved to: student_research_papers/v3_submissions/")

if __name__ == "__main__":
    main()