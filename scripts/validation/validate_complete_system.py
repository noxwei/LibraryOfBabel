#!/usr/bin/env python3
"""
Complete System Validation
Tests the entire pipeline from vector database to publication-ready essays
"""

import os
import time
import json
import requests
from datetime import datetime
import subprocess
import psycopg2

def validate_system_components():
    """Validate all system components are operational"""
    print("🔍 Complete System Validation")
    print("=" * 50)
    
    results = {'tests': [], 'overall_status': 'unknown'}
    
    # 1. Database validation
    print("1. Validating PostgreSQL database...")
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='knowledge_base',
            user='weixiangzhang',
            port=5432
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chunks")
        chunk_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM books")
        book_count = cursor.fetchone()[0]
        conn.close()
        
        if chunk_count >= 1000 and book_count >= 20:
            print(f"   ✅ Database: {chunk_count:,} chunks, {book_count} books")
            results['tests'].append(('Database', 'pass', f'{chunk_count} chunks'))
        else:
            print(f"   ⚠️ Database: Low content ({chunk_count} chunks, {book_count} books)")
            results['tests'].append(('Database', 'warning', 'Low content'))
    except Exception as e:
        print(f"   ❌ Database: {e}")
        results['tests'].append(('Database', 'fail', str(e)))
    
    # 2. Ollama validation
    print("\n2. Validating Ollama service...")
    try:
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        if response.status_code == 200:
            print("   ✅ Ollama: Service running")
            
            # Check available models
            models_response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if models_response.status_code == 200:
                models = models_response.json().get('models', [])
                model_names = [m['name'] for m in models]
                high_quality_models = [m for m in model_names if any(x in m for x in ['qwen2.5', 'llama3.1'])]
                
                if high_quality_models:
                    print(f"   ✅ Models: {len(high_quality_models)} high-quality models available")
                    results['tests'].append(('Ollama', 'pass', f'{len(models)} models'))
                else:
                    print(f"   ⚠️ Models: Only {len(models)} models, may lack high-quality options")
                    results['tests'].append(('Ollama', 'warning', 'Limited models'))
        else:
            print(f"   ❌ Ollama: HTTP {response.status_code}")
            results['tests'].append(('Ollama', 'fail', f'HTTP {response.status_code}'))
    except Exception as e:
        print(f"   ❌ Ollama: {e}")
        results['tests'].append(('Ollama', 'fail', str(e)))
    
    # 3. Essay API validation
    print("\n3. Validating Essay Generation API...")
    try:
        response = requests.get("http://localhost:5571/api/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            if health_data.get('status') == 'healthy':
                print("   ✅ Essay API: Healthy and operational")
                results['tests'].append(('Essay API', 'pass', 'Healthy'))
            else:
                print(f"   ⚠️ Essay API: {health_data.get('status')}")
                results['tests'].append(('Essay API', 'warning', health_data.get('status')))
        else:
            print(f"   ❌ Essay API: HTTP {response.status_code}")
            results['tests'].append(('Essay API', 'fail', f'HTTP {response.status_code}'))
    except Exception as e:
        print(f"   ❌ Essay API: Not running - {e}")
        results['tests'].append(('Essay API', 'fail', 'Not running'))
    
    # 4. Reference essay validation
    print("\n4. Validating reference essay...")
    reference_path = "/Users/weixiangzhang/Local Dev/LibraryOfBabel/essays/the_cognitive_capture_machine.md"
    try:
        if os.path.exists(reference_path):
            with open(reference_path, 'r') as f:
                content = f.read()
            word_count = len(content.split())
            if word_count >= 2000:
                print(f"   ✅ Reference Essay: {word_count:,} words")
                results['tests'].append(('Reference Essay', 'pass', f'{word_count} words'))
            else:
                print(f"   ⚠️ Reference Essay: Short ({word_count} words)")
                results['tests'].append(('Reference Essay', 'warning', f'Short: {word_count} words'))
        else:
            print("   ❌ Reference Essay: File not found")
            results['tests'].append(('Reference Essay', 'fail', 'Not found'))
    except Exception as e:
        print(f"   ❌ Reference Essay: {e}")
        results['tests'].append(('Reference Essay', 'fail', str(e)))
    
    # 5. QA system validation
    print("\n5. Validating QA system...")
    try:
        if os.path.exists("essay_qa_system.py"):
            # Test import
            result = subprocess.run(['python3', '-c', 'import essay_qa_system; print("Import successful")'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("   ✅ QA System: Import successful")
                results['tests'].append(('QA System', 'pass', 'Import OK'))
            else:
                print(f"   ❌ QA System: Import failed - {result.stderr}")
                results['tests'].append(('QA System', 'fail', 'Import failed'))
        else:
            print("   ❌ QA System: File not found")
            results['tests'].append(('QA System', 'fail', 'File not found'))
    except Exception as e:
        print(f"   ❌ QA System: {e}")
        results['tests'].append(('QA System', 'fail', str(e)))
    
    # Overall assessment
    passed = len([t for t in results['tests'] if t[1] == 'pass'])
    warnings = len([t for t in results['tests'] if t[1] == 'warning'])
    failed = len([t for t in results['tests'] if t[1] == 'fail'])
    total = len(results['tests'])
    
    print(f"\n📊 VALIDATION SUMMARY")
    print(f"   Total components: {total}")
    print(f"   Passed: {passed}")
    print(f"   Warnings: {warnings}")
    print(f"   Failed: {failed}")
    print(f"   Success rate: {passed/total*100:.1f}%")
    
    if failed == 0:
        if warnings == 0:
            results['overall_status'] = 'excellent'
            print("\n🎉 SYSTEM STATUS: EXCELLENT - All components operational")
        else:
            results['overall_status'] = 'good'
            print("\n✅ SYSTEM STATUS: GOOD - Ready with minor warnings")
    else:
        results['overall_status'] = 'degraded'
        print("\n⚠️ SYSTEM STATUS: DEGRADED - Some components need attention")
    
    return results

def test_essay_generation():
    """Test a quick essay generation"""
    print("\n🚀 Testing Essay Generation Pipeline")
    print("-" * 40)
    
    try:
        # Start generation
        test_data = {
            'topic': 'Test: Knowledge systems and cognitive control',
            'style': 'analytical',
            'search_query': 'knowledge power control'
        }
        
        print("   📝 Starting test essay generation...")
        response = requests.post("http://localhost:5571/api/generate", 
                               json=test_data, timeout=30)
        
        if response.status_code == 200:
            essay_id = response.json()['essay_id']
            print(f"   🔄 Generation started (ID: {essay_id})")
            
            # Poll for completion (max 5 minutes for quick test)
            max_wait = 300
            wait_time = 0
            
            while wait_time < max_wait:
                status_response = requests.get(f"http://localhost:5571/api/status/{essay_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    
                    if status_data['status'] == 'completed':
                        word_count = status_data.get('word_count', 0)
                        print(f"   ✅ Test essay completed: {word_count:,} words")
                        return True
                    elif status_data['status'] == 'error':
                        print(f"   ❌ Test essay failed: {status_data.get('error')}")
                        return False
                    else:
                        print(f"   ⏳ Status: {status_data['status']} ({wait_time}s)")
                
                time.sleep(10)
                wait_time += 10
            
            print("   ⏰ Test essay timeout (5 minutes)")
            return False
        else:
            print(f"   ❌ Generation request failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Test generation error: {e}")
        return False

def save_validation_report(results):
    """Save validation report"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = f"tests/system_validation_{timestamp}.json"
    
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    return report_path

def main():
    """Main validation function"""
    print("🎯 LibraryOfBabel Complete System Validation")
    print("Validating the entire pipeline from database to essay generation")
    print()
    
    # Component validation
    results = validate_system_components()
    
    # If basic components are working, test essay generation
    if results['overall_status'] in ['excellent', 'good']:
        essay_test_result = test_essay_generation()
        results['essay_generation_test'] = essay_test_result
        
        if essay_test_result:
            print("\n🎉 COMPLETE SYSTEM: OPERATIONAL")
            print("   📝 Essay generation pipeline validated")
            print("   🚀 Ready for production use")
        else:
            print("\n⚠️ COMPLETE SYSTEM: COMPONENTS OK, GENERATION ISSUES")
            print("   🔧 Check Ollama model availability and settings")
    else:
        print("\n❌ COMPLETE SYSTEM: COMPONENT ISSUES")
        print("   🔧 Fix component issues before testing generation")
    
    # Save report
    report_path = save_validation_report(results)
    print(f"\n📄 Validation report saved: {report_path}")
    
    # Final recommendations
    print("\n📋 NEXT STEPS:")
    if results['overall_status'] == 'excellent':
        print("   ✅ System ready for commit and deployment")
        print("   🚀 Run full QA tests: ./run_qa_tests.sh")
    elif results['overall_status'] == 'good':
        print("   ⚠️ Address warnings, then run QA tests")
        print("   📝 Review validation report for details")
    else:
        print("   🔧 Fix failed components before proceeding")
        print("   ❌ Do not commit until issues resolved")
    
    return 0 if results['overall_status'] in ['excellent', 'good'] else 1

if __name__ == "__main__":
    exit(main())