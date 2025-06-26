#!/usr/bin/env python3
"""
Natural Language Query Processor
================================

Processes natural language queries from AI research agents and converts them
into structured search parameters for the LibraryOfBabel search system.

Author: API Agent
Version: 1.0
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Types of queries the system can handle."""
    GENERAL = "general"
    AUTHOR = "author"
    TOPIC = "topic"
    CROSS_REFERENCE = "cross_reference"
    QUOTE_EXTRACTION = "quote_extraction"
    BOOK_RECOMMENDATION = "book_recommendation"
    TEMPORAL = "temporal"
    COMPARATIVE = "comparative"

@dataclass
class ProcessedQuery:
    """Processed query with extracted parameters."""
    original_query: str
    query_type: QueryType
    search_terms: List[str]
    filters: Dict[str, Any]
    concepts: List[str]
    authors: List[str]
    temporal_constraints: Dict[str, Any]
    intent: str
    confidence: float

class QueryProcessor:
    """Natural language query processor for research queries."""
    
    def __init__(self):
        """Initialize the query processor."""
        self.author_patterns = [
            r"(?:by|author|written by|works? (?:by|of))\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"find books by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'s (?:work|book|writing)",
        ]
        
        self.temporal_patterns = [
            r"(?:from|in|during|written in|published in)\s+(\d{4})",
            r"(\d{4})s?",
            r"(?:before|after|since)\s+(\d{4})",
            r"between\s+(\d{4})\s+and\s+(\d{4})",
        ]
        
        self.cross_reference_patterns = [
            r"(?:connection|relationship|link)\s+between\s+(.+?)\s+and\s+(.+?)(?:\?|$)",
            r"(.+?)\s+(?:and|vs|versus|compared to)\s+(.+?)(?:\?|$)",
            r"how (?:does|do)\s+(.+?)\s+relate to\s+(.+?)(?:\?|$)",
            r"both\s+(.+?)\s+and\s+(.+?)(?:\?|$)",
        ]
        
        self.quote_patterns = [
            r"(?:quote|passage|excerpt|text)\s+(?:about|on|regarding)\s+(.+?)(?:\?|$)",
            r"find (?:quotes|passages)\s+(?:about|on|regarding)\s+(.+?)(?:\?|$)",
            r"what (?:does|do)\s+(.+?)\s+say about\s+(.+?)(?:\?|$)",
        ]
        
        self.recommendation_patterns = [
            r"(?:similar|like|related)\s+(?:to|as)\s+(.+?)(?:\?|$)",
            r"recommend books?\s+(?:about|on|like)\s+(.+?)(?:\?|$)",
            r"what should I read\s+(?:about|on|next|after)\s+(.+?)(?:\?|$)",
            r"books?\s+(?:similar to|like)\s+(.+?)(?:\?|$)",
        ]
        
        self.comparative_patterns = [
            r"compare\s+(.+?)\s+(?:and|with|to|vs|versus)\s+(.+?)(?:\?|$)",
            r"difference between\s+(.+?)\s+and\s+(.+?)(?:\?|$)",
            r"(?:similarities|differences)\s+(?:between|of)\s+(.+?)\s+and\s+(.+?)(?:\?|$)",
        ]
        
        self.topic_indicators = [
            "about", "on", "regarding", "concerning", "related to",
            "dealing with", "focused on", "covering", "discussing"
        ]
        
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
            'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
        }
    
    def process_query(self, query: str) -> ProcessedQuery:
        """
        Process a natural language query and extract structured information.
        
        Args:
            query: Natural language query string
            
        Returns:
            ProcessedQuery with extracted parameters
        """
        query = query.strip()
        original_query = query
        
        # Determine query type and extract relevant information
        query_type, confidence = self._classify_query(query)
        
        # Extract different components based on query type
        search_terms = self._extract_search_terms(query)
        authors = self._extract_authors(query)
        concepts = self._extract_concepts(query, query_type)
        temporal_constraints = self._extract_temporal_constraints(query)
        filters = self._build_filters(query, authors, temporal_constraints)
        intent = self._determine_intent(query, query_type)
        
        return ProcessedQuery(
            original_query=original_query,
            query_type=query_type,
            search_terms=search_terms,
            filters=filters,
            concepts=concepts,
            authors=authors,
            temporal_constraints=temporal_constraints,
            intent=intent,
            confidence=confidence
        )
    
    def _classify_query(self, query: str) -> Tuple[QueryType, float]:
        """Classify the type of query and return confidence score."""
        query_lower = query.lower()
        
        # Check for author queries
        if any(re.search(pattern, query, re.IGNORECASE) for pattern in self.author_patterns):
            return QueryType.AUTHOR, 0.9
        
        # Check for cross-reference queries
        if any(re.search(pattern, query, re.IGNORECASE) for pattern in self.cross_reference_patterns):
            return QueryType.CROSS_REFERENCE, 0.9
        
        # Check for quote extraction queries
        if any(re.search(pattern, query, re.IGNORECASE) for pattern in self.quote_patterns):
            return QueryType.QUOTE_EXTRACTION, 0.9
        
        # Check for recommendation queries
        if any(re.search(pattern, query, re.IGNORECASE) for pattern in self.recommendation_patterns):
            return QueryType.BOOK_RECOMMENDATION, 0.9
        
        # Check for comparative queries
        if any(re.search(pattern, query, re.IGNORECASE) for pattern in self.comparative_patterns):
            return QueryType.COMPARATIVE, 0.9
        
        # Check for temporal queries
        if any(re.search(pattern, query) for pattern in self.temporal_patterns):
            return QueryType.TEMPORAL, 0.8
        
        # Check for topic queries
        if any(indicator in query_lower for indicator in self.topic_indicators):
            return QueryType.TOPIC, 0.7
        
        # Default to general query
        return QueryType.GENERAL, 0.6
    
    def _extract_search_terms(self, query: str) -> List[str]:
        """Extract main search terms from the query."""
        # Remove common question words and patterns
        cleaned_query = re.sub(r'^(?:find|search|look for|show me|get|what|how|where|when|why|who)\s+', '', query, flags=re.IGNORECASE)
        cleaned_query = re.sub(r'\?$', '', cleaned_query)
        
        # Remove author patterns
        for pattern in self.author_patterns:
            cleaned_query = re.sub(pattern, '', cleaned_query, flags=re.IGNORECASE)
        
        # Remove temporal patterns
        for pattern in self.temporal_patterns:
            cleaned_query = re.sub(pattern, '', cleaned_query)
        
        # Split into words and filter
        words = re.findall(r'\b[a-zA-Z]{3,}\b', cleaned_query.lower())
        
        # Remove stop words and short words
        search_terms = [word for word in words if word not in self.stop_words and len(word) >= 3]
        
        return search_terms
    
    def _extract_authors(self, query: str) -> List[str]:
        """Extract author names from the query."""
        authors = []
        
        for pattern in self.author_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                # Clean up the author name
                author = re.sub(r'\s+', ' ', match).strip()
                if author and len(author) > 2:
                    authors.append(author.title())
        
        return authors
    
    def _extract_concepts(self, query: str, query_type: QueryType) -> List[str]:
        """Extract key concepts from the query based on query type."""
        concepts = []
        
        if query_type == QueryType.CROSS_REFERENCE:
            # Extract concepts from cross-reference patterns
            for pattern in self.cross_reference_patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    concept1 = match.group(1).strip()
                    concept2 = match.group(2).strip()
                    concepts.extend([concept1, concept2])
                    break
        
        elif query_type == QueryType.COMPARATIVE:
            # Extract concepts from comparative patterns
            for pattern in self.comparative_patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    concept1 = match.group(1).strip()
                    concept2 = match.group(2).strip()
                    concepts.extend([concept1, concept2])
                    break
        
        elif query_type == QueryType.QUOTE_EXTRACTION:
            # Extract topic from quote patterns
            for pattern in self.quote_patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    if len(match.groups()) >= 2:
                        concepts.extend([match.group(1).strip(), match.group(2).strip()])
                    else:
                        concepts.append(match.group(1).strip())
                    break
        
        elif query_type == QueryType.TOPIC:
            # Extract topic after topic indicators
            for indicator in self.topic_indicators:
                pattern = rf"{indicator}\s+(.+?)(?:\?|$)"
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    concept = match.group(1).strip()
                    concepts.append(concept)
                    break
        
        # Clean up concepts
        cleaned_concepts = []
        for concept in concepts:
            # Remove articles and common words from the beginning
            concept = re.sub(r'^(?:the|a|an)\s+', '', concept, flags=re.IGNORECASE)
            concept = concept.strip()
            if concept and len(concept) > 2:
                cleaned_concepts.append(concept)
        
        return cleaned_concepts
    
    def _extract_temporal_constraints(self, query: str) -> Dict[str, Any]:
        """Extract temporal constraints from the query."""
        constraints = {}
        
        # Single year
        year_match = re.search(r'\b(\d{4})\b', query)
        if year_match:
            year = int(year_match.group(1))
            if 1800 <= year <= 2030:  # Reasonable range for books
                constraints['year'] = year
        
        # Year range
        range_match = re.search(r'between\s+(\d{4})\s+and\s+(\d{4})', query, re.IGNORECASE)
        if range_match:
            start_year = int(range_match.group(1))
            end_year = int(range_match.group(2))
            constraints['year_range'] = {'start': start_year, 'end': end_year}
        
        # Before/after constraints
        before_match = re.search(r'before\s+(\d{4})', query, re.IGNORECASE)
        if before_match:
            constraints['before_year'] = int(before_match.group(1))
        
        after_match = re.search(r'(?:after|since)\s+(\d{4})', query, re.IGNORECASE)
        if after_match:
            constraints['after_year'] = int(after_match.group(1))
        
        # Decade references
        decade_match = re.search(r'(\d{4})s', query)
        if decade_match:
            decade_start = int(decade_match.group(1))
            constraints['decade'] = decade_start
        
        return constraints
    
    def _build_filters(self, query: str, authors: List[str], 
                      temporal_constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Build search filters from extracted information."""
        filters = {}
        
        # Author filters
        if authors:
            filters['author'] = authors[0]  # Use first author for now
        
        # Temporal filters
        if 'year' in temporal_constraints:
            filters['year'] = temporal_constraints['year']
        elif 'year_range' in temporal_constraints:
            filters['year_range'] = temporal_constraints['year_range']
        elif 'before_year' in temporal_constraints:
            filters['before_year'] = temporal_constraints['before_year']
        elif 'after_year' in temporal_constraints:
            filters['after_year'] = temporal_constraints['after_year']
        elif 'decade' in temporal_constraints:
            decade = temporal_constraints['decade']
            filters['year_range'] = {'start': decade, 'end': decade + 9}
        
        # Genre/subject filters
        genre_patterns = [
            r'(?:fiction|novel|story|narrative)',
            r'(?:non-fiction|nonfiction|biography|memoir|history)',
            r'(?:science|scientific|research|academic)',
            r'(?:philosophy|philosophical|ethics|moral)',
            r'(?:economics|economic|business|finance)',
            r'(?:politics|political|government|policy)',
            r'(?:psychology|psychological|mental|cognitive)',
            r'(?:technology|technical|engineering|computer)',
        ]
        
        query_lower = query.lower()
        for pattern in genre_patterns:
            if re.search(pattern, query_lower):
                # Extract the genre keyword
                match = re.search(pattern, query_lower)
                if match:
                    filters['genre'] = match.group(0)
                break
        
        # Length filters
        length_match = re.search(r'(?:short|long|brief|comprehensive|detailed)\s+(?:book|work)', query_lower)
        if length_match:
            length_type = length_match.group(0).split()[0]
            if length_type in ['short', 'brief']:
                filters['max_words'] = 50000
            elif length_type in ['long', 'comprehensive', 'detailed']:
                filters['min_words'] = 100000
        
        return filters
    
    def _determine_intent(self, query: str, query_type: QueryType) -> str:
        """Determine the user's intent from the query."""
        query_lower = query.lower()
        
        if query_type == QueryType.AUTHOR:
            if any(word in query_lower for word in ['all', 'everything', 'complete', 'bibliography']):
                return "find_complete_works"
            else:
                return "find_books_by_author"
        
        elif query_type == QueryType.CROSS_REFERENCE:
            return "find_conceptual_connections"
        
        elif query_type == QueryType.QUOTE_EXTRACTION:
            return "extract_relevant_quotes"
        
        elif query_type == QueryType.BOOK_RECOMMENDATION:
            if 'similar' in query_lower or 'like' in query_lower:
                return "find_similar_books"
            else:
                return "recommend_books_on_topic"
        
        elif query_type == QueryType.COMPARATIVE:
            return "compare_concepts_or_authors"
        
        elif query_type == QueryType.TEMPORAL:
            return "find_books_by_time_period"
        
        elif query_type == QueryType.TOPIC:
            if any(word in query_lower for word in ['overview', 'summary', 'introduction']):
                return "find_introductory_material"
            elif any(word in query_lower for word in ['advanced', 'detailed', 'comprehensive']):
                return "find_advanced_material"
            else:
                return "find_topic_material"
        
        else:  # GENERAL
            if any(word in query_lower for word in ['research', 'study', 'analysis']):
                return "research_support"
            else:
                return "general_search"
    
    def to_api_params(self, processed_query: ProcessedQuery) -> Dict[str, Any]:
        """Convert processed query to API search parameters."""
        # Determine the main search query
        if processed_query.concepts:
            if processed_query.query_type == QueryType.CROSS_REFERENCE:
                search_query = ', '.join(processed_query.concepts)
            else:
                search_query = ' '.join(processed_query.concepts)
        elif processed_query.search_terms:
            search_query = ' '.join(processed_query.search_terms)
        else:
            search_query = processed_query.original_query
        
        # Map query type to API search type
        type_mapping = {
            QueryType.GENERAL: 'general',
            QueryType.AUTHOR: 'author',
            QueryType.TOPIC: 'topic',
            QueryType.CROSS_REFERENCE: 'cross_reference',
            QueryType.QUOTE_EXTRACTION: 'general',  # Use general with special processing
            QueryType.BOOK_RECOMMENDATION: 'topic',
            QueryType.TEMPORAL: 'general',
            QueryType.COMPARATIVE: 'cross_reference'
        }
        
        api_params = {
            'query': search_query,
            'type': type_mapping.get(processed_query.query_type, 'general'),
            'filters': processed_query.filters,
            'limit': 10,
            'offset': 0
        }
        
        # Add special parameters for certain query types
        if processed_query.query_type == QueryType.QUOTE_EXTRACTION:
            api_params['extract_quotes'] = True
            api_params['context_length'] = 200
        
        elif processed_query.query_type == QueryType.BOOK_RECOMMENDATION:
            api_params['suggest_similar'] = True
        
        return api_params
    
    def enhance_results_for_intent(self, results: Dict[str, Any], 
                                  processed_query: ProcessedQuery) -> Dict[str, Any]:
        """Enhance search results based on the determined intent."""
        enhanced_results = results.copy()
        
        # Add intent-specific metadata
        enhanced_results['intent'] = processed_query.intent
        enhanced_results['query_type'] = processed_query.query_type.value
        enhanced_results['confidence'] = processed_query.confidence
        enhanced_results['extracted_concepts'] = processed_query.concepts
        enhanced_results['extracted_authors'] = processed_query.authors
        
        # Add intent-specific recommendations
        if processed_query.intent == "research_support":
            enhanced_results['research_tips'] = [
                "Consider cross-referencing these results with primary sources",
                "Look for conflicting viewpoints on this topic",
                "Check publication dates for historical context"
            ]
        
        elif processed_query.intent == "find_introductory_material":
            # Prioritize books with higher accessibility
            if 'results' in enhanced_results:
                for result in enhanced_results['results']:
                    # Boost scores for books with "introduction", "guide", "basics" in title
                    title_lower = result.get('title', '').lower()
                    if any(word in title_lower for word in ['introduction', 'guide', 'basics', 'primer']):
                        result['relevance_score'] = result.get('relevance_score', 0) * 1.2
        
        elif processed_query.intent == "find_advanced_material":
            # Add note about complexity
            enhanced_results['note'] = "Results prioritized for advanced/comprehensive material"
        
        return enhanced_results


def demo_query_processing():
    """Demonstrate query processing capabilities."""
    processor = QueryProcessor()
    
    test_queries = [
        "Find books by Michel Foucault",
        "What is the connection between power and knowledge?",
        "Books about artificial intelligence and ethics",
        "Compare Marx and Weber on capitalism",
        "Find quotes about digital identity",
        "Recommend books similar to 'Discipline and Punish'",
        "Books on philosophy written in the 1980s",
        "What do authors say about surveillance?",
        "Overview of postmodern theory",
        "Advanced material on machine learning ethics"
    ]
    
    print("LibraryOfBabel Query Processing Demo")
    print("=" * 40)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        processed = processor.process_query(query)
        
        print(f"Type: {processed.query_type.value}")
        print(f"Intent: {processed.intent}")
        print(f"Confidence: {processed.confidence:.2f}")
        print(f"Search Terms: {processed.search_terms}")
        print(f"Concepts: {processed.concepts}")
        print(f"Authors: {processed.authors}")
        print(f"Filters: {processed.filters}")
        
        # Show API parameters
        api_params = processor.to_api_params(processed)
        print(f"API Params: {json.dumps(api_params, indent=2)}")
        print("-" * 40)


if __name__ == "__main__":
    demo_query_processing()