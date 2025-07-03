#!/usr/bin/env python3
"""
MLA Citation Verifier for LibraryOfBabel Analysis
Verifies MLA citations against the PostgreSQL database to ensure accuracy
"""

import psycopg2
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class MLACitationVerifier:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'database': 'knowledge_base',
            'user': 'weixiangzhang',
            'port': 5432
        }
        
        # Expected MLA citations from the document
        self.expected_citations = [
            {
                'author': 'Bloch, William Goldbloom',
                'title': 'The Unimaginable Mathematics of Borges\' Library of Babel',
                'publisher': 'Oxford University Press',
                'year': '2008'
            },
            {
                'author': 'Foucault, Michel',
                'title': 'Ethics: Subjectivity and Truth: Essential Works of Michel Foucault 1954-1984',
                'publisher': 'Penguin Modern Classics',
                'year': '2019'
            },
            {
                'author': 'Hall, Manly Palmer',
                'title': 'The Secret Teachings of All Ages',
                'publisher': 'Tarcher',
                'year': '2006'
            },
            {
                'author': 'Klein, Naomi',
                'title': 'The Shock Doctrine: The Rise of Disaster Capitalism',
                'publisher': 'Penguin Books Ltd',
                'year': '2014'
            },
            {
                'author': 'Peck, Steven L.',
                'title': 'A Short Stay in Hell',
                'publisher': 'Steven L. Peck',
                'year': '2022'
            },
            {
                'author': 'Sussman, Robert Wald',
                'title': 'The Myth of Race: The Troubling Persistence of an Unscientific Idea',
                'publisher': 'Harvard University Press',
                'year': '2014'
            }
        ]
    
    def get_database_books(self) -> List[Tuple]:
        """Retrieve book information from database"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT author, title, publisher, publication_date, created_at
            FROM books 
            WHERE author IN (
                'Michel Foucault', 'Steven L. Peck', 'William Goldbloom Bloch', 
                'Naomi Klein', 'Manly P. Hall', 'Robert Wald Sussman'
            )
            ORDER BY author
        """)
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def extract_year_from_date(self, date_str: Optional[str]) -> Optional[str]:
        """Extract year from publication date string"""
        if not date_str:
            return None
        
        # Handle different date formats
        try:
            if 'T' in str(date_str):
                # ISO format: 2019-11-13T18:30:00+00:00
                year = str(date_str).split('-')[0]
                return year
            elif '-' in str(date_str):
                # Simple format: 2019-11-13
                year = str(date_str).split('-')[0]
                return year
            else:
                return str(date_str)[:4] if len(str(date_str)) >= 4 else None
        except:
            return None
    
    def normalize_author_name(self, name: str) -> str:
        """Convert author name to Last, First format for MLA"""
        if ',' in name:
            return name  # Already in correct format
        
        parts = name.strip().split()
        if len(parts) >= 2:
            last = parts[-1]
            first_middle = ' '.join(parts[:-1])
            return f"{last}, {first_middle}"
        return name
    
    def verify_citations(self) -> Dict:
        """Verify MLA citations against database"""
        print("🔍 MLA Citation Verification")
        print("=" * 50)
        
        db_books = self.get_database_books()
        verification_results = {
            'verified': [],
            'discrepancies': [],
            'missing': [],
            'summary': {}
        }
        
        print(f"📊 Database contains {len(db_books)} relevant books")
        print(f"📋 MLA citations list contains {len(self.expected_citations)} entries")
        print()
        
        # Check each MLA citation against database
        for i, citation in enumerate(self.expected_citations, 1):
            print(f"🔎 Verifying Citation #{i}:")
            print(f"   Author: {citation['author']}")
            print(f"   Title: {citation['title']}")
            
            # Find matching book in database
            found_match = False
            for db_author, db_title, db_publisher, db_date, db_created in db_books:
                
                # Normalize author names for comparison
                normalized_db_author = self.normalize_author_name(db_author)
                
                # Check for author match (flexible)
                author_match = (
                    citation['author'].lower() in normalized_db_author.lower() or
                    normalized_db_author.lower() in citation['author'].lower()
                )
                
                # Check for title match (flexible)
                title_match = (
                    citation['title'].lower() in db_title.lower() or
                    db_title.lower() in citation['title'].lower()
                )
                
                if author_match and title_match:
                    found_match = True
                    db_year = self.extract_year_from_date(db_date)
                    
                    # Verify details
                    discrepancies = []
                    
                    if citation['publisher'].lower() not in db_publisher.lower() and db_publisher.lower() not in citation['publisher'].lower():
                        discrepancies.append(f"Publisher: MLA='{citation['publisher']}' vs DB='{db_publisher}'")
                    
                    if db_year and citation['year'] != db_year:
                        discrepancies.append(f"Year: MLA='{citation['year']}' vs DB='{db_year}'")
                    
                    if discrepancies:
                        verification_results['discrepancies'].append({
                            'citation': citation,
                            'database': {
                                'author': db_author,
                                'title': db_title,
                                'publisher': db_publisher,
                                'year': db_year
                            },
                            'issues': discrepancies
                        })
                        print(f"   ⚠️ DISCREPANCIES FOUND:")
                        for issue in discrepancies:
                            print(f"      - {issue}")
                    else:
                        verification_results['verified'].append(citation)
                        print(f"   ✅ VERIFIED: Perfect match")
                    
                    break
            
            if not found_match:
                verification_results['missing'].append(citation)
                print(f"   ❌ NOT FOUND: No matching book in database")
            
            print()
        
        # Summary
        verified_count = len(verification_results['verified'])
        discrepancy_count = len(verification_results['discrepancies'])
        missing_count = len(verification_results['missing'])
        total_count = len(self.expected_citations)
        
        verification_results['summary'] = {
            'total_citations': total_count,
            'verified': verified_count,
            'discrepancies': discrepancy_count,
            'missing': missing_count,
            'accuracy_rate': (verified_count / total_count) * 100 if total_count > 0 else 0
        }
        
        print("📋 VERIFICATION SUMMARY")
        print("=" * 30)
        print(f"✅ Verified: {verified_count}/{total_count} ({verification_results['summary']['accuracy_rate']:.1f}%)")
        print(f"⚠️ Discrepancies: {discrepancy_count}")
        print(f"❌ Missing: {missing_count}")
        
        if verified_count == total_count:
            print("\n🎉 ALL MLA CITATIONS SUCCESSFULLY VERIFIED!")
        elif verified_count + discrepancy_count == total_count:
            print("\n✅ All cited works found in database (some formatting differences)")
        else:
            print(f"\n⚠️ {missing_count} citations could not be verified against database")
        
        return verification_results
    
    def generate_report(self) -> str:
        """Generate detailed verification report"""
        results = self.verify_citations()
        
        report = f"""
MLA CITATION VERIFICATION REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY:
- Total Citations: {results['summary']['total_citations']}
- Verified: {results['summary']['verified']}
- Discrepancies: {results['summary']['discrepancies']}
- Missing: {results['summary']['missing']}
- Accuracy Rate: {results['summary']['accuracy_rate']:.1f}%

VERIFICATION STATUS:
"""
        
        if results['verified']:
            report += "\n✅ VERIFIED CITATIONS:\n"
            for citation in results['verified']:
                report += f"   - {citation['author']}. {citation['title']}. {citation['publisher']}, {citation['year']}.\n"
        
        if results['discrepancies']:
            report += "\n⚠️ CITATIONS WITH DISCREPANCIES:\n"
            for item in results['discrepancies']:
                report += f"   - {item['citation']['author']}. {item['citation']['title']}\n"
                for issue in item['issues']:
                    report += f"     ISSUE: {issue}\n"
        
        if results['missing']:
            report += "\n❌ MISSING CITATIONS:\n"
            for citation in results['missing']:
                report += f"   - {citation['author']}. {citation['title']}\n"
        
        return report

def main():
    """Main verification function"""
    print("🎯 LibraryOfBabel MLA Citation Verifier")
    print("Verifying citations against PostgreSQL database...")
    print()
    
    verifier = MLACitationVerifier()
    
    try:
        # Run verification
        results = verifier.verify_citations()
        
        # Generate and save report
        report = verifier.generate_report()
        
        # Save report to file
        report_path = "mla_verification_report.txt"
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"\n📄 Detailed report saved to: {report_path}")
        
        # Return exit code based on verification success
        if results['summary']['verified'] == results['summary']['total_citations']:
            print("\n🏆 VERIFICATION SUCCESSFUL: All citations verified!")
            return 0
        else:
            print("\n⚠️ VERIFICATION INCOMPLETE: Some issues found")
            return 1
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)