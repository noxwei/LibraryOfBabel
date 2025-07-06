#!/usr/bin/env python3
"""
🎓 QA LIBRARIAN PhD - Book Reconstruction Validation Agent 🎓
Advanced quality assurance for the Cyberpunk Data Fixer

This agent validates book reconstruction accuracy by:
1. Comparing reconstructed content against original sources
2. Measuring chapter continuity and structure preservation
3. Detecting overlap removal effectiveness
4. Scoring overall reconstruction quality
"""

import requests
import json
import random
import re
from typing import Dict, List, Any, Tuple
from datetime import datetime
import psycopg2
import os
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class ValidationResult:
    """Results from book reconstruction validation"""
    book_id: int
    title: str
    author: str
    format_type: str
    accuracy_score: float
    structure_score: float
    overlap_score: float
    overall_score: float
    issues: List[str]
    recommendations: List[str]

class QALibrarianPhD:
    """PhD-level quality assurance agent for book reconstruction"""
    
    def __init__(self, api_base_url: str = "http://localhost:8888"):
        self.api_base_url = api_base_url
        self.db_config = {
            'host': 'localhost',
            'database': 'knowledge_base',
            'user': os.getenv('USER'),
            'port': 5432
        }
        self.validation_history = []
        
    def get_connection(self):
        """Connect to the knowledge base"""
        return psycopg2.connect(**self.db_config)
    
    def select_test_sample(self, sample_size: int = 10) -> List[Dict[str, Any]]:
        """
        📚 Select representative sample of books for testing
        
        Strategy:
        - Mix of different genres/authors
        - Various book lengths
        - Different chapter structures
        """
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # Get diverse sample with metadata
            sample_sql = """
            SELECT 
                b.book_id,
                b.title,
                b.author,
                b.word_count,
                COUNT(DISTINCT c.chapter_number) as chapter_count,
                COUNT(c.chunk_id) as chunk_count
            FROM books b
            JOIN chunks c ON b.book_id = c.book_id
            WHERE b.word_count > 1000  -- Exclude very short books
            GROUP BY b.book_id, b.title, b.author, b.word_count
            HAVING COUNT(c.chunk_id) > 5  -- Ensure enough chunks for testing
            ORDER BY RANDOM()
            LIMIT %s
            """
            
            cur.execute(sample_sql, (sample_size,))
            results = cur.fetchall()
            
            sample_books = []
            for book_id, title, author, word_count, chapter_count, chunk_count in results:
                sample_books.append({
                    'book_id': book_id,
                    'title': title,
                    'author': author,
                    'word_count': word_count,
                    'chapter_count': chapter_count,
                    'chunk_count': chunk_count
                })
            
            conn.close()
            return sample_books
            
        except Exception as e:
            print(f"❌ Error selecting test sample: {e}")
            return []
    
    def get_original_chunks(self, book_id: int) -> List[Dict[str, Any]]:
        """Get original chunks from database for comparison"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
            SELECT 
                chunk_id, chunk_type, chapter_number, section_number, 
                content, word_count, character_count
            FROM chunks 
            WHERE book_id = %s
            ORDER BY 
                COALESCE(chapter_number, 0),
                COALESCE(section_number, 0),
                chunk_id
            """, (book_id,))
            
            results = cur.fetchall()
            chunks = []
            
            for chunk_id, chunk_type, chapter_num, section_num, content, word_count, char_count in results:
                chunks.append({
                    'chunk_id': chunk_id,
                    'chunk_type': chunk_type,
                    'chapter_number': chapter_num,
                    'section_number': section_num,
                    'content': content,
                    'word_count': word_count,
                    'character_count': char_count
                })
            
            conn.close()
            return chunks
            
        except Exception as e:
            print(f"❌ Error getting original chunks: {e}")
            return []
    
    def get_reconstructed_book(self, book_identifier: str, format_type: str = "full") -> Dict[str, Any]:
        """Get reconstructed book from API"""
        try:
            response = requests.get(
                f"{self.api_base_url}/api/build",
                params={'book': book_identifier, 'format': format_type},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            return {"error": f"API request failed: {e}"}
    
    def measure_overlap_effectiveness(self, original_chunks: List[Dict], reconstructed_content: str) -> Tuple[float, List[str]]:
        """
        🔍 Measure how well overlap removal worked
        
        Checks:
        - Duplicate sentences/paragraphs
        - Unnatural breaks in flow
        - Missing content at boundaries
        """
        issues = []
        
        # Check for duplicate sentences (indicates poor overlap removal)
        sentences = re.split(r'[.!?]+', reconstructed_content)
        sentence_counts = defaultdict(int)
        
        for sentence in sentences:
            cleaned = sentence.strip()
            if len(cleaned) > 20:  # Ignore very short sentences
                sentence_counts[cleaned] += 1
        
        duplicates = {s: count for s, count in sentence_counts.items() if count > 1}
        duplicate_ratio = len(duplicates) / len(sentence_counts) if sentence_counts else 0
        
        if duplicate_ratio > 0.05:  # More than 5% duplicates is concerning
            issues.append(f"High duplicate sentence ratio: {duplicate_ratio:.1%}")
        
        # Check for unnatural chapter breaks
        chapter_breaks = reconstructed_content.count('CHAPTER')
        expected_chapters = len(set(chunk['chapter_number'] for chunk in original_chunks 
                                 if chunk['chapter_number'] is not None))
        
        if abs(chapter_breaks - expected_chapters) > 1:
            issues.append(f"Chapter count mismatch: expected {expected_chapters}, got {chapter_breaks}")
        
        # Score: 1.0 = perfect, 0.0 = completely broken
        overlap_score = max(0.0, 1.0 - duplicate_ratio * 5)  # Penalize duplicates heavily
        
        return overlap_score, issues
    
    def measure_structure_preservation(self, original_chunks: List[Dict], reconstructed_content: str) -> Tuple[float, List[str]]:
        """
        📐 Measure how well book structure was preserved
        
        Checks:
        - Chapter boundaries
        - Content flow
        - Logical ordering
        """
        issues = []
        
        # Check chapter structure
        original_chapters = sorted(set(chunk['chapter_number'] for chunk in original_chunks 
                                     if chunk['chapter_number'] is not None))
        
        reconstructed_chapters = []
        for match in re.finditer(r'CHAPTER (\d+)', reconstructed_content):
            reconstructed_chapters.append(int(match.group(1)))
        
        # Check for missing chapters
        missing_chapters = set(original_chapters) - set(reconstructed_chapters)
        extra_chapters = set(reconstructed_chapters) - set(original_chapters)
        
        if missing_chapters:
            issues.append(f"Missing chapters: {sorted(missing_chapters)}")
        if extra_chapters:
            issues.append(f"Extra chapters: {sorted(extra_chapters)}")
        
        # Check content ordering by sampling key phrases
        content_flow_score = self._check_content_flow(original_chunks, reconstructed_content)
        
        # Calculate structure score
        chapter_accuracy = 1.0 - (len(missing_chapters) + len(extra_chapters)) / max(len(original_chapters), 1)
        structure_score = (chapter_accuracy + content_flow_score) / 2
        
        return max(0.0, structure_score), issues
    
    def _check_content_flow(self, original_chunks: List[Dict], reconstructed_content: str) -> float:
        """Check if content flows in logical order"""
        # Sample key phrases from original chunks
        sample_phrases = []
        for i, chunk in enumerate(original_chunks[:20]):  # Sample first 20 chunks
            # Extract meaningful phrases (10-30 words)
            words = chunk['content'].split()
            if len(words) >= 20:
                phrase_start = len(words) // 4
                phrase = ' '.join(words[phrase_start:phrase_start+15])
                sample_phrases.append((i, phrase))
        
        # Check if phrases appear in correct order in reconstructed content
        phrase_positions = []
        for order, phrase in sample_phrases:
            pos = reconstructed_content.find(phrase)
            if pos != -1:
                phrase_positions.append((order, pos))
        
        if len(phrase_positions) < 2:
            return 0.5  # Not enough data to judge
        
        # Check if positions are generally increasing
        correct_order = 0
        for i in range(len(phrase_positions) - 1):
            if phrase_positions[i][1] < phrase_positions[i+1][1]:
                correct_order += 1
        
        return correct_order / (len(phrase_positions) - 1) if len(phrase_positions) > 1 else 0.5
    
    def measure_content_accuracy(self, original_chunks: List[Dict], reconstructed_content: str) -> Tuple[float, List[str]]:
        """
        📊 Measure content accuracy and completeness
        
        Checks:
        - Word count preservation
        - Key content inclusion
        - Text corruption
        """
        issues = []
        
        # Calculate word counts
        original_word_count = sum(chunk['word_count'] or 0 for chunk in original_chunks)
        reconstructed_word_count = len(reconstructed_content.split())
        
        word_count_ratio = reconstructed_word_count / original_word_count if original_word_count > 0 else 0
        
        # Acceptable range: 80-120% of original (accounting for overlap removal and formatting)
        if word_count_ratio < 0.8:
            issues.append(f"Significant content loss: {word_count_ratio:.1%} of original word count")
        elif word_count_ratio > 1.2:
            issues.append(f"Content inflation: {word_count_ratio:.1%} of original word count")
        
        # Check for text corruption markers
        corruption_markers = [
            'â€™', 'â€œ', 'â€', 'Ã¡', 'Ã©', 'Ã­', 'Ã³', 'Ãº',  # Common encoding issues
            '????', '###', '***ERROR***', 'MISSING'
        ]
        
        corruption_count = sum(reconstructed_content.count(marker) for marker in corruption_markers)
        if corruption_count > 0:
            issues.append(f"Text corruption detected: {corruption_count} instances")
        
        # Content accuracy score
        accuracy_score = min(1.0, word_count_ratio) if word_count_ratio < 1.0 else min(1.0, 2.0 - word_count_ratio)
        accuracy_score = max(0.0, accuracy_score - corruption_count * 0.01)  # Penalize corruption
        
        return accuracy_score, issues
    
    def validate_book_reconstruction(self, book_info: Dict[str, Any], format_type: str = "full") -> ValidationResult:
        """
        🔬 Comprehensive validation of book reconstruction
        
        Returns detailed ValidationResult with scores and recommendations
        """
        book_id = book_info['book_id']
        title = book_info['title']
        author = book_info['author']
        
        print(f"\n📖 Validating: {title} by {author}")
        print("=" * 60)
        
        # Get original chunks
        original_chunks = self.get_original_chunks(book_id)
        if not original_chunks:
            return ValidationResult(
                book_id=book_id, title=title, author=author, format_type=format_type,
                accuracy_score=0.0, structure_score=0.0, overlap_score=0.0, overall_score=0.0,
                issues=["Could not retrieve original chunks"], recommendations=["Check database connectivity"]
            )
        
        # Get reconstructed book
        reconstructed = self.get_reconstructed_book(str(book_id), format_type)
        if 'error' in reconstructed:
            return ValidationResult(
                book_id=book_id, title=title, author=author, format_type=format_type,
                accuracy_score=0.0, structure_score=0.0, overlap_score=0.0, overall_score=0.0,
                issues=[reconstructed['error']], recommendations=["Check API connectivity"]
            )
        
        reconstructed_content = reconstructed.get('content', '')
        
        # Run validation tests
        print("🔍 Testing content accuracy...")
        accuracy_score, accuracy_issues = self.measure_content_accuracy(original_chunks, reconstructed_content)
        
        print("📐 Testing structure preservation...")
        structure_score, structure_issues = self.measure_structure_preservation(original_chunks, reconstructed_content)
        
        print("🧹 Testing overlap removal...")
        overlap_score, overlap_issues = self.measure_overlap_effectiveness(original_chunks, reconstructed_content)
        
        # Compile results
        all_issues = accuracy_issues + structure_issues + overlap_issues
        
        # Calculate overall score (weighted average)
        overall_score = (accuracy_score * 0.5 + structure_score * 0.3 + overlap_score * 0.2)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(accuracy_score, structure_score, overlap_score, all_issues)
        
        result = ValidationResult(
            book_id=book_id,
            title=title,
            author=author,
            format_type=format_type,
            accuracy_score=accuracy_score,
            structure_score=structure_score,
            overlap_score=overlap_score,
            overall_score=overall_score,
            issues=all_issues,
            recommendations=recommendations
        )
        
        self.validation_history.append(result)
        return result
    
    def _generate_recommendations(self, accuracy_score: float, structure_score: float, 
                                overlap_score: float, issues: List[str]) -> List[str]:
        """Generate specific recommendations based on validation results"""
        recommendations = []
        
        if accuracy_score < 0.7:
            recommendations.append("🔧 Improve content preservation algorithm")
            recommendations.append("📊 Review chunking strategy for better coverage")
        
        if structure_score < 0.7:
            recommendations.append("📐 Enhance chapter boundary detection")
            recommendations.append("🔄 Improve content ordering logic")
        
        if overlap_score < 0.7:
            recommendations.append("🧹 Refine overlap removal algorithm")
            recommendations.append("🔍 Implement better duplicate detection")
        
        if len(issues) > 5:
            recommendations.append("⚠️ Multiple issues detected - comprehensive review needed")
        
        if not recommendations:
            recommendations.append("✅ Excellent reconstruction quality - no changes needed")
        
        return recommendations
    
    def run_validation_suite(self, sample_size: int = 10) -> Dict[str, Any]:
        """
        🧪 Run comprehensive validation suite on sample books
        
        Returns aggregate statistics and detailed results
        """
        print("🎓 QA LIBRARIAN PhD - VALIDATION SUITE")
        print("=" * 50)
        
        # Select test sample
        print(f"📚 Selecting {sample_size} books for validation...")
        sample_books = self.select_test_sample(sample_size)
        
        if not sample_books:
            return {"error": "Could not select test sample"}
        
        print(f"✅ Selected {len(sample_books)} books for testing")
        
        # Validate each book
        results = []
        for book_info in sample_books:
            try:
                result = self.validate_book_reconstruction(book_info)
                results.append(result)
                
                # Print summary
                print(f"📊 Overall Score: {result.overall_score:.1%}")
                print(f"   • Accuracy: {result.accuracy_score:.1%}")
                print(f"   • Structure: {result.structure_score:.1%}")
                print(f"   • Overlap: {result.overlap_score:.1%}")
                if result.issues:
                    print(f"   • Issues: {len(result.issues)}")
                print()
                
            except Exception as e:
                print(f"❌ Error validating {book_info['title']}: {e}")
                continue
        
        # Calculate aggregate statistics
        if results:
            avg_accuracy = sum(r.accuracy_score for r in results) / len(results)
            avg_structure = sum(r.structure_score for r in results) / len(results)
            avg_overlap = sum(r.overlap_score for r in results) / len(results)
            avg_overall = sum(r.overall_score for r in results) / len(results)
            
            # Grade the system
            grade = self._calculate_grade(avg_overall)
            
            summary = {
                "validation_timestamp": datetime.now().isoformat(),
                "books_tested": len(results),
                "average_scores": {
                    "accuracy": avg_accuracy,
                    "structure": avg_structure,
                    "overlap": avg_overlap,
                    "overall": avg_overall
                },
                "grade": grade,
                "quality_assessment": self._assess_quality(avg_overall),
                "detailed_results": [
                    {
                        "title": r.title,
                        "author": r.author,
                        "overall_score": r.overall_score,
                        "issues_count": len(r.issues),
                        "top_recommendation": r.recommendations[0] if r.recommendations else "No issues"
                    }
                    for r in results
                ]
            }
            
            return summary
        
        return {"error": "No successful validations completed"}
    
    def _calculate_grade(self, score: float) -> str:
        """Convert score to academic grade"""
        if score >= 0.97: return "A+"
        elif score >= 0.93: return "A"
        elif score >= 0.90: return "A-"
        elif score >= 0.87: return "B+"
        elif score >= 0.83: return "B"
        elif score >= 0.80: return "B-"
        elif score >= 0.77: return "C+"
        elif score >= 0.73: return "C"
        elif score >= 0.70: return "C-"
        elif score >= 0.67: return "D+"
        elif score >= 0.60: return "D"
        else: return "F"
    
    def _assess_quality(self, score: float) -> str:
        """Provide quality assessment"""
        if score >= 0.90:
            return "🏆 Excellent - Production ready"
        elif score >= 0.80:
            return "✅ Good - Minor improvements needed"
        elif score >= 0.70:
            return "⚠️ Acceptable - Significant improvements recommended"
        elif score >= 0.60:
            return "🔧 Poor - Major fixes required"
        else:
            return "❌ Critical - System needs complete overhaul"
    
    def generate_report(self) -> str:
        """Generate comprehensive validation report"""
        if not self.validation_history:
            return "No validation data available. Run validation suite first."
        
        report = "📋 QA LIBRARIAN PhD - VALIDATION REPORT\n"
        report += "=" * 50 + "\n\n"
        
        for result in self.validation_history:
            report += f"📖 {result.title}\n"
            report += f"👤 Author: {result.author}\n"
            report += f"📊 Overall Score: {result.overall_score:.1%}\n"
            report += f"   • Content Accuracy: {result.accuracy_score:.1%}\n"
            report += f"   • Structure Preservation: {result.structure_score:.1%}\n"
            report += f"   • Overlap Removal: {result.overlap_score:.1%}\n"
            
            if result.issues:
                report += f"⚠️ Issues ({len(result.issues)}):\n"
                for issue in result.issues:
                    report += f"   • {issue}\n"
            
            if result.recommendations:
                report += f"💡 Recommendations:\n"
                for rec in result.recommendations:
                    report += f"   • {rec}\n"
            
            report += "\n" + "-" * 30 + "\n\n"
        
        return report

if __name__ == "__main__":
    # Initialize QA Librarian
    qa_librarian = QALibrarianPhD()
    
    print("🎓 QA LIBRARIAN PhD INITIALIZATION")
    print("Advanced Book Reconstruction Validation System")
    print("=" * 50)
    
    # Run validation suite
    results = qa_librarian.run_validation_suite(sample_size=5)
    
    if 'error' not in results:
        print("\n📊 VALIDATION SUMMARY")
        print("=" * 30)
        print(f"Books Tested: {results['books_tested']}")
        print(f"Average Overall Score: {results['average_scores']['overall']:.1%}")
        print(f"System Grade: {results['grade']}")
        print(f"Quality Assessment: {results['quality_assessment']}")
        
        print(f"\n📝 Detailed Report:")
        print(qa_librarian.generate_report())
        
        # Save results
        with open('/Users/weixiangzhang/Local Dev/LibraryOfBabel/validation_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print("💾 Results saved to validation_results.json")
    
    else:
        print(f"❌ Validation failed: {results['error']}")