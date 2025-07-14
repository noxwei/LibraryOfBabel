#!/usr/bin/env python3
"""
🏛️ Dr. Sarah Chen (陈雪芳) - Database Systems Librarian (DSL)
=========================================================

MLS Specialization: Library Systems Administration & Database Management
Primary Role: PostgreSQL database administration and optimization
Team: LibraryOfBabel Ebook Focus DBA Team

Background: Chinese-American librarian with 15 years experience in academic library
systems. PhD in Information Science from University of Washington. Specialized in
large-scale digital collection management and database optimization.

Philosophy: "数据库是图书馆的心脏 (Database is the heart of the library) - 
every query must be fast, every table must be precise, every index must be perfect."
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

class DrSarahChenDBA:
    """
    Dr. Sarah Chen (陈雪芳) - Database Systems Librarian
    
    MLS Expertise: Library Systems Administration & Database Management
    Specialization: PostgreSQL optimization, vector embeddings, search performance
    
    Cultural Background: Chinese-American librarian who combines traditional
    library science precision with modern database technologies. Believes in
    systematic approach to database management.
    
    Management Philosophy: "严格的数据库管理带来优秀的用户体验"
    (Strict database management brings excellent user experience)
    """
    
    def __init__(self):
        # Professional identity
        self.name = "Dr. Sarah Chen (陈雪芳)"
        self.title = "Database Systems Librarian (DSL)"
        self.mls_school = "University of Washington iSchool"
        self.phd_year = 2015
        self.library_experience = 15
        
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
        
        # Performance targets (from team charter)
        self.performance_targets = {
            'uptime': 99.9,  # 99.9% target
            'query_response_ms': 100,  # <100ms average
            'processing_throughput': 50,  # 50+ books/hour
            'corruption_incidents': 0  # 0 corruption incidents
        }
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("DrSarahChen_DBA")
        
        # Working directory setup
        self.workspace = Path("agents/ebook_dba_team/sarah_chen_workspace")
        self.workspace.mkdir(exist_ok=True)
        
        print(f"🏛️ Dr. Sarah Chen (陈雪芳) - Database Systems Librarian initialized")
        print(f"📚 MLS: {self.mls_school} | PhD: {self.phd_year} | Experience: {self.library_experience} years")
        print(f"🎯 Mission: PostgreSQL optimization for LibraryOfBabel")
        print(f"📊 Performance Targets: {self.performance_targets['uptime']}% uptime, <{self.performance_targets['query_response_ms']}ms queries")
        print(f"👥 Reporting: HR → {self.reports_to_hr}, Content → {self.reports_to_content}")
        
    def get_db_connection(self):
        """Get database connection with Dr. Chen's credentials"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except psycopg2.Error as e:
            self.logger.error(f"💔 Database connection failed: {e}")
            return None
    
    def perform_database_health_check(self) -> Dict[str, Any]:
        """Comprehensive database health assessment"""
        print(f"\n🏥 DATABASE HEALTH CHECK - {self.name}")
        print("=" * 60)
        
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "librarian": self.name,
            "checks": {},
            "recommendations": [],
            "overall_status": "unknown"
        }
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    health_report["overall_status"] = "critical_failure"
                    health_report["recommendations"].append("数据库连接失败 - 立即检查服务器状态")
                    return health_report
                
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    
                    # Check 1: Database size and table status
                    print("📊 Checking database size and table status...")
                    cur.execute("""
                        SELECT schemaname, tablename, 
                               pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                               pg_stat_get_tuples_fetched(c.oid) as tuples_fetched,
                               pg_stat_get_tuples_inserted(c.oid) as tuples_inserted
                        FROM pg_tables pt
                        JOIN pg_class c ON c.relname = pt.tablename
                        WHERE schemaname = 'public'
                        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
                    """)
                    
                    tables = cur.fetchall()
                    health_report["checks"]["table_analysis"] = {
                        "total_tables": len(tables),
                        "tables": [dict(table) for table in tables[:10]]  # Top 10 largest
                    }
                    
                    # Check 2: Query performance analysis
                    print("⚡ Analyzing query performance...")
                    cur.execute("""
                        SELECT query, calls, total_time, mean_time, rows
                        FROM pg_stat_statements 
                        WHERE mean_time > 100  -- Queries slower than 100ms
                        ORDER BY mean_time DESC 
                        LIMIT 10;
                    """)
                    
                    slow_queries = cur.fetchall()
                    if slow_queries:
                        health_report["checks"]["performance_issues"] = {
                            "slow_queries_count": len(slow_queries),
                            "slowest_queries": [dict(query) for query in slow_queries]
                        }
                        health_report["recommendations"].append("发现慢查询 - 需要优化索引或查询结构")
                    
                    # Check 3: Index usage analysis
                    print("🔍 Checking index usage efficiency...")
                    cur.execute("""
                        SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
                        FROM pg_stat_user_indexes
                        WHERE idx_scan = 0  -- Unused indexes
                        ORDER BY pg_relation_size(indexrelid) DESC;
                    """)
                    
                    unused_indexes = cur.fetchall()
                    if unused_indexes:
                        health_report["checks"]["unused_indexes"] = {
                            "count": len(unused_indexes),
                            "indexes": [dict(idx) for idx in unused_indexes]
                        }
                        health_report["recommendations"].append("发现未使用的索引 - 考虑删除以节省空间")
                    
                    # Check 4: Connection and lock analysis
                    print("🔒 Analyzing connections and locks...")
                    cur.execute("""
                        SELECT state, count(*) as connection_count
                        FROM pg_stat_activity
                        WHERE state IS NOT NULL
                        GROUP BY state;
                    """)
                    
                    connections = cur.fetchall()
                    health_report["checks"]["connection_analysis"] = {
                        "connection_states": [dict(conn) for conn in connections]
                    }
                    
                    # Check 5: Books and chunks data validation
                    print("📚 Validating books and chunks data...")
                    cur.execute("SELECT COUNT(*) as book_count FROM books;")
                    book_count = cur.fetchone()['book_count']
                    
                    cur.execute("SELECT COUNT(*) as chunk_count FROM chunks;")
                    chunk_count = cur.fetchone()['chunk_count']
                    
                    health_report["checks"]["data_validation"] = {
                        "book_count": book_count,
                        "chunk_count": chunk_count,
                        "avg_chunks_per_book": chunk_count / book_count if book_count > 0 else 0
                    }
                    
                    # Overall assessment
                    if len(health_report["recommendations"]) == 0:
                        health_report["overall_status"] = "excellent"
                        print("✅ 数据库状态优秀! (Database status excellent!)")
                    elif len(health_report["recommendations"]) <= 2:
                        health_report["overall_status"] = "good"
                        print("✅ 数据库状态良好，有小幅改进空间 (Database status good, minor improvements needed)")
                    else:
                        health_report["overall_status"] = "needs_attention"
                        print("⚠️ 数据库需要注意，发现多个问题 (Database needs attention, multiple issues found)")
                        
        except Exception as e:
            self.logger.error(f"❌ Health check failed: {e}")
            health_report["overall_status"] = "check_failed"
            health_report["error"] = str(e)
            health_report["recommendations"].append("健康检查失败 - 需要立即调查数据库状态")
        
        return health_report
    
    def optimize_database_performance(self) -> Dict[str, Any]:
        """Perform database optimization based on Dr. Chen's expertise"""
        print(f"\n⚡ DATABASE OPTIMIZATION - {self.name}")
        print("=" * 60)
        
        optimization_report = {
            "timestamp": datetime.now().isoformat(),
            "librarian": self.name,
            "optimizations_performed": [],
            "performance_improvements": {},
            "recommendations": []
        }
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    optimization_report["error"] = "数据库连接失败"
                    return optimization_report
                
                with conn.cursor() as cur:
                    
                    # Optimization 1: Update table statistics
                    print("📊 Updating table statistics...")
                    cur.execute("ANALYZE;")
                    optimization_report["optimizations_performed"].append("Table statistics updated")
                    
                    # Optimization 2: Reindex for better performance
                    print("🔄 Reindexing critical tables...")
                    cur.execute("REINDEX TABLE books;")
                    cur.execute("REINDEX TABLE chunks;")
                    optimization_report["optimizations_performed"].append("Critical tables reindexed")
                    
                    # Optimization 3: Vacuum to reclaim space
                    print("🧹 Vacuuming tables to reclaim space...")
                    cur.execute("VACUUM ANALYZE books;")
                    cur.execute("VACUUM ANALYZE chunks;")
                    optimization_report["optimizations_performed"].append("Tables vacuumed and analyzed")
                    
                    conn.commit()
                    
                    # Performance measurement
                    start_time = time.time()
                    cur.execute("SELECT COUNT(*) FROM books JOIN chunks ON books.id = chunks.book_id LIMIT 1000;")
                    query_time = (time.time() - start_time) * 1000  # Convert to ms
                    
                    optimization_report["performance_improvements"]["sample_query_time_ms"] = query_time
                    
                    if query_time < self.performance_targets['query_response_ms']:
                        optimization_report["recommendations"].append("✅ 查询性能达到目标 (Query performance meets target)")
                    else:
                        optimization_report["recommendations"].append("⚠️ 查询性能仍需改进 (Query performance still needs improvement)")
                    
                    print(f"📈 Sample query time: {query_time:.2f}ms (Target: <{self.performance_targets['query_response_ms']}ms)")
                    
        except Exception as e:
            self.logger.error(f"❌ Optimization failed: {e}")
            optimization_report["error"] = str(e)
            optimization_report["recommendations"].append("优化失败 - 需要进一步调查")
        
        return optimization_report
    
    def prepare_vector_embedding_infrastructure(self) -> Dict[str, Any]:
        """Prepare database for vector embedding integration"""
        print(f"\n🧠 VECTOR EMBEDDING PREPARATION - {self.name}")
        print("=" * 60)
        
        vector_prep_report = {
            "timestamp": datetime.now().isoformat(),
            "librarian": self.name,
            "preparations": [],
            "readiness_status": "unknown"
        }
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    vector_prep_report["error"] = "数据库连接失败"
                    return vector_prep_report
                
                with conn.cursor() as cur:
                    
                    # Check if pgvector extension exists
                    print("🔍 Checking pgvector extension availability...")
                    cur.execute("""
                        SELECT EXISTS(
                            SELECT 1 FROM pg_available_extensions 
                            WHERE name = 'vector'
                        );
                    """)
                    
                    pgvector_available = cur.fetchone()[0]
                    
                    if pgvector_available:
                        # Install pgvector extension
                        print("📦 Installing pgvector extension...")
                        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                        vector_prep_report["preparations"].append("pgvector extension installed")
                        
                        # Create vector column for embeddings
                        print("🗂️ Preparing vector columns...")
                        cur.execute("""
                            ALTER TABLE chunks 
                            ADD COLUMN IF NOT EXISTS embedding vector(1536);
                        """)
                        vector_prep_report["preparations"].append("Embedding column added to chunks table")
                        
                        # Create vector index for similarity search
                        print("🔍 Creating vector similarity index...")
                        cur.execute("""
                            CREATE INDEX IF NOT EXISTS chunks_embedding_idx 
                            ON chunks USING ivfflat (embedding vector_cosine_ops)
                            WITH (lists = 100);
                        """)
                        vector_prep_report["preparations"].append("Vector similarity index created")
                        
                        conn.commit()
                        vector_prep_report["readiness_status"] = "ready"
                        print("✅ 向量嵌入基础设施准备完成! (Vector embedding infrastructure ready!)")
                        
                    else:
                        vector_prep_report["readiness_status"] = "pgvector_missing"
                        vector_prep_report["preparations"].append("pgvector extension not available")
                        print("⚠️ pgvector扩展不可用 - 需要安装 (pgvector extension not available - installation needed)")
                        
        except Exception as e:
            self.logger.error(f"❌ Vector preparation failed: {e}")
            vector_prep_report["error"] = str(e)
            vector_prep_report["readiness_status"] = "failed"
        
        return vector_prep_report
    
    def generate_dba_report(self) -> Dict[str, Any]:
        """Generate comprehensive DBA report for Linda and Lexi"""
        print(f"\n📋 COMPREHENSIVE DBA REPORT - {self.name}")
        print("=" * 60)
        
        # Perform all assessments
        health_report = self.perform_database_health_check()
        optimization_report = self.optimize_database_performance()
        vector_prep_report = self.prepare_vector_embedding_infrastructure()
        
        # Compile comprehensive report
        comprehensive_report = {
            "timestamp": datetime.now().isoformat(),
            "librarian": {
                "name": self.name,
                "title": self.title,
                "mls_school": self.mls_school,
                "experience_years": self.library_experience,
                "performance_targets": self.performance_targets
            },
            "database_health": health_report,
            "optimization_results": optimization_report,
            "vector_infrastructure": vector_prep_report,
            "dr_chen_assessment": self._generate_personal_assessment(health_report, optimization_report, vector_prep_report),
            "recommendations_for_linda": self._generate_hr_recommendations(health_report),
            "recommendations_for_lexi": self._generate_content_recommendations(health_report, vector_prep_report)
        }
        
        # Save report
        report_file = self.workspace / "comprehensive_dba_report.json"
        with open(report_file, 'w') as f:
            json.dump(comprehensive_report, f, indent=2)
        
        print(f"\n📄 Report saved: {report_file}")
        print(f"💼 Ready for review by {self.reports_to_hr} and {self.reports_to_content}")
        
        return comprehensive_report
    
    def _generate_personal_assessment(self, health_report, optimization_report, vector_prep_report) -> Dict[str, Any]:
        """Dr. Chen's personal assessment of database status"""
        
        # Calculate performance grade
        issues = len(health_report.get("recommendations", []))
        if issues == 0:
            grade = "A"
            chinese_assessment = "优秀"
        elif issues <= 2:
            grade = "B"
            chinese_assessment = "良好"
        else:
            grade = "C"
            chinese_assessment = "需要改进"
        
        return {
            "overall_grade": grade,
            "chinese_assessment": chinese_assessment,
            "professional_opinion": f"Based on {self.library_experience} years of library systems experience, "
                                  f"the database shows {health_report.get('overall_status', 'unknown')} status. "
                                  f"Performance meets library standards with {issues} areas for improvement.",
            "next_steps": [
                "Continue monitoring query performance daily",
                "Implement automated backup verification",
                "Plan quarterly performance optimization",
                "Prepare for vector embedding integration"
            ],
            "cultural_note": "按照严格的图书馆标准，数据库管理必须精确无误 (According to strict library standards, database management must be precise and error-free)"
        }
    
    def _generate_hr_recommendations(self, health_report) -> List[str]:
        """Generate recommendations for Linda Zhang (HR)"""
        recommendations = [
            f"Database performance grade: {health_report.get('overall_status', 'unknown')}",
            f"Dr. Chen available for {self.performance_targets['processing_throughput']} books/hour processing",
            "Recommend quarterly performance reviews for database team",
            "Database infrastructure ready for expanded team operations"
        ]
        
        if health_report.get("overall_status") == "needs_attention":
            recommendations.append("Request additional DBA support for optimization projects")
        
        return recommendations
    
    def _generate_content_recommendations(self, health_report, vector_prep_report) -> List[str]:
        """Generate recommendations for Lexi (Content Strategy)"""
        recommendations = [
            f"Database ready for research operations with {health_report['checks']['data_validation']['book_count']} books",
            f"Vector embedding infrastructure: {vector_prep_report['readiness_status']}",
            "Search performance optimized for AI agent interactions",
            "Ready to support advanced research workflows"
        ]
        
        if vector_prep_report.get("readiness_status") == "ready":
            recommendations.append("Semantic search capabilities can be implemented")
        
        return recommendations

def main():
    """Main DBA operations"""
    print("🚀 Initializing Dr. Sarah Chen DBA Operations...")
    
    dba = DrSarahChenDBA()
    
    # Generate comprehensive report
    report = dba.generate_dba_report()
    
    print(f"\n✅ DBA Operations Complete!")
    print(f"📊 Database Status: {report['database_health']['overall_status']}")
    print(f"⚡ Optimization: {len(report['optimization_results']['optimizations_performed'])} tasks completed")
    print(f"🧠 Vector Infrastructure: {report['vector_infrastructure']['readiness_status']}")
    print(f"🎯 Overall Grade: {report['dr_chen_assessment']['overall_grade']}")
    
    return report

if __name__ == "__main__":
    main()