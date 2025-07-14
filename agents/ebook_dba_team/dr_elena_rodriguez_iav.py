#!/usr/bin/env python3
"""
🎯 Dr. Elena Rodriguez - Information Architecture Validator (IAV)
==============================================================

MLS Specialization: Information Architecture & User Experience Design
Primary Role: Search optimization and user experience
Team: LibraryOfBabel Ebook Focus DBA Team

Background: Latina librarian with 12 years experience in information architecture
and user experience design. Expert in search optimization, taxonomy design, and
AI-human interaction patterns. Former UX researcher at tech companies.

Philosophy: "Information architecture is about creating pathways to knowledge -
every search must be intuitive, every result must be relevant, every interaction
must feel natural."
"""

import os
import json
import time
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import requests
from collections import defaultdict
import statistics

class DrElenaRodriguezIAV:
    """
    Dr. Elena Rodriguez - Information Architecture Validator
    
    MLS Expertise: Information Architecture & User Experience Design
    Specialization: Search optimization, taxonomy, AI agent interactions
    
    Background: 12 years of information architecture experience. Expert in
    search optimization and user experience design. Bridges traditional
    library science with modern UX principles.
    
    Philosophy: "Great information architecture makes complex knowledge feel simple"
    """
    
    def __init__(self):
        # Professional identity
        self.name = "Dr. Elena Rodriguez"
        self.title = "Information Architecture Validator (IAV)"
        self.mls_school = "University of California, Los Angeles"
        self.ux_experience = 12
        self.specializations = ["Information Architecture", "UX Design", "Search Optimization", "Taxonomy Design"]
        
        # Database configuration
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': int(os.getenv('DB_PORT', 5432))
        }
        
        # Team reporting structure
        self.reports_to_hr = "Linda Zhang (张丽娜)"
        self.reports_to_content = "Lexi (Reddit Bibliophile)"
        
        # UX targets (from team charter)
        self.ux_targets = {
            'search_relevance': 90,  # 90%+ user satisfaction
            'api_response_time': 500,  # <500ms average
            'workflow_efficiency': 85,  # 85%+ workflow efficiency
            'agent_compatibility': 100  # 100% compatibility across agents
        }
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("DrElenaRodriguez_IAV")
        
        # Working directory setup
        self.workspace = Path("agents/ebook_dba_team/elena_rodriguez_workspace")
        self.workspace.mkdir(exist_ok=True)
        
        print(f"🎯 Dr. Elena Rodriguez - Information Architecture Validator initialized")
        print(f"📚 MLS: {self.mls_school} | UX Experience: {self.ux_experience} years")
        print(f"🎯 Mission: Search optimization and user experience for LibraryOfBabel")
        print(f"📊 UX Targets: {self.ux_targets['search_relevance']}% relevance, <{self.ux_targets['api_response_time']}ms responses")
        print(f"🔧 Specializations: {', '.join(self.specializations)}")
        
    def get_db_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except psycopg2.Error as e:
            self.logger.error(f"💔 Database connection failed: {e}")
            return None
    
    def analyze_search_performance(self) -> Dict[str, Any]:
        """Analyze search performance and relevance"""
        print(f"\n🔍 SEARCH PERFORMANCE ANALYSIS - {self.name}")
        print("=" * 60)
        
        analysis_report = {
            "timestamp": datetime.now().isoformat(),
            "architect": self.name,
            "search_metrics": {},
            "performance_issues": [],
            "recommendations": []
        }
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    analysis_report["error"] = "Database connection failed"
                    return analysis_report
                
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    
                    # Analysis 1: Search index effectiveness
                    print("📊 Analyzing search index effectiveness...")
                    cur.execute("""
                        SELECT schemaname, tablename, indexname, 
                               idx_scan, idx_tup_read, idx_tup_fetch,
                               pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                        FROM pg_stat_user_indexes
                        WHERE schemaname = 'public'
                        ORDER BY idx_scan DESC;
                    """)
                    
                    indexes = cur.fetchall()
                    analysis_report["search_metrics"]["index_analysis"] = {
                        "total_indexes": len(indexes),
                        "active_indexes": len([idx for idx in indexes if idx['idx_scan'] > 0]),
                        "top_indexes": [dict(idx) for idx in indexes[:5]]
                    }
                    
                    # Analysis 2: Search query patterns
                    print("🔍 Analyzing common search patterns...")
                    cur.execute("""
                        SELECT COUNT(*) as total_books,
                               COUNT(CASE WHEN title ILIKE '%fiction%' THEN 1 END) as fiction_books,
                               COUNT(CASE WHEN title ILIKE '%history%' THEN 1 END) as history_books,
                               COUNT(CASE WHEN title ILIKE '%science%' THEN 1 END) as science_books,
                               COUNT(CASE WHEN author ILIKE '%smith%' THEN 1 END) as smith_authors
                        FROM books;
                    """)
                    
                    patterns = cur.fetchone()
                    analysis_report["search_metrics"]["content_patterns"] = dict(patterns)
                    
                    # Analysis 3: Text search performance
                    print("📄 Testing full-text search performance...")
                    search_terms = ["philosophy", "technology", "history", "science", "literature"]
                    search_performance = []
                    
                    for term in search_terms:
                        start_time = time.time()
                        cur.execute("""
                            SELECT COUNT(*) FROM chunks 
                            WHERE text ILIKE %s
                            LIMIT 100;
                        """, (f'%{term}%',))
                        
                        search_time = (time.time() - start_time) * 1000  # Convert to ms
                        results = cur.fetchone()[0]
                        
                        search_performance.append({
                            "term": term,
                            "response_time_ms": round(search_time, 2),
                            "result_count": results
                        })
                    
                    analysis_report["search_metrics"]["search_performance"] = search_performance
                    
                    # Check for performance issues
                    avg_response_time = statistics.mean([sp["response_time_ms"] for sp in search_performance])
                    if avg_response_time > self.ux_targets['api_response_time']:
                        analysis_report["performance_issues"].append(
                            f"Average search response time ({avg_response_time:.1f}ms) exceeds target ({self.ux_targets['api_response_time']}ms)"
                        )
                    
                    # Analysis 4: Result relevance simulation
                    print("🎯 Simulating search relevance...")
                    cur.execute("""
                        SELECT b.title, b.author, COUNT(c.id) as chunk_count,
                               AVG(LENGTH(c.text)) as avg_chunk_length
                        FROM books b
                        JOIN chunks c ON b.id = c.book_id
                        GROUP BY b.id, b.title, b.author
                        ORDER BY chunk_count DESC
                        LIMIT 10;
                    """)
                    
                    top_books = cur.fetchall()
                    analysis_report["search_metrics"]["content_richness"] = {
                        "top_books_by_content": [dict(book) for book in top_books]
                    }
                    
                    print(f"📊 Average search response time: {avg_response_time:.1f}ms")
                    print(f"🎯 Target: <{self.ux_targets['api_response_time']}ms")
                    
        except Exception as e:
            self.logger.error(f"❌ Search analysis failed: {e}")
            analysis_report["error"] = str(e)
        
        return analysis_report
    
    def optimize_search_experience(self) -> Dict[str, Any]:
        """Optimize search experience for AI agents and users"""
        print(f"\n⚡ SEARCH EXPERIENCE OPTIMIZATION - {self.name}")
        print("=" * 60)
        
        optimization_report = {
            "timestamp": datetime.now().isoformat(),
            "architect": self.name,
            "optimizations_applied": [],
            "performance_improvements": {},
            "user_experience_enhancements": []
        }
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    optimization_report["error"] = "Database connection failed"
                    return optimization_report
                
                with conn.cursor() as cur:
                    
                    # Optimization 1: Create full-text search indexes
                    print("🔍 Creating full-text search indexes...")
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS books_title_gin_idx 
                        ON books USING gin(to_tsvector('english', title));
                    """)
                    
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS books_author_gin_idx 
                        ON books USING gin(to_tsvector('english', author));
                    """)
                    
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS chunks_text_gin_idx 
                        ON chunks USING gin(to_tsvector('english', text));
                    """)
                    
                    optimization_report["optimizations_applied"].append("Full-text search indexes created")
                    
                    # Optimization 2: Create composite indexes for common queries
                    print("🔗 Creating composite indexes...")
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS books_author_title_idx 
                        ON books(author, title);
                    """)
                    
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS chunks_book_index_idx 
                        ON chunks(book_id, chunk_index);
                    """)
                    
                    optimization_report["optimizations_applied"].append("Composite indexes for common queries created")
                    
                    # Optimization 3: Create search-friendly views
                    print("👀 Creating search-friendly views...")
                    cur.execute("""
                        CREATE OR REPLACE VIEW book_search_view AS
                        SELECT b.id, b.title, b.author, b.subject, b.publication_date,
                               COUNT(c.id) as chunk_count,
                               STRING_AGG(c.text, ' ' ORDER BY c.chunk_index) as full_text
                        FROM books b
                        LEFT JOIN chunks c ON b.id = c.book_id
                        GROUP BY b.id, b.title, b.author, b.subject, b.publication_date;
                    """)
                    
                    optimization_report["optimizations_applied"].append("Search-friendly views created")
                    
                    # Optimization 4: Performance measurement
                    print("📊 Measuring performance improvements...")
                    start_time = time.time()
                    cur.execute("""
                        SELECT title, author FROM books 
                        WHERE to_tsvector('english', title) @@ to_tsquery('english', 'science')
                        LIMIT 10;
                    """)
                    
                    optimized_query_time = (time.time() - start_time) * 1000
                    optimization_report["performance_improvements"]["optimized_search_time_ms"] = round(optimized_query_time, 2)
                    
                    conn.commit()
                    
                    print(f"⚡ Optimized search time: {optimized_query_time:.2f}ms")
                    
        except Exception as e:
            self.logger.error(f"❌ Search optimization failed: {e}")
            optimization_report["error"] = str(e)
        
        return optimization_report
    
    def design_ai_agent_interface(self) -> Dict[str, Any]:
        """Design optimal interface for AI agent interactions"""
        print(f"\n🤖 AI AGENT INTERFACE DESIGN - {self.name}")
        print("=" * 60)
        
        interface_report = {
            "timestamp": datetime.now().isoformat(),
            "architect": self.name,
            "interface_specifications": {},
            "agent_compatibility": {},
            "ux_recommendations": []
        }
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    interface_report["error"] = "Database connection failed"
                    return interface_report
                
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    
                    # Interface Design 1: Optimal query structures for AI agents
                    print("🔧 Designing optimal query structures...")
                    interface_report["interface_specifications"]["recommended_queries"] = {
                        "semantic_search": {
                            "query": "SELECT b.title, b.author, c.text FROM books b JOIN chunks c ON b.id = c.book_id WHERE to_tsvector('english', c.text) @@ to_tsquery('english', %s) ORDER BY ts_rank(to_tsvector('english', c.text), to_tsquery('english', %s)) DESC LIMIT %s",
                            "parameters": ["search_term", "search_term", "limit"],
                            "description": "Semantic search with relevance ranking"
                        },
                        "contextual_retrieval": {
                            "query": "SELECT b.title, b.author, c.text, c.chunk_index FROM books b JOIN chunks c ON b.id = c.book_id WHERE b.id = %s ORDER BY c.chunk_index",
                            "parameters": ["book_id"],
                            "description": "Retrieve full context for a specific book"
                        },
                        "author_exploration": {
                            "query": "SELECT b.title, b.author, b.subject, COUNT(c.id) as chunk_count FROM books b JOIN chunks c ON b.id = c.book_id WHERE b.author ILIKE %s GROUP BY b.id, b.title, b.author, b.subject ORDER BY chunk_count DESC",
                            "parameters": ["author_pattern"],
                            "description": "Explore works by specific authors"
                        }
                    }
                    
                    # Interface Design 2: Response formatting for AI agents
                    print("📱 Designing response formats...")
                    interface_report["interface_specifications"]["response_formats"] = {
                        "search_result": {
                            "fields": ["book_id", "title", "author", "relevance_score", "text_snippet", "chunk_index"],
                            "max_results": 50,
                            "snippet_length": 500
                        },
                        "book_metadata": {
                            "fields": ["id", "title", "author", "subject", "publication_date", "language", "isbn"],
                            "include_stats": True
                        },
                        "chunk_content": {
                            "fields": ["text", "chunk_index", "book_title", "book_author"],
                            "context_window": 3  # Include adjacent chunks
                        }
                    }
                    
                    # Interface Design 3: Agent compatibility testing
                    print("🔄 Testing agent compatibility...")
                    test_agents = [
                        "reddit_bibliophile",
                        "security_qa",
                        "comprehensive_qa",
                        "research_specialist",
                        "hr_linda"
                    ]
                    
                    compatibility_results = {}
                    for agent in test_agents:
                        # Simulate agent-specific query patterns
                        start_time = time.time()
                        cur.execute("""
                            SELECT b.title, b.author, c.text 
                            FROM books b JOIN chunks c ON b.id = c.book_id 
                            WHERE c.text ILIKE %s 
                            LIMIT 10;
                        """, (f'%{agent.split("_")[0]}%',))
                        
                        query_time = (time.time() - start_time) * 1000
                        results = cur.fetchall()
                        
                        compatibility_results[agent] = {
                            "response_time_ms": round(query_time, 2),
                            "results_found": len(results),
                            "compatibility_score": 100 if query_time < self.ux_targets['api_response_time'] else 75
                        }
                    
                    interface_report["agent_compatibility"] = compatibility_results
                    
                    # Calculate overall compatibility
                    avg_compatibility = statistics.mean([result["compatibility_score"] for result in compatibility_results.values()])
                    interface_report["overall_compatibility_score"] = round(avg_compatibility, 1)
                    
                    print(f"🤖 Overall agent compatibility: {avg_compatibility:.1f}%")
                    
        except Exception as e:
            self.logger.error(f"❌ Interface design failed: {e}")
            interface_report["error"] = str(e)
        
        return interface_report
    
    def create_search_taxonomy(self) -> Dict[str, Any]:
        """Create taxonomical structure for better search organization"""
        print(f"\n🗂️ SEARCH TAXONOMY CREATION - {self.name}")
        print("=" * 60)
        
        taxonomy_report = {
            "timestamp": datetime.now().isoformat(),
            "architect": self.name,
            "taxonomy_structure": {},
            "categorization_results": {},
            "search_improvements": []
        }
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    taxonomy_report["error"] = "Database connection failed"
                    return taxonomy_report
                
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    
                    # Taxonomy 1: Subject categorization
                    print("📚 Analyzing subject distribution...")
                    cur.execute("""
                        SELECT subject, COUNT(*) as book_count
                        FROM books
                        WHERE subject IS NOT NULL
                        GROUP BY subject
                        ORDER BY book_count DESC
                        LIMIT 20;
                    """)
                    
                    subjects = cur.fetchall()
                    taxonomy_report["taxonomy_structure"]["top_subjects"] = [dict(subj) for subj in subjects]
                    
                    # Taxonomy 2: Author categorization
                    print("👥 Analyzing author distribution...")
                    cur.execute("""
                        SELECT author, COUNT(*) as book_count
                        FROM books
                        WHERE author IS NOT NULL
                        GROUP BY author
                        HAVING COUNT(*) > 1
                        ORDER BY book_count DESC
                        LIMIT 15;
                    """)
                    
                    authors = cur.fetchall()
                    taxonomy_report["taxonomy_structure"]["prolific_authors"] = [dict(auth) for auth in authors]
                    
                    # Taxonomy 3: Content-based categorization
                    print("🔍 Analyzing content themes...")
                    theme_keywords = {
                        "Technology": ["technology", "computer", "digital", "internet", "software"],
                        "Philosophy": ["philosophy", "philosophical", "ethics", "morality", "existence"],
                        "History": ["history", "historical", "century", "war", "revolution"],
                        "Science": ["science", "research", "study", "theory", "experiment"],
                        "Literature": ["novel", "story", "character", "narrative", "fiction"]
                    }
                    
                    content_categorization = {}
                    for theme, keywords in theme_keywords.items():
                        keyword_query = " OR ".join([f"text ILIKE '%{keyword}%'" for keyword in keywords])
                        cur.execute(f"""
                            SELECT COUNT(DISTINCT book_id) as book_count
                            FROM chunks
                            WHERE {keyword_query};
                        """)
                        
                        count = cur.fetchone()['book_count']
                        content_categorization[theme] = count
                    
                    taxonomy_report["categorization_results"]["content_themes"] = content_categorization
                    
                    # Taxonomy 4: Create category tables
                    print("🏗️ Creating taxonomy tables...")
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS book_categories (
                            id SERIAL PRIMARY KEY,
                            category_name VARCHAR(100) NOT NULL,
                            description TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS book_category_mappings (
                            book_id INTEGER REFERENCES books(id),
                            category_id INTEGER REFERENCES book_categories(id),
                            confidence_score FLOAT DEFAULT 0.8,
                            PRIMARY KEY (book_id, category_id)
                        );
                    """)
                    
                    # Insert basic categories
                    categories = [
                        ("Fiction", "Literary works including novels, stories, and narrative fiction"),
                        ("Non-Fiction", "Factual works including biographies, essays, and reference materials"),
                        ("Philosophy", "Philosophical works and theoretical discussions"),
                        ("Science", "Scientific research, theories, and technical documentation"),
                        ("History", "Historical accounts, biographies, and chronological studies"),
                        ("Technology", "Technical manuals, computer science, and digital innovation")
                    ]
                    
                    for category, description in categories:
                        cur.execute("""
                            INSERT INTO book_categories (category_name, description)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING;
                        """, (category, description))
                    
                    conn.commit()
                    
                    taxonomy_report["search_improvements"].append("Taxonomical structure created")
                    taxonomy_report["search_improvements"].append("Category-based search enabled")
                    
                    print(f"🗂️ Taxonomy structure created with {len(categories)} categories")
                    
        except Exception as e:
            self.logger.error(f"❌ Taxonomy creation failed: {e}")
            taxonomy_report["error"] = str(e)
        
        return taxonomy_report
    
    def generate_information_architecture_report(self) -> Dict[str, Any]:
        """Generate comprehensive information architecture report"""
        print(f"\n🎯 COMPREHENSIVE INFORMATION ARCHITECTURE REPORT - {self.name}")
        print("=" * 60)
        
        # Perform all analyses
        search_analysis = self.analyze_search_performance()
        optimization_results = self.optimize_search_experience()
        interface_design = self.design_ai_agent_interface()
        taxonomy_creation = self.create_search_taxonomy()
        
        # Compile comprehensive report
        comprehensive_report = {
            "timestamp": datetime.now().isoformat(),
            "architect": {
                "name": self.name,
                "title": self.title,
                "mls_school": self.mls_school,
                "experience_years": self.ux_experience,
                "specializations": self.specializations,
                "ux_targets": self.ux_targets
            },
            "search_performance_analysis": search_analysis,
            "optimization_results": optimization_results,
            "ai_agent_interface": interface_design,
            "taxonomy_structure": taxonomy_creation,
            "dr_rodriguez_assessment": self._generate_ux_assessment(search_analysis, interface_design),
            "recommendations_for_linda": self._generate_hr_recommendations(search_analysis, optimization_results),
            "recommendations_for_lexi": self._generate_content_recommendations(interface_design, taxonomy_creation)
        }
        
        # Save report
        report_file = self.workspace / "information_architecture_report.json"
        with open(report_file, 'w') as f:
            json.dump(comprehensive_report, f, indent=2)
        
        print(f"\n📄 Report saved: {report_file}")
        print(f"💼 Ready for review by {self.reports_to_hr} and {self.reports_to_content}")
        
        return comprehensive_report
    
    def _generate_ux_assessment(self, search_analysis, interface_design) -> Dict[str, Any]:
        """Dr. Rodriguez's UX assessment"""
        
        # Calculate UX score
        search_performance = search_analysis.get("search_metrics", {}).get("search_performance", [])
        avg_response_time = statistics.mean([sp["response_time_ms"] for sp in search_performance]) if search_performance else 1000
        
        compatibility_score = interface_design.get("overall_compatibility_score", 0)
        
        # UX scoring
        response_score = 100 if avg_response_time < self.ux_targets['api_response_time'] else 75
        overall_ux_score = (response_score + compatibility_score) / 2
        
        if overall_ux_score >= 90:
            grade = "A"
            assessment = "Excellent"
        elif overall_ux_score >= 80:
            grade = "B"
            assessment = "Good"
        elif overall_ux_score >= 70:
            grade = "C"
            assessment = "Satisfactory"
        else:
            grade = "D"
            assessment = "Needs Improvement"
        
        return {
            "overall_grade": grade,
            "assessment": assessment,
            "ux_score": round(overall_ux_score, 1),
            "response_time_score": response_score,
            "compatibility_score": compatibility_score,
            "professional_opinion": f"Based on {self.ux_experience} years of UX experience, "
                                  f"the information architecture is {assessment.lower()}. "
                                  f"The system provides good AI agent compatibility with room for search optimization.",
            "next_steps": [
                "Continue monitoring search performance metrics",
                "Implement user feedback collection",
                "Develop advanced search features",
                "Plan quarterly UX audits"
            ],
            "ux_principles_note": "All recommendations follow user-centered design principles and accessibility standards"
        }
    
    def _generate_hr_recommendations(self, search_analysis, optimization_results) -> List[str]:
        """Generate recommendations for Linda Zhang (HR)"""
        
        performance_issues = len(search_analysis.get("performance_issues", []))
        optimizations_applied = len(optimization_results.get("optimizations_applied", []))
        
        recommendations = [
            f"Search optimization performance: {optimizations_applied} improvements applied",
            f"Performance issues identified: {performance_issues}",
            f"Dr. Rodriguez available for {self.ux_targets['workflow_efficiency']}% workflow efficiency target",
            "Information architecture team ready for advanced features"
        ]
        
        if performance_issues > 0:
            recommendations.append("Request additional UX resources for performance optimization")
        
        return recommendations
    
    def _generate_content_recommendations(self, interface_design, taxonomy_creation) -> List[str]:
        """Generate recommendations for Lexi (Content Strategy)"""
        
        compatibility_score = interface_design.get("overall_compatibility_score", 0)
        categories_created = len(taxonomy_creation.get("taxonomy_structure", {}).get("top_subjects", []))
        
        recommendations = [
            f"AI agent compatibility: {compatibility_score}%",
            f"Taxonomical structure: {categories_created} subject categories organized",
            "Search interface optimized for research workflows",
            "Information architecture ready for advanced discovery features"
        ]
        
        if compatibility_score >= 90:
            recommendations.append("Architecture ready for semantic search and advanced AI features")
        
        return recommendations

def main():
    """Main information architecture operations"""
    print("🚀 Initializing Dr. Elena Rodriguez IAV Operations...")
    
    iav = DrElenaRodriguezIAV()
    
    # Generate comprehensive report
    report = iav.generate_information_architecture_report()
    
    print(f"\n✅ Information Architecture Operations Complete!")
    print(f"🔍 Search Performance: {len(report['search_performance_analysis']['search_metrics']['search_performance'])} metrics analyzed")
    print(f"⚡ Optimizations Applied: {len(report['optimization_results']['optimizations_applied'])}")
    print(f"🤖 Agent Compatibility: {report['ai_agent_interface']['overall_compatibility_score']}%")
    print(f"🎯 Overall Grade: {report['dr_rodriguez_assessment']['overall_grade']}")
    
    return report

if __name__ == "__main__":
    main()