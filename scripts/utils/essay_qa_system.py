#!/usr/bin/env python3
"""
Essay Quality Assurance System
Comprehensive testing and validation for LibraryOfBabel essay generation
"""

import json
import time
import requests
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re
import statistics
import os
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    word_count: int
    paragraph_count: int
    sentence_count: int
    avg_sentence_length: float
    vocabulary_diversity: float
    citation_integration: int
    coherence_score: float
    depth_indicators: int
    error_count: int
    overall_score: float

@dataclass
class TestResult:
    test_name: str
    status: str  # 'pass', 'fail', 'warning'
    details: str
    metrics: Optional[Dict] = None

class EssayQASystem:
    def __init__(self):
        self.api_base = "http://localhost:5571"
        self.db_config = {
            'host': 'localhost',
            'database': 'knowledge_base',
            'user': 'weixiangzhang',
            'port': 5432
        }
        
        # Quality thresholds
        self.quality_thresholds = {
            'min_word_count': 2500,
            'max_word_count': 6000,
            'min_paragraph_count': 8,
            'min_sentence_avg_length': 15,
            'min_vocabulary_diversity': 0.4,
            'min_citation_integration': 3,
            'min_coherence_score': 0.6,
            'min_depth_indicators': 5,
            'max_error_count': 3
        }
        
        # Test scenarios (including successful essay validation)
        self.test_scenarios = [
            {
                'name': 'Cognitive_Capture_Replication',
                'topic': 'How digital libraries became attention predators',
                'style': 'journalistic',
                'search_query': 'power knowledge library digital algorithm',
                'expected_authors': ['Foucault', 'Bloch', 'Sussman'],
                'expected_concepts': ['attention', 'algorithm', 'library', 'power', 'control', 'digital'],
                'reference_essay': '/Users/weixiangzhang/Local Dev/LibraryOfBabel/essays/the_cognitive_capture_machine.md',
                'min_quality_score': 0.80
            },
            {
                'name': 'Philosophy Synthesis',
                'topic': 'The epistemological foundations of digital knowledge systems',
                'style': 'academic',
                'search_query': 'knowledge power truth foucault',
                'expected_authors': ['Foucault', 'Barthes'],
                'expected_concepts': ['epistemology', 'power', 'knowledge', 'discourse']
            },
            {
                'name': 'Cross-Domain Analysis',
                'topic': 'Libraries as spaces of cognitive control',
                'style': 'journalistic',
                'search_query': 'library babel infinite knowledge',
                'expected_authors': ['Bloch', 'Borges'],
                'expected_concepts': ['library', 'information', 'control', 'access']
            },
            {
                'name': 'Contemporary Critique',
                'topic': 'Algorithmic recommendation as intellectual capture',
                'style': 'analytical',
                'search_query': 'algorithm recommendation attention',
                'expected_concepts': ['algorithm', 'attention', 'control', 'digital']
            }
        ]
    
    def test_api_health(self) -> TestResult:
        """Test API health and connectivity"""
        try:
            response = requests.get(f"{self.api_base}/api/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                
                # Check critical components
                issues = []
                if health_data.get('database') != 'connected':
                    issues.append(f"Database: {health_data.get('database')}")
                if health_data.get('ollama') != 'connected':
                    issues.append(f"Ollama: {health_data.get('ollama')}")
                
                if issues:
                    return TestResult(
                        test_name="API Health Check",
                        status="fail",
                        details=f"Issues found: {', '.join(issues)}",
                        metrics=health_data
                    )
                else:
                    return TestResult(
                        test_name="API Health Check",
                        status="pass",
                        details=f"All systems operational. Model: {health_data.get('model')}",
                        metrics=health_data
                    )
            else:
                return TestResult(
                    test_name="API Health Check",
                    status="fail",
                    details=f"API returned status {response.status_code}"
                )
        except Exception as e:
            return TestResult(
                test_name="API Health Check",
                status="fail",
                details=f"Connection error: {str(e)}"
            )
    
    def test_database_integrity(self) -> TestResult:
        """Test database content and integrity"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Check chunk count
            cursor.execute("SELECT COUNT(*) FROM chunks")
            chunk_count = cursor.fetchone()[0]
            
            # Check book count
            cursor.execute("SELECT COUNT(*) FROM books")
            book_count = cursor.fetchone()[0]
            
            # Check for key authors
            cursor.execute("SELECT DISTINCT author FROM books ORDER BY author")
            authors = [row[0] for row in cursor.fetchall()]
            
            # Check search functionality
            cursor.execute("""
                SELECT COUNT(*) FROM chunks 
                WHERE search_vector @@ plainto_tsquery('english', 'knowledge power')
            """)
            search_results = cursor.fetchone()[0]
            
            conn.close()
            
            issues = []
            if chunk_count < 1000:
                issues.append(f"Low chunk count: {chunk_count}")
            if book_count < 20:
                issues.append(f"Low book count: {book_count}")
            if search_results < 10:
                issues.append(f"Poor search results: {search_results}")
            
            status = "fail" if issues else "pass"
            details = f"Chunks: {chunk_count}, Books: {book_count}, Authors: {len(authors)}"
            if issues:
                details += f". Issues: {', '.join(issues)}"
            
            return TestResult(
                test_name="Database Integrity",
                status=status,
                details=details,
                metrics={
                    'chunk_count': chunk_count,
                    'book_count': book_count,
                    'author_count': len(authors),
                    'search_results': search_results
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="Database Integrity",
                status="fail",
                details=f"Database error: {str(e)}"
            )
    
    def generate_test_essay(self, scenario: Dict) -> Tuple[str, Dict]:
        """Generate essay for testing"""
        try:
            # Start generation
            generation_data = {
                'topic': scenario['topic'],
                'style': scenario['style'],
                'search_query': scenario.get('search_query', '')
            }
            
            response = requests.post(f"{self.api_base}/api/generate", 
                                   json=generation_data, timeout=30)
            
            if response.status_code != 200:
                return None, {'error': f"Generation failed: {response.status_code}"}
            
            essay_id = response.json()['essay_id']
            
            # Poll for completion
            max_wait = 1200  # 20 minutes max
            wait_time = 0
            poll_interval = 10
            
            while wait_time < max_wait:
                status_response = requests.get(f"{self.api_base}/api/status/{essay_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    
                    if status_data['status'] == 'completed':
                        return status_data['essay'], status_data
                    elif status_data['status'] == 'error':
                        return None, status_data
                
                time.sleep(poll_interval)
                wait_time += poll_interval
                logger.info(f"Waiting for essay generation... ({wait_time}s)")
            
            return None, {'error': 'Generation timeout'}
            
        except Exception as e:
            return None, {'error': str(e)}
    
    def analyze_essay_quality(self, essay_text: str, metadata: Dict) -> QualityMetrics:
        """Comprehensive essay quality analysis"""
        
        # Basic metrics
        words = essay_text.split()
        word_count = len(words)
        
        # Paragraph analysis
        paragraphs = [p.strip() for p in essay_text.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)
        
        # Sentence analysis
        sentences = re.split(r'[.!?]+', essay_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)
        avg_sentence_length = statistics.mean([len(s.split()) for s in sentences]) if sentences else 0
        
        # Vocabulary diversity (unique words / total words)
        unique_words = set(word.lower().strip('.,!?";:()[]') for word in words)
        vocabulary_diversity = len(unique_words) / word_count if word_count > 0 else 0
        
        # Citation integration (mentions of sources)
        sources = metadata.get('sources', [])
        citation_integration = 0
        if sources:
            for source in sources:
                author_name = source.get('author', '').split()[-1] if source.get('author') else ''
                if author_name and author_name.lower() in essay_text.lower():
                    citation_integration += 1
        
        # Coherence indicators
        coherence_indicators = [
            'however', 'therefore', 'furthermore', 'moreover', 'consequently',
            'in contrast', 'similarly', 'additionally', 'meanwhile', 'thus',
            'nevertheless', 'hence', 'accordingly', 'likewise'
        ]
        coherence_score = sum(1 for indicator in coherence_indicators 
                            if indicator in essay_text.lower()) / len(coherence_indicators)
        
        # Depth indicators
        depth_indicators = [
            'analysis', 'framework', 'theoretical', 'conceptual', 'methodology',
            'implications', 'demonstrates', 'reveals', 'suggests', 'indicates',
            'examination', 'investigation', 'perspective', 'interpretation'
        ]
        depth_count = sum(1 for indicator in depth_indicators 
                         if indicator in essay_text.lower())
        
        # Error detection (basic)
        error_patterns = [
            r'\b[A-Z]{2,}\b',  # All caps words (potential errors)
            r'\s{2,}',         # Multiple spaces
            r'[.]{2,}',        # Multiple periods
            r'[?]{2,}',        # Multiple question marks
        ]
        error_count = sum(len(re.findall(pattern, essay_text)) for pattern in error_patterns)
        
        # Overall score calculation
        scores = []
        
        # Word count score (0-1)
        if word_count >= self.quality_thresholds['min_word_count']:
            word_score = min(1.0, word_count / 4000)  # Optimal around 4000 words
        else:
            word_score = word_count / self.quality_thresholds['min_word_count']
        scores.append(word_score)
        
        # Structure score
        structure_score = min(1.0, paragraph_count / self.quality_thresholds['min_paragraph_count'])
        scores.append(structure_score)
        
        # Language quality score
        lang_score = min(1.0, vocabulary_diversity / self.quality_thresholds['min_vocabulary_diversity'])
        scores.append(lang_score)
        
        # Content integration score
        content_score = min(1.0, citation_integration / self.quality_thresholds['min_citation_integration'])
        scores.append(content_score)
        
        # Coherence and depth
        scores.append(min(1.0, coherence_score / self.quality_thresholds['min_coherence_score']))
        scores.append(min(1.0, depth_count / self.quality_thresholds['min_depth_indicators']))
        
        # Error penalty
        error_penalty = max(0, 1 - (error_count / 10))  # Reduce score for errors
        scores.append(error_penalty)
        
        overall_score = statistics.mean(scores)
        
        return QualityMetrics(
            word_count=word_count,
            paragraph_count=paragraph_count,
            sentence_count=sentence_count,
            avg_sentence_length=avg_sentence_length,
            vocabulary_diversity=vocabulary_diversity,
            citation_integration=citation_integration,
            coherence_score=coherence_score,
            depth_indicators=depth_count,
            error_count=error_count,
            overall_score=overall_score
        )
    
    def evaluate_essay(self, essay_text: str, metadata: Dict, scenario: Dict) -> TestResult:
        """Comprehensive essay evaluation"""
        if not essay_text:
            return TestResult(
                test_name=f"Essay Quality: {scenario['name']}",
                status="fail",
                details="No essay content generated"
            )
        
        metrics = self.analyze_essay_quality(essay_text, metadata)
        
        # Check against thresholds
        issues = []
        warnings = []
        
        if metrics.word_count < self.quality_thresholds['min_word_count']:
            issues.append(f"Word count too low: {metrics.word_count}")
        elif metrics.word_count > self.quality_thresholds['max_word_count']:
            warnings.append(f"Word count high: {metrics.word_count}")
        
        if metrics.paragraph_count < self.quality_thresholds['min_paragraph_count']:
            issues.append(f"Too few paragraphs: {metrics.paragraph_count}")
        
        if metrics.avg_sentence_length < self.quality_thresholds['min_sentence_avg_length']:
            issues.append(f"Sentences too short: {metrics.avg_sentence_length:.1f}")
        
        if metrics.vocabulary_diversity < self.quality_thresholds['min_vocabulary_diversity']:
            issues.append(f"Low vocabulary diversity: {metrics.vocabulary_diversity:.2f}")
        
        if metrics.citation_integration < self.quality_thresholds['min_citation_integration']:
            warnings.append(f"Few source integrations: {metrics.citation_integration}")
        
        if metrics.error_count > self.quality_thresholds['max_error_count']:
            issues.append(f"Too many errors: {metrics.error_count}")
        
        # Check for expected concepts
        missing_concepts = []
        for concept in scenario.get('expected_concepts', []):
            if concept.lower() not in essay_text.lower():
                missing_concepts.append(concept)
        
        if missing_concepts:
            warnings.append(f"Missing concepts: {', '.join(missing_concepts)}")
        
        # Determine status
        if issues:
            status = "fail"
            details = f"Issues: {'; '.join(issues)}"
            if warnings:
                details += f". Warnings: {'; '.join(warnings)}"
        elif warnings:
            status = "warning"
            details = f"Warnings: {'; '.join(warnings)}"
        else:
            status = "pass"
            details = f"Quality score: {metrics.overall_score:.2f}"
        
        details += f". Words: {metrics.word_count}, Paragraphs: {metrics.paragraph_count}"
        
        return TestResult(
            test_name=f"Essay Quality: {scenario['name']}",
            status=status,
            details=details,
            metrics=metrics.__dict__
        )
    
    def run_comprehensive_tests(self) -> Dict:
        """Run complete test suite"""
        print("🔍 LibraryOfBabel Essay QA System")
        print("=" * 50)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'essays_generated': [],
            'summary': {}
        }
        
        # 1. API Health Test
        print("1. Testing API health...")
        health_result = self.test_api_health()
        results['tests'].append(health_result.__dict__)
        print(f"   {health_result.status.upper()}: {health_result.details}")
        
        if health_result.status == 'fail':
            print("❌ API health check failed - aborting tests")
            return results
        
        # 2. Database Integrity Test
        print("\n2. Testing database integrity...")
        db_result = self.test_database_integrity()
        results['tests'].append(db_result.__dict__)
        print(f"   {db_result.status.upper()}: {db_result.details}")
        
        if db_result.status == 'fail':
            print("❌ Database integrity check failed - aborting tests")
            return results
        
        # 3. Essay Generation Tests
        print("\n3. Testing essay generation...")
        for i, scenario in enumerate(self.test_scenarios, 1):
            print(f"\n   3.{i} Generating: {scenario['name']}")
            print(f"       Topic: {scenario['topic']}")
            
            essay_text, metadata = self.generate_test_essay(scenario)
            
            if essay_text:
                print(f"       ✅ Generated {len(essay_text.split())} words")
                
                # Save essay
                essay_filename = f"test_essay_{scenario['name'].lower().replace(' ', '_')}.md"
                essay_path = f"/Users/weixiangzhang/Local Dev/LibraryOfBabel/tests/essays/{essay_filename}"
                os.makedirs(os.path.dirname(essay_path), exist_ok=True)
                
                with open(essay_path, 'w') as f:
                    f.write(f"# {scenario['topic']}\n\n")
                    f.write(f"**Style:** {scenario['style']}\n")
                    f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"**Model:** {metadata.get('model_used', 'Unknown')}\n\n")
                    f.write("---\n\n")
                    f.write(essay_text)
                
                results['essays_generated'].append({
                    'scenario': scenario['name'],
                    'file_path': essay_path,
                    'word_count': len(essay_text.split()),
                    'metadata': metadata
                })
                
                # Evaluate quality
                quality_result = self.evaluate_essay(essay_text, metadata, scenario)
                results['tests'].append(quality_result.__dict__)
                print(f"       {quality_result.status.upper()}: {quality_result.details}")
                
            else:
                error_msg = metadata.get('error', 'Unknown error')
                print(f"       ❌ Generation failed: {error_msg}")
                results['tests'].append({
                    'test_name': f"Essay Generation: {scenario['name']}",
                    'status': 'fail',
                    'details': f"Generation failed: {error_msg}"
                })
        
        # Generate summary
        test_results = [t for t in results['tests'] if 'status' in t]
        passed = len([t for t in test_results if t['status'] == 'pass'])
        warned = len([t for t in test_results if t['status'] == 'warning'])
        failed = len([t for t in test_results if t['status'] == 'fail'])
        
        results['summary'] = {
            'total_tests': len(test_results),
            'passed': passed,
            'warnings': warned,
            'failed': failed,
            'success_rate': passed / len(test_results) if test_results else 0,
            'essays_generated': len(results['essays_generated'])
        }
        
        print(f"\n📊 TEST SUMMARY")
        print(f"   Total tests: {results['summary']['total_tests']}")
        print(f"   Passed: {passed}")
        print(f"   Warnings: {warned}")
        print(f"   Failed: {failed}")
        print(f"   Success rate: {results['summary']['success_rate']:.1%}")
        print(f"   Essays generated: {results['summary']['essays_generated']}")
        
        return results
    
    def save_qa_report(self, results: Dict) -> str:
        """Save comprehensive QA report"""
        report_path = f"/Users/weixiangzhang/Local Dev/LibraryOfBabel/tests/qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        return report_path

def main():
    """Run QA system"""
    qa_system = EssayQASystem()
    results = qa_system.run_comprehensive_tests()
    
    # Save report
    report_path = qa_system.save_qa_report(results)
    print(f"\n📄 QA report saved to: {report_path}")
    
    # Determine if system is ready for commit
    if results['summary']['failed'] == 0:
        if results['summary']['warnings'] == 0:
            print("\n🎉 ALL TESTS PASSED - System ready for commit!")
            return 0
        else:
            print("\n⚠️ Tests passed with warnings - Review before commit")
            return 1
    else:
        print("\n❌ Tests failed - Do not commit until issues resolved")
        return 2

if __name__ == "__main__":
    exit(main())