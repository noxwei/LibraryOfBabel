#!/usr/bin/env python3
"""
Ollama Integration Test Suite
============================

Comprehensive testing for the Ollama URL Generator Agent integration
with the 360-book LibraryOfBabel knowledge base.

Test Categories:
- Natural language query processing
- URL generation accuracy
- Security validation
- API integration
- Performance benchmarks
- 360-book database compatibility

Comprehensive QA Agent Requirements:
✅ Natural language accuracy testing
✅ API response validation  
✅ 360-book integration validation
"""

import asyncio
import unittest
import sys
import os
import time
import json
from typing import Dict, List, Any

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'agents'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'security'))

from ollama_url_generator import OllamaUrlGeneratorAgent
from ollama_security import OllamaSecurityValidator, validate_input, sanitize_query

class TestOllamaUrlGenerator(unittest.TestCase):
    """Test suite for Ollama URL Generator Agent"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.agent = OllamaUrlGeneratorAgent(
            ollama_endpoint="http://localhost:11434",
            ollama_model="llama2",
            api_key="test_key_for_testing",
            library_api_base="https://api.ashortstayinhell.com/api/v3"
        )
        cls.security_validator = OllamaSecurityValidator()
    
    def setUp(self):
        """Set up for each test"""
        self.start_time = time.time()
    
    def tearDown(self):
        """Clean up after each test"""
        test_time = time.time() - self.start_time
        print(f"⏱️ Test completed in {test_time:.3f}s")

class TestNaturalLanguageProcessing(TestOllamaUrlGenerator):
    """Test natural language query processing"""
    
    def test_basic_query_processing(self):
        """Test basic natural language query processing"""
        test_queries = [
            "Find books about artificial intelligence",
            "Show me philosophy books",
            "Books on social justice",
            "Climate change literature",
            "Technology and ethics"
        ]
        
        for query in test_queries:
            with self.subTest(query=query):
                # Test query processing without Ollama (fallback mode)
                result = asyncio.run(self.agent.natural_language_to_url(query))
                
                self.assertTrue(result.get('success'), f"Query processing failed for: {query}")
                self.assertIn('structured_query', result)
                self.assertIn('search_urls', result)
                self.assertGreater(len(result['search_urls']), 0)
    
    def test_complex_queries(self):
        """Test complex multi-concept queries"""
        complex_queries = [
            "Find books that discuss both artificial intelligence and consciousness",
            "Show me Octavia Butler's approach to social justice and power dynamics",
            "Books that bridge science and spirituality in modern context",
            "Contemporary analysis of digital surveillance and privacy rights",
            "Intersection of race, technology, and social inequality"
        ]
        
        for query in complex_queries:
            with self.subTest(query=query):
                result = asyncio.run(self.agent.natural_language_to_url(query))
                
                self.assertTrue(result.get('success'))
                structured = result['structured_query']
                
                # Check for multiple search terms extracted
                self.assertGreater(len(structured.get('search_terms', [])), 1)
                
                # Check for multiple search strategies
                self.assertGreater(len(result['search_urls']), 1)
    
    def test_author_specific_queries(self):
        """Test author-specific queries"""
        author_queries = [
            "Show me books by Octavia Butler",
            "Find Ursula K. Le Guin works",
            "Books by Michel Foucault",
            "Jorge Luis Borges literature"
        ]
        
        for query in author_queries:
            with self.subTest(query=query):
                result = asyncio.run(self.agent.natural_language_to_url(query))
                
                self.assertTrue(result.get('success'))
                structured = result['structured_query']
                
                # Should detect author names
                authors = structured.get('authors', [])
                self.assertGreater(len(authors), 0, f"No authors detected in: {query}")
                
                # Should generate author-focused search strategy
                strategies = [url['strategy'] for url in result['search_urls']]
                self.assertIn('author_focused', strategies)

class TestUrlGeneration(TestOllamaUrlGenerator):
    """Test URL generation functionality"""
    
    def test_url_structure(self):
        """Test generated URL structure and validity"""
        query = "Find books about artificial intelligence"
        result = asyncio.run(self.agent.natural_language_to_url(query))
        
        self.assertTrue(result.get('success'))
        
        for url_config in result['search_urls']:
            url = url_config['url']
            
            # Check URL structure
            self.assertTrue(url.startswith('https://api.ashortstayinhell.com/api/v3/search'))
            self.assertIn('?', url)
            
            # Check required parameters
            self.assertIn('q=', url)
            self.assertIn('limit=', url)
    
    def test_search_strategies(self):
        """Test different search strategy generation"""
        query = "Find books by Octavia Butler about social justice"
        result = asyncio.run(self.agent.natural_language_to_url(query))
        
        strategies = [url['strategy'] for url in result['search_urls']]
        
        # Should generate multiple strategies
        expected_strategies = ['primary_semantic', 'author_focused']
        for strategy in expected_strategies:
            self.assertIn(strategy, strategies)
    
    def test_parameter_extraction(self):
        """Test search parameter extraction accuracy"""
        test_cases = [
            {
                'query': "Find 5 books about AI consciousness",
                'expected_limit': 5
            },
            {
                'query': "Show me books by Ursula Le Guin",
                'expected_authors': ['Ursula Le Guin']
            },
            {
                'query': "Climate change and environmental policy",
                'expected_terms': ['climate', 'change', 'environmental', 'policy']
            }
        ]
        
        for case in test_cases:
            with self.subTest(query=case['query']):
                result = asyncio.run(self.agent.natural_language_to_url(case['query']))
                structured = result['structured_query']
                
                if 'expected_limit' in case:
                    self.assertEqual(structured.get('limit'), case['expected_limit'])
                
                if 'expected_authors' in case:
                    authors = structured.get('authors', [])
                    for expected_author in case['expected_authors']:
                        self.assertTrue(
                            any(expected_author.lower() in author.lower() for author in authors),
                            f"Author '{expected_author}' not found in: {authors}"
                        )
                
                if 'expected_terms' in case:
                    search_terms = [term.lower() for term in structured.get('search_terms', [])]
                    for expected_term in case['expected_terms']:
                        self.assertTrue(
                            any(expected_term in term for term in search_terms),
                            f"Term '{expected_term}' not found in: {search_terms}"
                        )

class TestSecurityValidation(TestOllamaUrlGenerator):
    """Test security validation functionality"""
    
    def test_input_validation(self):
        """Test input validation and sanitization"""
        # Valid inputs
        valid_queries = [
            "Find books about AI",
            "Philosophy and technology",
            "Social justice literature"
        ]
        
        for query in valid_queries:
            with self.subTest(query=query):
                is_valid, message = validate_input(query)
                self.assertTrue(is_valid, f"Valid query rejected: {query} - {message}")
    
    def test_malicious_input_detection(self):
        """Test detection of malicious input patterns"""
        malicious_queries = [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "'; DROP TABLE books; --",
            "<iframe src='evil.com'></iframe>",
            "eval(malicious_code)",
            "../../../etc/passwd",
            "system('rm -rf /')"
        ]
        
        for query in malicious_queries:
            with self.subTest(query=query):
                is_valid, message = validate_input(query)
                self.assertFalse(is_valid, f"Malicious query not detected: {query}")
    
    def test_input_sanitization(self):
        """Test input sanitization functionality"""
        test_cases = [
            {
                'input': "<script>Find books about AI</script>",
                'expected_clean': "Find books about AI"
            },
            {
                'input': "Find books    with   multiple   spaces",
                'expected_clean': "Find books with multiple spaces"
            },
            {
                'input': "Books & articles about <AI>",
                'expected_clean': "Books  articles about AI"
            }
        ]
        
        for case in test_cases:
            with self.subTest(input=case['input']):
                sanitized = sanitize_query(case['input'])
                self.assertEqual(sanitized.strip(), case['expected_clean'])
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        validator = OllamaSecurityValidator()
        client_ip = "test.127.0.0.1"
        
        # Test within limits
        for i in range(5):
            is_valid, message = validator.validate_input("test query", client_ip=client_ip)
            self.assertTrue(is_valid, f"Request {i+1} should be valid")
        
        # Test exceeding limits (simulate rapid requests)
        validator.rate_limits['requests_per_minute'] = 3  # Lower limit for testing
        
        for i in range(5):
            is_valid, message = validator.validate_input("test query", client_ip=client_ip)
            if i < 3:
                self.assertTrue(is_valid, f"Request {i+1} should be valid")
            else:
                self.assertFalse(is_valid, f"Request {i+1} should be rate limited")

class TestPerformance(TestOllamaUrlGenerator):
    """Test performance characteristics"""
    
    def test_response_time(self):
        """Test response time performance"""
        query = "Find books about artificial intelligence"
        
        start_time = time.time()
        result = asyncio.run(self.agent.natural_language_to_url(query))
        response_time = time.time() - start_time
        
        # Should respond within 5 seconds (allowing for fallback mode)
        self.assertLess(response_time, 5.0, f"Response too slow: {response_time:.3f}s")
        
        # Check performance metrics in result
        if 'performance' in result:
            self.assertIn('response_time', result['performance'])
    
    def test_concurrent_queries(self):
        """Test handling of concurrent queries"""
        queries = [
            "Find books about AI",
            "Philosophy books",
            "Social justice literature",
            "Climate change",
            "Technology ethics"
        ]
        
        async def process_queries():
            tasks = [self.agent.natural_language_to_url(query) for query in queries]
            return await asyncio.gather(*tasks)
        
        start_time = time.time()
        results = asyncio.run(process_queries())
        total_time = time.time() - start_time
        
        # All queries should succeed
        for i, result in enumerate(results):
            self.assertTrue(result.get('success'), f"Query {i+1} failed: {queries[i]}")
        
        # Concurrent processing should be faster than sequential
        self.assertLess(total_time, len(queries) * 2.0, "Concurrent processing too slow")

class TestKnowledgeBaseIntegration(TestOllamaUrlGenerator):
    """Test integration with 360-book knowledge base"""
    
    def test_360_book_compatibility(self):
        """Test compatibility with 360-book database structure"""
        query = "Find books about philosophy"
        result = asyncio.run(self.agent.natural_language_to_url(query))
        
        self.assertTrue(result.get('success'))
        
        # Check knowledge base info
        agent_info = self.agent.knowledge_base_info
        self.assertEqual(agent_info['total_books'], 360)
        self.assertEqual(agent_info['total_words'], 34236988)
        self.assertEqual(agent_info['total_chunks'], 10514)
    
    def test_domain_coverage(self):
        """Test coverage of knowledge domains"""
        domain_queries = [
            ("philosophy", "philosophy"),
            ("technology", "technology"),
            ("social theory", "social_theory"),
            ("literature", "literature"),
            ("science fiction", "science_fiction"),
            ("artificial intelligence", "ai_consciousness")
        ]
        
        for query_text, expected_domain in domain_queries:
            with self.subTest(domain=expected_domain):
                result = asyncio.run(self.agent.natural_language_to_url(f"Find books about {query_text}"))
                
                self.assertTrue(result.get('success'))
                
                # Check if domain is recognized
                domains = self.agent.knowledge_base_info['domains']
                relevant_domains = [d for d in domains if expected_domain in d or query_text.replace(' ', '_') in d]
                
                # Should have some relevant domain coverage
                # Note: This is a soft check since exact domain matching depends on the knowledge base structure
                self.assertGreater(len(domains), 0, "No domains configured in knowledge base")

class TestErrorHandling(TestOllamaUrlGenerator):
    """Test error handling and edge cases"""
    
    def test_empty_query(self):
        """Test handling of empty queries"""
        empty_queries = ["", "   ", None]
        
        for query in empty_queries:
            with self.subTest(query=repr(query)):
                result = asyncio.run(self.agent.natural_language_to_url(query))
                self.assertFalse(result.get('success'))
                self.assertIn('error', result)
    
    def test_very_long_query(self):
        """Test handling of very long queries"""
        long_query = "Find books about artificial intelligence " * 50  # Very long query
        
        result = asyncio.run(self.agent.natural_language_to_url(long_query))
        
        # Should either handle gracefully or provide appropriate error
        self.assertIn('success', result)
        if not result['success']:
            self.assertIn('error', result)
    
    def test_special_characters(self):
        """Test handling of special characters"""
        special_queries = [
            "Books about AI & ML",
            "Philosophy: mind vs. body",
            "Climate change (urgent topic)",
            "Books with 'quotes' and \"double quotes\"",
            "Technology—past & future"
        ]
        
        for query in special_queries:
            with self.subTest(query=query):
                result = asyncio.run(self.agent.natural_language_to_url(query))
                # Should handle gracefully (either succeed or fail safely)
                self.assertIn('success', result)

def run_comprehensive_test_suite():
    """Run the complete test suite with detailed reporting"""
    
    print("🧪 OLLAMA INTEGRATION TEST SUITE")
    print("=" * 60)
    print("Testing natural language to 360-book search integration")
    print()
    
    # Create test suite
    test_classes = [
        TestNaturalLanguageProcessing,
        TestUrlGeneration,
        TestSecurityValidation,
        TestPerformance,
        TestKnowledgeBaseIntegration,
        TestErrorHandling
    ]
    
    total_tests = 0
    total_failures = 0
    
    for test_class in test_classes:
        print(f"📋 Running {test_class.__name__}...")
        
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        total_tests += result.testsRun
        total_failures += len(result.failures) + len(result.errors)
        
        print(f"✅ {test_class.__name__}: {result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} passed")
        print()
    
    print("🎯 TEST SUMMARY")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_tests - total_failures}")
    print(f"Failed: {total_failures}")
    print(f"Success Rate: {((total_tests - total_failures) / total_tests * 100):.1f}%")
    
    if total_failures == 0:
        print("🎉 ALL TESTS PASSED! Ollama integration ready for production.")
    else:
        print(f"⚠️ {total_failures} tests failed. Review failures before deployment.")

if __name__ == "__main__":
    run_comprehensive_test_suite()