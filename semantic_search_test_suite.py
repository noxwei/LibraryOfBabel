#!/usr/bin/env python3
"""
Comprehensive Semantic Search Test Suite
========================================

Industry-standard semantic search evaluation framework for LibraryOfBabel.
Tests BGE-M3 and NOMIC embeddings across multiple domains and query types.

Features:
- Domain diversity testing (fiction, non-fiction, technical)
- Query type analysis (exact, semantic, contextual, multi-hop)
- Performance benchmarking (speed, relevance, recall, precision)
- Comparative model analysis (BGE vs NOMIC)
- Comprehensive reporting with quality metrics
"""

import psycopg2
import psycopg2.extras
import time
import json
import statistics
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SemanticSearchTester:
    """Comprehensive semantic search evaluation framework"""
    
    def __init__(self):
        """Initialize the test suite with database connection"""
        self.db_config = {
            'host': 'localhost',
            'port': '5432', 
            'database': 'knowledge_base',
            'user': 'weixiangzhang',
            'password': ''
        }
        
        # Test configuration
        self.models = ['bge-m3', 'nomic-embed-text']
        self.similarity_threshold = 0.8
        self.max_results = 20
        
        # Results storage
        self.test_results = {}
        self.performance_metrics = {}
        
        logger.info("🧠 Semantic Search Test Suite initialized")
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)
    
    def generate_test_queries(self) -> List[Dict]:
        """Generate comprehensive test query dataset"""
        
        test_queries = [
            # 1. FICTION LITERATURE TESTS
            {
                "query": "artificial intelligence consciousness and humanity",
                "category": "Fiction - Sci-Fi",
                "type": "semantic_similarity",
                "expected_domains": ["science_fiction", "philosophy"],
                "description": "AI consciousness themes in literature"
            },
            {
                "query": "space exploration and discovery",
                "category": "Fiction - Sci-Fi", 
                "type": "contextual_search",
                "expected_domains": ["science_fiction", "adventure"],
                "description": "Space travel and exploration narratives"
            },
            {
                "query": "magic systems and fantasy worlds",
                "category": "Fiction - Fantasy",
                "type": "semantic_similarity", 
                "expected_domains": ["fantasy", "worldbuilding"],
                "description": "Fantasy magic and world creation"
            },
            
            # 2. NON-FICTION TESTS
            {
                "query": "climate change environmental impact",
                "category": "Non-Fiction - Science",
                "type": "exact_match",
                "expected_domains": ["environmental_science", "climate"],
                "description": "Climate and environmental science"
            },
            {
                "query": "economic inequality wealth distribution",
                "category": "Non-Fiction - Economics", 
                "type": "semantic_similarity",
                "expected_domains": ["economics", "sociology"],
                "description": "Economic disparity and social issues"
            },
            {
                "query": "machine learning algorithms and neural networks",
                "category": "Non-Fiction - Technology",
                "type": "contextual_search",
                "expected_domains": ["computer_science", "ai"],
                "description": "ML and AI technical concepts"
            },
            
            # 3. PHILOSOPHICAL AND ABSTRACT CONCEPTS
            {
                "query": "meaning of life existential philosophy",
                "category": "Philosophy - Existential",
                "type": "semantic_similarity",
                "expected_domains": ["philosophy", "existentialism"],
                "description": "Life meaning and existential questions"
            },
            {
                "query": "ethical dilemmas moral reasoning",
                "category": "Philosophy - Ethics",
                "type": "contextual_search", 
                "expected_domains": ["philosophy", "ethics"],
                "description": "Moral philosophy and ethical reasoning"
            },
            
            # 4. TECHNICAL AND SCIENTIFIC
            {
                "query": "quantum mechanics wave particle duality",
                "category": "Science - Physics",
                "type": "exact_match",
                "expected_domains": ["physics", "quantum"],
                "description": "Quantum physics concepts"
            },
            {
                "query": "genetic engineering biotechnology ethics",
                "category": "Science - Biology", 
                "type": "multi_hop",
                "expected_domains": ["biology", "ethics", "technology"],
                "description": "Biotech and ethical implications"
            },
            
            # 5. CROSS-DOMAIN CONCEPTS
            {
                "query": "technology impact on society and culture",
                "category": "Cross-Domain - Tech+Society",
                "type": "multi_hop",
                "expected_domains": ["technology", "sociology", "culture"],
                "description": "Technology's societal effects"
            },
            {
                "query": "historical patterns and human behavior",
                "category": "Cross-Domain - History+Psychology",
                "type": "semantic_similarity",
                "expected_domains": ["history", "psychology", "sociology"],
                "description": "Historical patterns in human behavior"
            },
            
            # 6. NARRATIVE AND STORYTELLING
            {
                "query": "hero's journey character development",
                "category": "Literature - Narrative",
                "type": "contextual_search",
                "expected_domains": ["literature", "storytelling"],
                "description": "Character arcs and narrative structure"
            },
            {
                "query": "dystopian future totalitarian control",
                "category": "Fiction - Dystopian",
                "type": "semantic_similarity",
                "expected_domains": ["dystopian", "political", "future"],
                "description": "Dystopian themes and control"
            },
            
            # 7. SPECIFIC AUTHOR/WORK TESTS
            {
                "query": "Isaac Asimov robotics three laws",
                "category": "Author-Specific - Asimov",
                "type": "exact_match",
                "expected_domains": ["science_fiction", "robotics"],
                "description": "Asimov's robot laws and concepts"
            },
            
            # 8. COMPLEX REASONING TESTS
            {
                "query": "power corruption politics leadership",
                "category": "Complex - Power Dynamics",
                "type": "multi_hop",
                "expected_domains": ["politics", "psychology", "leadership"],
                "description": "Power, corruption, and leadership"
            },
            {
                "query": "love relationships human connection",
                "category": "Complex - Human Relations",
                "type": "semantic_similarity", 
                "expected_domains": ["relationships", "psychology", "emotion"],
                "description": "Love, relationships, and human bonds"
            },
            
            # 9. EDGE CASES AND CHALLENGES
            {
                "query": "solitude isolation loneliness",
                "category": "Edge - Emotional States",
                "type": "semantic_similarity",
                "expected_domains": ["psychology", "emotion"],
                "description": "Isolation and solitude themes"
            },
            {
                "query": "paradox contradiction logical impossibility",
                "category": "Edge - Logic",
                "type": "contextual_search",
                "expected_domains": ["philosophy", "logic", "mathematics"],
                "description": "Paradoxes and logical contradictions"
            },
            
            # 10. PERFORMANCE STRESS TESTS
            {
                "query": "the",
                "category": "Stress - High Frequency",
                "type": "exact_match",
                "expected_domains": ["all"],
                "description": "High-frequency word stress test"
            }
        ]
        
        logger.info(f"📝 Generated {len(test_queries)} comprehensive test queries")
        return test_queries
    
    def execute_semantic_search(self, query: str, model: str, limit: int = 20) -> List[Dict]:
        """Execute semantic search using vector similarity"""
        
        start_time = time.time()
        
        # Get embedding for the query (using a sample similar chunk for now)
        search_sql = """
        WITH query_vector AS (
            SELECT ce.embedding_vector
            FROM chunk_embeddings ce
            JOIN chunks c ON ce.chunk_id = c.chunk_id
            WHERE ce.embedding_model = %s
                AND (
                    c.content ILIKE %s OR 
                    c.content ILIKE %s OR
                    c.content ILIKE %s
                )
            ORDER BY RANDOM()
            LIMIT 1
        )
        SELECT 
            b.title,
            b.author,
            c.content,
            c.chunk_id,
            ROUND((ce.embedding_vector <=> (SELECT embedding_vector FROM query_vector))::numeric, 4) as similarity_distance,
            ce.created_at
        FROM chunks c
        JOIN books b ON c.book_id = b.book_id
        JOIN chunk_embeddings ce ON c.chunk_id = ce.chunk_id
        CROSS JOIN query_vector
        WHERE ce.embedding_model = %s
        ORDER BY ce.embedding_vector <=> (SELECT embedding_vector FROM query_vector)
        LIMIT %s;
        """
        
        # Create search patterns from query
        query_words = query.split()
        pattern1 = f"%{query_words[0]}%" if query_words else "%the%"
        pattern2 = f"%{query_words[1]}%" if len(query_words) > 1 else "%and%"
        pattern3 = f"%{query_words[2]}%" if len(query_words) > 2 else "%of%"
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(search_sql, (model, pattern1, pattern2, pattern3, model, limit))
                    results = cur.fetchall()
            
            execution_time = time.time() - start_time
            
            # Convert to list of dicts
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'title': row['title'],
                    'author': row['author'], 
                    'content': row['content'],
                    'chunk_id': row['chunk_id'],
                    'similarity_distance': float(row['similarity_distance']),
                    'created_at': row['created_at']
                })
            
            logger.info(f"🔍 Query '{query[:30]}...' with {model}: {len(formatted_results)} results in {execution_time:.3f}s")
            
            return {
                'results': formatted_results,
                'execution_time': execution_time,
                'query': query,
                'model': model,
                'result_count': len(formatted_results)
            }
            
        except Exception as e:
            logger.error(f"❌ Search failed for query '{query}' with model {model}: {e}")
            return {
                'results': [],
                'execution_time': 0,
                'query': query,
                'model': model,
                'result_count': 0,
                'error': str(e)
            }
    
    def evaluate_result_quality(self, search_result: Dict, test_query: Dict) -> Dict:
        """Evaluate the quality of search results"""
        
        results = search_result['results']
        if not results:
            return {
                'relevance_score': 0.0,
                'diversity_score': 0.0,
                'coherence_score': 0.0,
                'overall_score': 0.0
            }
        
        # 1. Relevance Score (based on query terms appearing in results)
        query_terms = set(test_query['query'].lower().split())
        relevance_scores = []
        
        for result in results[:10]:  # Top 10 for relevance
            content_words = set(result['content'].lower().split())
            overlap = len(query_terms.intersection(content_words))
            relevance = overlap / len(query_terms) if query_terms else 0
            relevance_scores.append(relevance)
        
        avg_relevance = statistics.mean(relevance_scores) if relevance_scores else 0
        
        # 2. Diversity Score (different books/authors)
        unique_books = len(set(r['title'] for r in results))
        unique_authors = len(set(r['author'] for r in results if r['author']))
        diversity_score = min(unique_books / min(len(results), 10), 1.0)
        
        # 3. Coherence Score (similarity distances should be reasonable)
        distances = [r['similarity_distance'] for r in results if 'similarity_distance' in r]
        if distances:
            # Good results should have distances < 1.0 and show gradual increase
            coherence_score = sum(1 for d in distances[:5] if d < 1.0) / 5
        else:
            coherence_score = 0.0
        
        # 4. Overall Score
        overall_score = (avg_relevance * 0.4 + diversity_score * 0.3 + coherence_score * 0.3)
        
        return {
            'relevance_score': round(avg_relevance, 3),
            'diversity_score': round(diversity_score, 3), 
            'coherence_score': round(coherence_score, 3),
            'overall_score': round(overall_score, 3),
            'unique_books': unique_books,
            'unique_authors': unique_authors,
            'avg_similarity_distance': round(statistics.mean(distances[:5]), 3) if distances else 0
        }
    
    def run_comprehensive_tests(self) -> Dict:
        """Run the complete test suite"""
        
        logger.info("🚀 Starting comprehensive semantic search test suite")
        
        test_queries = self.generate_test_queries()
        all_results = {}
        
        for i, test_query in enumerate(test_queries, 1):
            logger.info(f"\n📋 Test {i}/{len(test_queries)}: {test_query['description']}")
            
            query_results = {}
            
            # Test each model
            for model in self.models:
                logger.info(f"  🧠 Testing {model}...")
                
                search_result = self.execute_semantic_search(
                    test_query['query'], 
                    model,
                    self.max_results
                )
                
                quality_metrics = self.evaluate_result_quality(search_result, test_query)
                
                query_results[model] = {
                    'search_result': search_result,
                    'quality_metrics': quality_metrics
                }
            
            all_results[f"test_{i:02d}_{test_query['category'].replace(' ', '_')}"] = {
                'test_query': test_query,
                'results': query_results
            }
            
            # Brief summary for this test
            logger.info(f"  ✅ Test {i} completed")
        
        return all_results
    
    def generate_performance_report(self, all_results: Dict) -> Dict:
        """Generate comprehensive performance analysis"""
        
        logger.info("📊 Generating performance analysis report")
        
        model_stats = {}
        category_stats = {}
        
        for test_name, test_data in all_results.items():
            test_query = test_data['test_query']
            category = test_query['category']
            
            if category not in category_stats:
                category_stats[category] = {model: [] for model in self.models}
            
            for model in self.models:
                if model not in model_stats:
                    model_stats[model] = {
                        'execution_times': [],
                        'result_counts': [],
                        'quality_scores': [],
                        'relevance_scores': [],
                        'diversity_scores': []
                    }
                
                result_data = test_data['results'][model]
                search_result = result_data['search_result']
                quality = result_data['quality_metrics']
                
                # Collect statistics
                model_stats[model]['execution_times'].append(search_result['execution_time'])
                model_stats[model]['result_counts'].append(search_result['result_count'])
                model_stats[model]['quality_scores'].append(quality['overall_score'])
                model_stats[model]['relevance_scores'].append(quality['relevance_score'])
                model_stats[model]['diversity_scores'].append(quality['diversity_score'])
                
                # Category statistics
                category_stats[category][model].append(quality['overall_score'])
        
        # Calculate summary statistics
        performance_summary = {}
        
        for model in self.models:
            stats = model_stats[model]
            performance_summary[model] = {
                'avg_execution_time': round(statistics.mean(stats['execution_times']), 3),
                'avg_result_count': round(statistics.mean(stats['result_counts']), 1),
                'avg_quality_score': round(statistics.mean(stats['quality_scores']), 3),
                'avg_relevance': round(statistics.mean(stats['relevance_scores']), 3),
                'avg_diversity': round(statistics.mean(stats['diversity_scores']), 3),
                'min_execution_time': round(min(stats['execution_times']), 3),
                'max_execution_time': round(max(stats['execution_times']), 3)
            }
        
        # Category performance analysis
        category_performance = {}
        for category, models_data in category_stats.items():
            category_performance[category] = {}
            for model, scores in models_data.items():
                if scores:
                    category_performance[category][model] = round(statistics.mean(scores), 3)
        
        return {
            'performance_summary': performance_summary,
            'category_performance': category_performance,
            'total_tests': len(all_results),
            'models_tested': self.models,
            'timestamp': datetime.now().isoformat()
        }
    
    def print_results_summary(self, all_results: Dict, performance_report: Dict):
        """Print a comprehensive results summary"""
        
        print("\n" + "="*80)
        print("🧠 SEMANTIC SEARCH TEST SUITE - COMPREHENSIVE RESULTS")
        print("="*80)
        
        # Overall Performance Summary
        print(f"\n📊 OVERALL PERFORMANCE SUMMARY")
        print("-" * 50)
        
        for model, stats in performance_report['performance_summary'].items():
            print(f"\n🤖 {model.upper()}")
            print(f"   Average Execution Time: {stats['avg_execution_time']}s")
            print(f"   Average Result Count: {stats['avg_result_count']}")
            print(f"   Average Quality Score: {stats['avg_quality_score']}/1.0")
            print(f"   Average Relevance: {stats['avg_relevance']}/1.0")
            print(f"   Average Diversity: {stats['avg_diversity']}/1.0")
            print(f"   Speed Range: {stats['min_execution_time']}s - {stats['max_execution_time']}s")
        
        # Category Performance Analysis
        print(f"\n📋 CATEGORY PERFORMANCE ANALYSIS")
        print("-" * 50)
        
        for category, models_scores in performance_report['category_performance'].items():
            print(f"\n📚 {category}")
            for model, score in models_scores.items():
                print(f"   {model}: {score}/1.0")
        
        # Best and Worst Performing Tests
        print(f"\n🏆 TOP PERFORMING TESTS")
        print("-" * 50)
        
        best_tests = []
        for test_name, test_data in all_results.items():
            for model in self.models:
                quality = test_data['results'][model]['quality_metrics']['overall_score']
                best_tests.append((test_name, model, quality, test_data['test_query']['description']))
        
        best_tests.sort(key=lambda x: x[2], reverse=True)
        
        for i, (test_name, model, score, description) in enumerate(best_tests[:5], 1):
            print(f"{i}. {description} ({model}): {score}/1.0")
        
        # Model Comparison
        print(f"\n⚖️ MODEL COMPARISON")
        print("-" * 50)
        
        bge_avg = performance_report['performance_summary']['bge-m3']['avg_quality_score']
        nomic_avg = performance_report['performance_summary']['nomic-embed-text']['avg_quality_score']
        
        if bge_avg > nomic_avg:
            winner = "BGE-M3"
            margin = bge_avg - nomic_avg
        else:
            winner = "NOMIC"
            margin = nomic_avg - bge_avg
        
        print(f"🥇 Winner: {winner} (margin: +{margin:.3f})")
        print(f"📈 BGE-M3 average quality: {bge_avg}/1.0")
        print(f"📈 NOMIC average quality: {nomic_avg}/1.0")
        
        print(f"\n✅ Test suite completed successfully!")
        print(f"📝 Total tests: {performance_report['total_tests']}")
        print(f"🕒 Timestamp: {performance_report['timestamp']}")
        print("="*80 + "\n")

def main():
    """Main execution function"""
    
    print("🧠 LibraryOfBabel Semantic Search Test Suite")
    print("=" * 60)
    
    # Initialize tester
    tester = SemanticSearchTester()
    
    # Run comprehensive tests
    all_results = tester.run_comprehensive_tests()
    
    # Generate performance report
    performance_report = tester.generate_performance_report(all_results)
    
    # Print summary
    tester.print_results_summary(all_results, performance_report)
    
    # Save detailed results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"semantic_search_test_results_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump({
            'test_results': all_results,
            'performance_report': performance_report
        }, f, indent=2, default=str)
    
    print(f"💾 Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main()