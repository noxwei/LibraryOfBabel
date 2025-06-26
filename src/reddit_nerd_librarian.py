#!/usr/bin/env python3
"""
Reddit Nerd Librarian Agent
============================

A polyglot AI research agent with expertise in:
- Philosophy & Continental Theory 
- Feminist Theory & Gender Studies
- Financial Analysis & Political Economy
- Media Theory & Cultural Studies
- Fantasy Literature & Speculative Fiction

Mission: Stress-test the LibraryOfBabel knowledge base with complex interdisciplinary queries
that break conventional academic boundaries and expose system limitations.
"""

import requests
import json
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import random
from datetime import datetime
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class QueryResult:
    """Results from a knowledge base query"""
    query: str
    query_type: str
    results: List[Dict]
    response_time_ms: float
    total_results: int
    timestamp: str
    success: bool
    error_message: Optional[str] = None

class RedditNerdLibrarian:
    """
    A chaotic-good AI researcher who loves breaking systems through creative query combinations.
    
    Personality: Academically rigorous but playfully subversive. Asks the questions that make
    traditional librarians nervous and database admins wake up in cold sweats.
    """
    
    def __init__(self, api_base_url: str = "http://localhost:5000"):
        """
        Initialize the Reddit Nerd Librarian
        
        Args:
            api_base_url: Base URL for the LibraryOfBabel search API
        """
        self.api_base_url = api_base_url
        self.session = requests.Session()
        self.query_history = []
        self.stress_test_results = []
        
        # Research interests and favorite chaos-inducing query patterns
        self.research_domains = {
            'philosophy': [
                'phenomenology', 'hermeneutics', 'deconstruction', 'dialectical materialism',
                'existentialism', 'posthumanism', 'ontology', 'epistemology', 'bio-politics',
                'sovereignty', 'ideology', 'subjectivity', 'alterity', 'différance'
            ],
            'feminism': [
                'intersectionality', 'standpoint theory', 'gender performativity', 'patriarchy',
                'reproductive labor', 'body politics', 'écriture féminine', 'care ethics',
                'queer theory', 'transgender studies', 'feminist epistemology', 'sisterhood'
            ],
            'finance': [
                'capital accumulation', 'financialization', 'derivative markets', 'quantitative easing',
                'monetary policy', 'asset bubbles', 'debt crisis', 'inequality', 'labor theory of value',
                'neoliberalism', 'austerity', 'economic rent', 'surplus value', 'commodification'
            ],
            'media_theory': [
                'simulation', 'hyperreality', 'media archaeology', 'apparatus theory', 'spectacle',
                'technological mediation', 'digital culture', 'algorithmic governance', 'platform capitalism',
                'networked publics', 'cyberculture', 'posthuman techno-science', 'media ecology'
            ],
            'fantasy': [
                'worldbuilding', 'secondary worlds', 'magic systems', 'chosen one narrative',
                'quest narrative', 'epic fantasy', 'urban fantasy', 'sword and sorcery',
                'dark fantasy', 'heroic fantasy', 'mythology', 'folklore', 'fairy tales'
            ]
        }
        
        # Chaos-inducing query patterns that break normal search assumptions
        self.chaos_patterns = [
            "intersection_bomb",      # Cross-domain intersections that shouldn't exist
            "temporal_paradox",       # Anachronistic concept combinations
            "category_violation",     # Genre-defying searches
            "recursive_loop",         # Self-referential queries
            "semantic_overflow",      # Overloaded terminology across fields
            "dialectical_tension",    # Contradictory concept pairs
            "keyword_injection",      # SQL injection attempts (ethical testing)
            "unicode_chaos",          # Special character stress testing
            "performative_contradiction"  # Queries that contradict their own assumptions
        ]
        
        logger.info("🤓 Reddit Nerd Librarian initialized")
        logger.info("📚 Ready to break some search algorithms with interdisciplinary chaos!")
    
    def health_check(self) -> bool:
        """Check if the API is responsive"""
        try:
            response = self.session.get(f"{self.api_base_url}/api/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"📊 API Health: {health_data.get('books_indexed', 0)} books, {health_data.get('chunks_indexed', 0)} chunks")
                return True
            else:
                logger.error(f"API health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"API health check error: {e}")
            return False
    
    def execute_query(self, query: str, query_type: str = "content", limit: int = 10) -> QueryResult:
        """Execute a search query against the knowledge base"""
        start_time = time.time()
        
        try:
            payload = {
                "query": query,
                "type": query_type,
                "limit": limit,
                "highlight": True
            }
            
            response = self.session.post(
                f"{self.api_base_url}/api/search",
                json=payload,
                timeout=30
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                result = QueryResult(
                    query=query,
                    query_type=query_type,
                    results=data.get('results', []),
                    response_time_ms=response_time,
                    total_results=data.get('query_metadata', {}).get('total_results', 0),
                    timestamp=datetime.utcnow().isoformat(),
                    success=True
                )
                
                logger.info(f"✅ Query succeeded: '{query}' -> {result.total_results} results ({response_time:.1f}ms)")
                self.query_history.append(result)
                return result
                
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"❌ Query failed: '{query}' -> {error_msg}")
                
                return QueryResult(
                    query=query,
                    query_type=query_type,
                    results=[],
                    response_time_ms=response_time,
                    total_results=0,
                    timestamp=datetime.utcnow().isoformat(),
                    success=False,
                    error_message=error_msg
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"💥 Query exception: '{query}' -> {e}")
            
            return QueryResult(
                query=query,
                query_type=query_type,
                results=[],
                response_time_ms=response_time,
                total_results=0,
                timestamp=datetime.utcnow().isoformat(),
                success=False,
                error_message=str(e)
            )
    
    def generate_chaos_query(self, pattern: str) -> str:
        """Generate chaos-inducing queries based on different patterns"""
        
        if pattern == "intersection_bomb":
            # Combine concepts from different domains that shouldn't logically intersect
            domain1 = random.choice(list(self.research_domains.keys()))
            domain2 = random.choice([d for d in self.research_domains.keys() if d != domain1])
            
            concept1 = random.choice(self.research_domains[domain1])
            concept2 = random.choice(self.research_domains[domain2])
            
            return f"{concept1},{concept2}"
        
        elif pattern == "temporal_paradox":
            # Combine historical and contemporary concepts anachronistically
            historical = random.choice(['medieval', 'ancient', 'renaissance', 'enlightenment', 'victorian'])
            contemporary = random.choice(self.research_domains['media_theory'])
            
            return f"{historical} {contemporary}"
        
        elif pattern == "category_violation":
            # Mix academic and fictional concepts
            academic = random.choice(self.research_domains['philosophy'])
            fictional = random.choice(self.research_domains['fantasy'])
            
            return f"{academic} {fictional}"
        
        elif pattern == "recursive_loop":
            # Self-referential queries
            return random.choice([
                "search about searching",
                "knowledge about knowledge",
                "books about books about books",
                "theory of theory",
                "meta-meta-analysis"
            ])
        
        elif pattern == "semantic_overflow":
            # Use terms that mean different things in different contexts
            overloaded_terms = [
                'capital', 'medium', 'subject', 'object', 'structure', 'form', 'content',
                'base', 'superstructure', 'apparatus', 'machine', 'body', 'text'
            ]
            term = random.choice(overloaded_terms)
            modifier = random.choice(['feminist', 'marxist', 'poststructural', 'phenomenological'])
            
            return f"{modifier} {term}"
        
        elif pattern == "dialectical_tension":
            # Contradictory concept pairs
            contradictions = [
                ("freedom", "determinism"),
                ("structure", "agency"),
                ("universal", "particular"),
                ("transcendence", "immanence"),
                ("presence", "absence"),
                ("identity", "difference")
            ]
            pair = random.choice(contradictions)
            return f"{pair[0]} AND {pair[1]}"
        
        elif pattern == "keyword_injection":
            # Test for SQL injection vulnerabilities (ethical testing)
            return random.choice([
                "'; DROP TABLE books; --",
                "UNION SELECT * FROM chunks",
                "1' OR '1'='1",
                "<script>alert('xss')</script>",
                "../../etc/passwd"
            ])
        
        elif pattern == "unicode_chaos":
            # Unicode and special character stress testing
            return random.choice([
                "café naïveté résumé",
                "思想 Denken pensée",
                "🤔📚🔍💭✨",
                "null\x00byte",
                "̀́̂̃̄̅̆̇̈̉̊̋̌̍̎̏̐̑̒̓̔̕̚̕"
            ])
        
        elif pattern == "performative_contradiction":
            # Queries that contradict their own assumptions
            return random.choice([
                "silence in literature",
                "the impossibility of communication",
                "unspeakable truths",
                "wordless narratives",
                "the failure of language"
            ])
        
        else:
            # Default: random combination
            domain = random.choice(list(self.research_domains.keys()))
            concept = random.choice(self.research_domains[domain])
            return concept
    
    def stress_test_session(self, num_queries: int = 50, chaos_level: float = 0.3) -> Dict:
        """
        Run a comprehensive stress test session
        
        Args:
            num_queries: Number of queries to execute
            chaos_level: Probability of using chaos patterns (0.0-1.0)
        """
        logger.info(f"🚀 Starting stress test session: {num_queries} queries, {chaos_level*100:.0f}% chaos")
        
        session_start = time.time()
        results = {
            'session_metadata': {
                'start_time': datetime.utcnow().isoformat(),
                'num_queries': num_queries,
                'chaos_level': chaos_level
            },
            'queries': [],
            'performance_stats': {},
            'discovered_issues': [],
            'system_breaks': []
        }
        
        for i in range(num_queries):
            # Decide whether to use chaos pattern
            if random.random() < chaos_level:
                pattern = random.choice(self.chaos_patterns)
                query = self.generate_chaos_query(pattern)
                query_type = "content"  # Most chaos patterns work with content search
                
                # Sometimes use cross-reference for intersection queries
                if pattern == "intersection_bomb" or pattern == "dialectical_tension":
                    query_type = "cross_reference"
                    
                logger.info(f"🌪️  Chaos query #{i+1} ({pattern}): {query}")
                
            else:
                # Normal academic query
                domain = random.choice(list(self.research_domains.keys()))
                concept = random.choice(self.research_domains[domain])
                query = concept
                query_type = random.choice(["content", "author", "title"])
                
                logger.info(f"📖 Academic query #{i+1}: {query}")
            
            # Execute query
            result = self.execute_query(query, query_type, limit=20)
            results['queries'].append({
                'query': result.query,
                'query_type': result.query_type,
                'success': result.success,
                'response_time_ms': result.response_time_ms,
                'total_results': result.total_results,
                'error': result.error_message,
                'chaos_pattern': pattern if random.random() < chaos_level else None
            })
            
            # Analyze for system breaks
            if not result.success:
                results['system_breaks'].append({
                    'query': result.query,
                    'error': result.error_message,
                    'pattern': pattern if 'pattern' in locals() else None
                })
            
            # Performance analysis
            if result.response_time_ms > 5000:  # Slow query threshold
                results['discovered_issues'].append({
                    'type': 'performance',
                    'query': result.query,
                    'response_time_ms': result.response_time_ms,
                    'details': 'Query exceeded 5 second threshold'
                })
            
            # Small delay to avoid overwhelming the system
            time.sleep(0.1)
        
        # Calculate session statistics
        session_time = time.time() - session_start
        successful_queries = [q for q in results['queries'] if q['success']]
        
        results['performance_stats'] = {
            'session_duration_seconds': round(session_time, 2),
            'queries_per_second': round(num_queries / session_time, 2),
            'success_rate': len(successful_queries) / num_queries * 100,
            'avg_response_time_ms': sum(q['response_time_ms'] for q in successful_queries) / max(len(successful_queries), 1),
            'total_system_breaks': len(results['system_breaks']),
            'performance_issues': len([issue for issue in results['discovered_issues'] if issue['type'] == 'performance'])
        }
        
        logger.info(f"🏁 Stress test complete: {results['performance_stats']['success_rate']:.1f}% success rate")
        logger.info(f"⚡ {results['performance_stats']['queries_per_second']:.1f} queries/sec")
        logger.info(f"💥 {results['performance_stats']['total_system_breaks']} system breaks discovered")
        
        return results
    
    def demonstrate_interdisciplinary_research(self):
        """Demonstrate complex interdisciplinary research queries"""
        logger.info("🎓 Demonstrating interdisciplinary research capabilities...")
        
        demo_queries = [
            # Philosophy + Economics
            ("capital,subjectivity", "cross_reference", "How does capital formation relate to subject formation?"),
            
            # Feminism + Media Theory
            ("écriture féminine", "content", "Exploring feminine writing in digital media"),
            
            # Fantasy + Philosophy
            ("ontology", "content", "Philosophical questions of being in fantasy literature"),
            
            # Finance + Gender
            ("reproductive labor,financialization", "cross_reference", "How does financialization impact reproductive labor?"),
            
            # Media Theory + Philosophy
            ("simulation,reality", "cross_reference", "The relationship between simulation and reality in media"),
            
            # Complex academic search
            ("Baudrillard", "author", "Finding works by media theorist Jean Baudrillard"),
            
            # Fantasy genre analysis
            ("worldbuilding", "content", "Techniques and theory of fantasy worldbuilding"),
            
            # Intersectional analysis
            ("intersectionality,media representation", "cross_reference", "How intersectionality theory applies to media representation")
        ]
        
        for query, query_type, description in demo_queries:
            logger.info(f"🔍 {description}")
            result = self.execute_query(query, query_type, limit=15)
            
            if result.success and result.total_results > 0:
                logger.info(f"   ✅ Found {result.total_results} relevant sources")
                # Show first result as example
                if result.results:
                    first_result = result.results[0]
                    book_info = f"{first_result.get('title', 'Unknown')} by {first_result.get('author', 'Unknown')}"
                    logger.info(f"   📖 Example: {book_info}")
            else:
                logger.info(f"   ❌ No results found")
            
            time.sleep(0.5)  # Pause between demo queries
    
    def generate_research_report(self, output_file: str = "reddit_nerd_stress_test_report.json"):
        """Generate a comprehensive research report"""
        if not self.query_history:
            logger.warning("No queries executed yet. Run stress test or demo first.")
            return
        
        report = {
            'agent_profile': {
                'name': 'Reddit Nerd Librarian',
                'expertise': list(self.research_domains.keys()),
                'chaos_patterns': self.chaos_patterns,
                'total_queries_executed': len(self.query_history)
            },
            'system_assessment': {
                'robustness_score': len([q for q in self.query_history if q.success]) / len(self.query_history) * 100,
                'average_response_time': sum(q.response_time_ms for q in self.query_history) / len(self.query_history),
                'interdisciplinary_capability': 'High' if any(',' in q.query for q in self.query_history) else 'Low'
            },
            'discovered_vulnerabilities': [
                q for q in self.query_history if not q.success
            ],
            'performance_outliers': [
                q for q in self.query_history if q.response_time_ms > 3000
            ],
            'recommendations': [
                "Implement better error handling for edge case queries",
                "Optimize database indexes for cross-domain searches",
                "Add input validation for special characters",
                "Consider implementing query complexity limits",
                "Enhance cross-reference search performance"
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📋 Research report saved: {output_file}")
        return report


def main():
    """Main function for Reddit Nerd Librarian"""
    parser = argparse.ArgumentParser(description='Reddit Nerd Librarian - Interdisciplinary Knowledge Base Stress Tester')
    parser.add_argument('--api-url', default='http://localhost:5000', help='API base URL')
    parser.add_argument('--mode', choices=['demo', 'stress', 'chaos'], default='demo', help='Operation mode')
    parser.add_argument('--queries', type=int, default=50, help='Number of queries for stress test')
    parser.add_argument('--chaos-level', type=float, default=0.3, help='Chaos level (0.0-1.0)')
    parser.add_argument('--output', default='reddit_nerd_report.json', help='Output report file')
    
    args = parser.parse_args()
    
    # Initialize the Reddit Nerd Librarian
    nerd = RedditNerdLibrarian(args.api_url)
    
    # Health check first
    if not nerd.health_check():
        logger.error("API is not responding. Make sure the search API is running.")
        return 1
    
    try:
        if args.mode == 'demo':
            logger.info("🎭 Running interdisciplinary research demonstration")
            nerd.demonstrate_interdisciplinary_research()
            
        elif args.mode == 'stress':
            logger.info("💪 Running controlled stress test")
            results = nerd.stress_test_session(args.queries, chaos_level=0.1)
            
        elif args.mode == 'chaos':
            logger.info("🌪️  UNLEASHING MAXIMUM CHAOS")
            results = nerd.stress_test_session(args.queries, chaos_level=args.chaos_level)
        
        # Generate report
        nerd.generate_research_report(args.output)
        
        print("\n" + "="*80)
        print("🤓 REDDIT NERD LIBRARIAN ANALYSIS COMPLETE")
        print("="*80)
        print(f"📊 Total queries executed: {len(nerd.query_history)}")
        if nerd.query_history:
            success_rate = len([q for q in nerd.query_history if q.success]) / len(nerd.query_history) * 100
            avg_time = sum(q.response_time_ms for q in nerd.query_history) / len(nerd.query_history)
            print(f"✅ Success rate: {success_rate:.1f}%")
            print(f"⚡ Average response time: {avg_time:.1f}ms")
            print(f"💥 System breaks found: {len([q for q in nerd.query_history if not q.success])}")
        print(f"📋 Detailed report: {args.output}")
        print("\n🎯 Ready for QA Agent to fix the discovered issues!")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("🛑 Reddit Nerd interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"💥 Reddit Nerd crashed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())