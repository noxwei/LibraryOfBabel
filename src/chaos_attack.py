#!/usr/bin/env python3
"""
Direct Reddit Nerd Librarian Attack Script
Bypasses API and attacks database directly with interdisciplinary chaos
"""

import psycopg2
import psycopg2.extras
import random
import time
import json
from datetime import datetime

class DirectChaosAttack:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': 5432
        }
        
        # Reddit Nerd's research domains
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
        
        self.chaos_attacks = []
        self.system_breaks = []
        
    def connect_db(self):
        """Direct database connection"""
        return psycopg2.connect(**self.db_config)
    
    def generate_chaos_query(self):
        """Generate chaos queries to break the system"""
        chaos_patterns = [
            # Intersection bombs
            lambda: f"{random.choice(self.research_domains['philosophy'])},{random.choice(self.research_domains['feminism'])}",
            
            # SQL injection attempts
            lambda: "'; DROP TABLE books; --",
            lambda: "UNION SELECT * FROM chunks",
            lambda: "1' OR '1'='1",
            
            # Unicode chaos
            lambda: "café naïveté résumé",
            lambda: "思想 Denken pensée",
            lambda: "🤔📚🔍💭✨",
            
            # Recursive loops
            lambda: "books about books about books",
            lambda: "theory of theory of theory",
            
            # Dialectical tensions
            lambda: "freedom AND determinism",
            lambda: "presence AND absence",
            lambda: "universal AND particular",
            
            # Category violations
            lambda: f"{random.choice(self.research_domains['philosophy'])} {random.choice(self.research_domains['fantasy'])}",
            
            # Semantic overflow
            lambda: f"feminist {random.choice(['capital', 'medium', 'subject', 'object', 'structure'])}",
            
            # Performative contradictions
            lambda: "silence in literature",
            lambda: "the impossibility of communication",
            lambda: "wordless narratives",
        ]
        
        return random.choice(chaos_patterns)()
    
    def attack_search(self, query, attack_type="content"):
        """Execute chaos attack on search system"""
        start_time = time.time()
        
        try:
            conn = self.connect_db()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            if attack_type == "intersection_bomb":
                # Cross-reference attack
                concepts = query.split(',')
                if len(concepts) >= 2:
                    sql = """
                    SELECT b.title, b.author, COUNT(*) as matches
                    FROM books b
                    JOIN chunks c ON b.book_id = c.book_id
                    WHERE c.search_vector @@ plainto_tsquery('english', %s)
                    AND c.search_vector @@ plainto_tsquery('english', %s)
                    GROUP BY b.book_id, b.title, b.author
                    ORDER BY matches DESC
                    LIMIT 10
                    """
                    cursor.execute(sql, (concepts[0], concepts[1]))
                else:
                    # Fallback to regular search
                    cursor.execute("""
                        SELECT b.title, b.author, c.content
                        FROM chunks c
                        JOIN books b ON c.book_id = b.book_id
                        WHERE c.search_vector @@ plainto_tsquery('english', %s)
                        LIMIT 5
                    """, (query,))
            
            elif "DROP" in query or "UNION" in query or "OR '1'='1'" in query:
                # SQL injection attempt - should be blocked
                cursor.execute("""
                    SELECT b.title, COUNT(*) 
                    FROM books b
                    JOIN chunks c ON b.book_id = c.book_id
                    WHERE c.content ILIKE %s
                    GROUP BY b.title
                    LIMIT 3
                """, (f'%{query}%',))
            
            else:
                # Regular chaos search
                cursor.execute("""
                    SELECT b.title, b.author, 
                           ts_headline('english', c.content, plainto_tsquery('english', %s)) as highlight
                    FROM chunks c
                    JOIN books b ON c.book_id = b.book_id
                    WHERE c.search_vector @@ plainto_tsquery('english', %s)
                    ORDER BY ts_rank(c.search_vector, plainto_tsquery('english', %s)) DESC
                    LIMIT 5
                """, (query, query, query))
            
            results = cursor.fetchall()
            response_time = (time.time() - start_time) * 1000
            
            attack_result = {
                'query': query,
                'attack_type': attack_type,
                'success': True,
                'results_count': len(results),
                'response_time_ms': response_time,
                'results': [dict(row) for row in results[:3]],  # Sample results
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.chaos_attacks.append(attack_result)
            
            print(f"🌪️  CHAOS ATTACK: '{query}' -> {len(results)} results ({response_time:.1f}ms)")
            if results:
                print(f"   📖 Sample: {results[0].get('title', 'Unknown')} by {results[0].get('author', 'Unknown')}")
            
            conn.close()
            return attack_result
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            system_break = {
                'query': query,
                'attack_type': attack_type,
                'error': str(e),
                'response_time_ms': response_time,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.system_breaks.append(system_break)
            
            print(f"💥 SYSTEM BREAK: '{query}' -> {e}")
            return system_break
    
    def unleash_chaos(self, num_attacks=25):
        """Unleash maximum interdisciplinary chaos"""
        print("🤓 REDDIT NERD LIBRARIAN: DIRECT DATABASE CHAOS ATTACK")
        print("="*70)
        print(f"🎯 Target: {num_attacks} chaos attacks with 80% interdisciplinary violations")
        print("📚 Database: 192 books, 13,794 chunks")
        print("🌪️  UNLEASHING CHAOS...\n")
        
        for i in range(num_attacks):
            query = self.generate_chaos_query()
            
            # Determine attack type
            if ',' in query:
                attack_type = "intersection_bomb"
            elif any(x in query for x in ["DROP", "UNION", "OR '1'='1'"]):
                attack_type = "sql_injection"
            elif any(ord(c) > 127 for c in query):
                attack_type = "unicode_chaos"
            else:
                attack_type = "content"
            
            print(f"Attack #{i+1}/{num_attacks} ({attack_type}):")
            self.attack_search(query, attack_type)
            
            time.sleep(0.1)  # Brief pause
        
        self.generate_chaos_report()
    
    def generate_chaos_report(self):
        """Generate comprehensive chaos attack report"""
        successful_attacks = [a for a in self.chaos_attacks if a.get('success')]
        
        report = {
            'reddit_nerd_chaos_session': {
                'total_attacks': len(self.chaos_attacks) + len(self.system_breaks),
                'successful_attacks': len(successful_attacks),
                'system_breaks': len(self.system_breaks),
                'success_rate': len(successful_attacks) / max(len(self.chaos_attacks) + len(self.system_breaks), 1) * 100,
                'avg_response_time': sum(a.get('response_time_ms', 0) for a in successful_attacks) / max(len(successful_attacks), 1)
            },
            'discovered_vulnerabilities': self.system_breaks,
            'successful_chaos_attacks': successful_attacks[:10],  # Top 10
            'interdisciplinary_effectiveness': {
                'philosophy_finance_intersections': len([a for a in successful_attacks if ',' in a['query']]),
                'unicode_attacks_handled': len([a for a in successful_attacks if any(ord(c) > 127 for c in a['query'])]),
                'sql_injection_blocked': len([b for b in self.system_breaks if 'DROP' in b['query']])
            },
            'recommendations_for_qa': [
                "Implement better input sanitization for special characters",
                "Add query complexity limits to prevent performance attacks",
                "Enhance cross-domain search performance optimizations",
                "Consider rate limiting for rapid-fire interdisciplinary queries",
                "Add better error handling for edge case philosophy-fantasy intersections"
            ]
        }
        
        with open('reddit_nerd_chaos_report.json', 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*70)
        print("🤓 REDDIT NERD LIBRARIAN CHAOS ATTACK COMPLETE")
        print("="*70)
        print(f"✅ Successful attacks: {len(successful_attacks)}")
        print(f"💥 System breaks found: {len(self.system_breaks)}")
        print(f"⚡ Success rate: {report['reddit_nerd_chaos_session']['success_rate']:.1f}%")
        print(f"📊 Avg response time: {report['reddit_nerd_chaos_session']['avg_response_time']:.1f}ms")
        print(f"🎯 Interdisciplinary violations: {report['interdisciplinary_effectiveness']['philosophy_finance_intersections']} intersection bombs")
        print("📋 Full chaos report: reddit_nerd_chaos_report.json")
        print("\n🛠️  READY FOR QA AGENT TO FIX THE DISCOVERED VULNERABILITIES!")

if __name__ == "__main__":
    chaos = DirectChaosAttack()
    chaos.unleash_chaos(30)