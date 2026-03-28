#!/usr/bin/env python3
"""
Multi-Embedding Book Verification System
Tests book quality using BGE-M3, MxBAI, and Nomic embeddings
"""

import psycopg2
import numpy as np
from datetime import datetime
import json
import statistics
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import re
from sklearn.metrics.pairwise import cosine_similarity
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class BookVerificationSystem:
    def __init__(self, conn):
        self.conn = conn
        self.suspicious_books = []
        self.verification_results = defaultdict(dict)

    def run_full_verification(self):
        """Run complete verification pipeline"""
        print("\n" + "="*80)
        print("MULTI-EMBEDDING BOOK VERIFICATION SYSTEM")
        print("="*80)

        # Phase 1: Database Analytics
        print("\n📊 PHASE 1: Database Analytics")
        print("-"*40)
        phase1_results = self.phase1_database_analytics()

        # Phase 2: Content Validation
        print("\n📝 PHASE 2: Content Validation Sampling")
        print("-"*40)
        phase2_results = self.phase2_content_validation(phase1_results['sample_books'])

        # Phase 3: Multi-Embedding Analysis
        print("\n🧠 PHASE 3: Multi-Embedding Anomaly Detection")
        print("-"*40)
        phase3_results = self.phase3_embedding_analysis()

        # Generate Final Report
        print("\n📋 FINAL QUALITY REPORT")
        print("="*80)
        self.generate_final_report(phase1_results, phase2_results, phase3_results)

        return {
            'phase1': phase1_results,
            'phase2': phase2_results,
            'phase3': phase3_results,
            'suspicious_books': self.suspicious_books
        }

    def phase1_database_analytics(self) -> Dict:
        """Phase 1: Analyze all books for statistical anomalies"""
        cur = self.conn.cursor()

        # Get comprehensive stats for all books
        query = """
        WITH book_stats AS (
            SELECT
                b.book_id,
                b.title,
                b.author,
                b.genre,
                b.language,
                COUNT(DISTINCT c.chunk_id) as chunk_count,
                SUM(c.word_count) as total_words,
                SUM(c.character_count) as total_chars,
                AVG(c.word_count) as avg_chunk_words,
                STDDEV(c.word_count) as stddev_chunk_words,
                MIN(c.word_count) as min_chunk_words,
                MAX(c.word_count) as max_chunk_words,
                CASE WHEN SUM(c.word_count) > 0
                    THEN CAST(SUM(c.character_count) AS FLOAT) / SUM(c.word_count)
                    ELSE 0 END as char_word_ratio
            FROM books b
            LEFT JOIN chunks c ON b.book_id = c.book_id
            GROUP BY b.book_id, b.title, b.author, b.genre, b.language
        ),
        embedding_coverage AS (
            SELECT
                book_id,
                STRING_AGG(DISTINCT embedding_model, ', ') as embedding_models,
                COUNT(DISTINCT embedding_model) as model_count
            FROM chunk_embeddings
            GROUP BY book_id
        )
        SELECT
            bs.*,
            COALESCE(ec.embedding_models, 'none') as embedding_models,
            COALESCE(ec.model_count, 0) as embedding_model_count
        FROM book_stats bs
        LEFT JOIN embedding_coverage ec ON bs.book_id = ec.book_id
        ORDER BY bs.total_words DESC
        """

        cur.execute(query)
        books = cur.fetchall()

        # Analyze results
        results = {
            'total_books': len(books),
            'statistics': {},
            'outliers': [],
            'sample_books': []
        }

        # Calculate statistics
        word_counts = [b[6] for b in books if b[6]]  # total_words
        char_word_ratios = [b[12] for b in books if b[12] > 0]  # char_word_ratio
        chunk_counts = [b[5] for b in books if b[5]]  # chunk_count

        results['statistics'] = {
            'word_count': {
                'mean': statistics.mean(word_counts),
                'median': statistics.median(word_counts),
                'stdev': statistics.stdev(word_counts),
                'q1': np.percentile(word_counts, 25),
                'q3': np.percentile(word_counts, 75)
            },
            'char_word_ratio': {
                'mean': statistics.mean(char_word_ratios),
                'median': statistics.median(char_word_ratios),
                'normal_range': (4.5, 6.5)  # English typically 5-6
            },
            'chunk_count': {
                'mean': statistics.mean(chunk_counts),
                'median': statistics.median(chunk_counts)
            }
        }

        # Identify outliers
        for book in books:
            book_id, title = book[0], book[1]
            total_words = book[6] or 0
            char_word_ratio = book[12]
            chunk_count = book[5] or 0

            outlier_reasons = []

            # Check for anomalies
            if char_word_ratio and (char_word_ratio < 4.0 or char_word_ratio > 8.0):
                outlier_reasons.append(f"Unusual char/word ratio: {char_word_ratio:.2f}")

            if chunk_count > 0 and total_words / chunk_count < 50:
                outlier_reasons.append(f"Very small chunks: {total_words/chunk_count:.1f} words/chunk")

            if chunk_count > 0 and total_words / chunk_count > 2000:
                outlier_reasons.append(f"Very large chunks: {total_words/chunk_count:.1f} words/chunk")

            if outlier_reasons:
                results['outliers'].append({
                    'book_id': book_id,
                    'title': title[:80],
                    'reasons': outlier_reasons
                })
                self.suspicious_books.append(book_id)

        # Select stratified sample for Phase 2
        # Sample across different sizes and embedding coverages
        sample_size = min(250, len(books))
        sample_indices = np.random.choice(len(books), sample_size, replace=False)
        results['sample_books'] = [books[i] for i in sample_indices]

        # Print summary
        print(f"✅ Analyzed {len(books)} books")
        print(f"📊 Mean word count: {results['statistics']['word_count']['mean']:,.0f}")
        print(f"📊 Mean char/word ratio: {results['statistics']['char_word_ratio']['mean']:.2f}")
        print(f"⚠️  Found {len(results['outliers'])} statistical outliers")

        cur.close()
        return results

    def phase2_content_validation(self, sample_books: List) -> Dict:
        """Phase 2: Validate content quality of sampled books"""
        cur = self.conn.cursor()
        results = {
            'books_analyzed': len(sample_books),
            'content_issues': [],
            'encoding_issues': [],
            'structure_issues': []
        }

        for book in sample_books[:50]:  # Detailed check on first 50
            book_id = book[0]
            title = book[1][:80]

            # Get sample chunks (first, middle, last)
            cur.execute("""
                WITH ordered_chunks AS (
                    SELECT
                        chunk_id,
                        content,
                        ROW_NUMBER() OVER (ORDER BY chunk_id) as rn,
                        COUNT(*) OVER () as total
                    FROM chunks
                    WHERE book_id = %s
                )
                SELECT chunk_id, content
                FROM ordered_chunks
                WHERE rn = 1
                   OR rn = total
                   OR rn = CAST(total/2 AS INTEGER)
                LIMIT 3
            """, (book_id,))

            chunks = cur.fetchall()

            if not chunks:
                results['structure_issues'].append({
                    'book_id': book_id,
                    'title': title,
                    'issue': 'No chunks found'
                })
                continue

            # Check each chunk for issues
            for chunk_id, content in chunks:
                if not content:
                    results['content_issues'].append({
                        'book_id': book_id,
                        'title': title,
                        'issue': 'Empty chunk content'
                    })
                    continue

                # Check for encoding issues (mojibake)
                if self._has_encoding_issues(content):
                    results['encoding_issues'].append({
                        'book_id': book_id,
                        'title': title,
                        'issue': 'Possible encoding corruption'
                    })

                # Check for repetitive content
                if self._is_repetitive(content):
                    results['content_issues'].append({
                        'book_id': book_id,
                        'title': title,
                        'issue': 'Repetitive content detected'
                    })

                # Check for non-book content patterns
                if self._is_non_book_content(content):
                    results['content_issues'].append({
                        'book_id': book_id,
                        'title': title,
                        'issue': 'Possible non-book content (code/data)'
                    })

        # Print summary
        print(f"✅ Analyzed {results['books_analyzed']} sample books")
        print(f"⚠️  Content issues: {len(results['content_issues'])}")
        print(f"⚠️  Encoding issues: {len(results['encoding_issues'])}")
        print(f"⚠️  Structure issues: {len(results['structure_issues'])}")

        cur.close()
        return results

    def phase3_embedding_analysis(self) -> Dict:
        """Phase 3: Multi-embedding anomaly detection"""
        cur = self.conn.cursor()

        # Get books with multiple embeddings
        cur.execute("""
            SELECT
                book_id,
                COUNT(DISTINCT embedding_model) as model_count,
                STRING_AGG(DISTINCT embedding_model, ', ') as models
            FROM chunk_embeddings
            GROUP BY book_id
            HAVING COUNT(DISTINCT embedding_model) >= 2
            LIMIT 100
        """)

        multi_embed_books = cur.fetchall()

        results = {
            'books_analyzed': len(multi_embed_books),
            'cross_validation_issues': [],
            'embedding_outliers': [],
            'coherence_scores': {}
        }

        print(f"🔍 Analyzing {len(multi_embed_books)} books with multiple embeddings...")

        for book_id, model_count, models in multi_embed_books[:20]:  # Detailed analysis on first 20
            # Get embeddings for each model
            embeddings_by_model = {}

            for model in ['bge-m3', 'mxbai-embed-large', 'nomic-embed-text']:
                if model in models:
                    cur.execute("""
                        SELECT
                            CASE
                                WHEN %s = 'bge-m3' THEN embedding_vector_bge
                                WHEN %s = 'mxbai-embed-large' THEN embedding_vector_mxbai
                                ELSE embedding_vector
                            END as embedding
                        FROM chunk_embeddings
                        WHERE book_id = %s
                        AND embedding_model = %s
                        AND CASE
                                WHEN %s = 'bge-m3' THEN embedding_vector_bge
                                WHEN %s = 'mxbai-embed-large' THEN embedding_vector_mxbai
                                ELSE embedding_vector
                            END IS NOT NULL
                        LIMIT 10
                    """, (model, model, book_id, model, model, model))

                    embeddings = cur.fetchall()
                    if embeddings:
                        # Convert to numpy arrays
                        embeddings_by_model[model] = [
                            np.fromstring(str(e[0]).strip('[]'), sep=',')
                            for e in embeddings if e[0]
                        ]

            # Calculate coherence for each model
            coherence_scores = {}
            for model, embeddings in embeddings_by_model.items():
                if len(embeddings) >= 2:
                    coherence = self._calculate_coherence(embeddings)
                    coherence_scores[model] = coherence

            results['coherence_scores'][book_id] = coherence_scores

            # Cross-model validation
            if len(embeddings_by_model) >= 2:
                models_list = list(embeddings_by_model.keys())
                for i in range(len(models_list)-1):
                    for j in range(i+1, len(models_list)):
                        model1, model2 = models_list[i], models_list[j]

                        # Check if embeddings disagree significantly
                        disagreement = self._check_embedding_disagreement(
                            embeddings_by_model[model1],
                            embeddings_by_model[model2]
                        )

                        if disagreement > 0.3:  # Threshold for significant disagreement
                            results['cross_validation_issues'].append({
                                'book_id': book_id,
                                'models': f"{model1} vs {model2}",
                                'disagreement_score': disagreement
                            })

            # Check for outliers in each embedding space
            for model, embeddings in embeddings_by_model.items():
                if len(embeddings) >= 5:
                    is_outlier = self._detect_outlier(embeddings)
                    if is_outlier:
                        results['embedding_outliers'].append({
                            'book_id': book_id,
                            'model': model,
                            'outlier_score': is_outlier
                        })

        # Print summary
        print(f"✅ Cross-validated {results['books_analyzed']} books")
        print(f"⚠️  Cross-validation issues: {len(results['cross_validation_issues'])}")
        print(f"⚠️  Embedding outliers: {len(results['embedding_outliers'])}")

        cur.close()
        return results

    def _has_encoding_issues(self, text: str) -> bool:
        """Check for encoding/mojibake issues"""
        # Common mojibake patterns
        mojibake_patterns = [
            r'Ã¢â‚¬â„¢',  # Smart quotes
            r'â€™',       # Apostrophe
            r'Â©',        # Copyright
            r'ï¿½',       # Replacement character
            r'Ã‚Â',       # Double encoding
        ]

        for pattern in mojibake_patterns:
            if re.search(pattern, text):
                return True

        # Check for high proportion of non-ASCII in supposedly English text
        non_ascii = len([c for c in text if ord(c) > 127])
        if non_ascii > len(text) * 0.1:  # More than 10% non-ASCII
            return True

        return False

    def _is_repetitive(self, text: str) -> bool:
        """Check if content is repetitive"""
        lines = text.split('\n')
        if len(lines) < 5:
            return False

        # Check for repeated lines
        unique_lines = set(lines)
        if len(unique_lines) < len(lines) * 0.5:  # Less than 50% unique
            return True

        # Check for repeated phrases
        words = text.split()
        if len(words) > 20:
            # Check for 5-word phrases repeated
            phrases = [' '.join(words[i:i+5]) for i in range(len(words)-4)]
            unique_phrases = set(phrases)
            if len(unique_phrases) < len(phrases) * 0.7:
                return True

        return False

    def _is_non_book_content(self, text: str) -> bool:
        """Detect non-book content like code, logs, data"""
        # Code indicators
        code_patterns = [
            r'^\s*import\s+\w+',  # Python imports
            r'^\s*function\s+\w+\(',  # JavaScript functions
            r'^\s*def\s+\w+\(',  # Python functions
            r'^\s*class\s+\w+[:\(]',  # Class definitions
            r'^\s*#include\s*<',  # C includes
            r'{\s*"[\w]+"\s*:\s*',  # JSON
            r'<\?xml',  # XML
            r'<!DOCTYPE',  # HTML
        ]

        lines = text.split('\n')
        code_line_count = 0

        for line in lines[:20]:  # Check first 20 lines
            for pattern in code_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    code_line_count += 1
                    break

        # If more than 30% of lines look like code
        if code_line_count > len(lines[:20]) * 0.3:
            return True

        # Check for data table patterns (CSV, TSV)
        if len(lines) > 5:
            # Count lines with multiple tabs or commas
            delimited_lines = sum(1 for line in lines if line.count('\t') > 2 or line.count(',') > 3)
            if delimited_lines > len(lines) * 0.5:
                return True

        return False

    def _calculate_coherence(self, embeddings: List[np.ndarray]) -> float:
        """Calculate semantic coherence of embeddings"""
        if len(embeddings) < 2:
            return 0.0

        try:
            # Calculate pairwise cosine similarities
            embeddings_matrix = np.vstack([e.flatten()[:768] for e in embeddings[:10]])  # Limit dimensions
            similarities = cosine_similarity(embeddings_matrix)

            # Get mean similarity (excluding diagonal)
            np.fill_diagonal(similarities, 0)
            mean_similarity = similarities.sum() / (len(embeddings) * (len(embeddings) - 1))

            return float(mean_similarity)
        except (ValueError, ZeroDivisionError):
            return 0.0

    def _check_embedding_disagreement(self, embed1: List[np.ndarray], embed2: List[np.ndarray]) -> float:
        """Check disagreement between two embedding sets"""
        if not embed1 or not embed2:
            return 0.0

        try:
            # Compare coherence scores
            coherence1 = self._calculate_coherence(embed1)
            coherence2 = self._calculate_coherence(embed2)

            if coherence1 > 0 and coherence2 > 0:
                disagreement = abs(coherence1 - coherence2) / max(coherence1, coherence2)
                return disagreement
        except (ValueError, ZeroDivisionError):
            pass

        return 0.0

    def _detect_outlier(self, embeddings: List[np.ndarray]) -> Optional[float]:
        """Detect if embeddings are outliers"""
        if len(embeddings) < 5:
            return None

        try:
            # Calculate average embedding
            embeddings_matrix = np.vstack([e.flatten()[:768] for e in embeddings])
            mean_embedding = np.mean(embeddings_matrix, axis=0)

            # Calculate distances from mean
            distances = [
                np.linalg.norm(e.flatten()[:768] - mean_embedding)
                for e in embeddings
            ]

            # Use z-score to detect outliers
            z_scores = stats.zscore(distances)
            max_z = max(abs(z_scores))

            if max_z > 3:  # 3 standard deviations
                return float(max_z)
        except (ValueError, TypeError):
            pass

        return None

    def generate_final_report(self, phase1: Dict, phase2: Dict, phase3: Dict):
        """Generate comprehensive final report"""

        total_issues = (
            len(phase1['outliers']) +
            len(phase2['content_issues']) +
            len(phase2['encoding_issues']) +
            len(phase3['cross_validation_issues']) +
            len(phase3['embedding_outliers'])
        )

        print(f"\n📊 VERIFICATION SUMMARY")
        print(f"Total books analyzed: {phase1['total_books']}")
        print(f"Total issues found: {total_issues}")

        print(f"\n🔍 BREAKDOWN BY ISSUE TYPE:")
        print(f"  Statistical outliers: {len(phase1['outliers'])}")
        print(f"  Content issues: {len(phase2['content_issues'])}")
        print(f"  Encoding issues: {len(phase2['encoding_issues'])}")
        print(f"  Embedding disagreements: {len(phase3['cross_validation_issues'])}")
        print(f"  Embedding outliers: {len(phase3['embedding_outliers'])}")

        # Calculate quality score
        quality_score = max(0, 100 - (total_issues / phase1['total_books'] * 100))

        print(f"\n🎯 OVERALL QUALITY SCORE: {quality_score:.1f}%")

        if quality_score >= 95:
            print("✅ EXCELLENT: Library quality is very high!")
        elif quality_score >= 90:
            print("👍 GOOD: Library quality is good with minor issues")
        elif quality_score >= 80:
            print("⚠️ FAIR: Library has some quality issues to address")
        else:
            print("❌ POOR: Library has significant quality issues")

        # Show top suspicious books
        if self.suspicious_books:
            print(f"\n📚 TOP SUSPICIOUS BOOKS (IDs):")
            for book_id in self.suspicious_books[:10]:
                print(f"  - Book ID: {book_id}")


def main():
    """Main execution"""
    print("Connecting to database...")
    conn = psycopg2.connect(
        dbname="knowledge_base",
        user="weixiangzhang",
        host="localhost"
    )

    try:
        verifier = BookVerificationSystem(conn)
        results = verifier.run_full_verification()

        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"book_verification_results_{timestamp}.json"

        # Convert numpy arrays to lists for JSON serialization
        def convert_to_serializable(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.float32) or isinstance(obj, np.float64):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            return obj

        serializable_results = convert_to_serializable(results)

        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)

        print(f"\n💾 Detailed results saved to: {filename}")

    finally:
        conn.close()

    print("\n" + "="*80)
    print("Verification complete!")


if __name__ == "__main__":
    # Check dependencies
    try:
        from sklearn.metrics.pairwise import cosine_similarity
        from scipy import stats
    except ImportError:
        print("Installing required dependencies...")
        import subprocess
        subprocess.run(["pip3", "install", "scikit-learn", "scipy", "numpy"])
        print("Dependencies installed. Please run the script again.")
        exit(0)

    main()