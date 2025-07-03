#!/usr/bin/env python3
"""
Monitor embedding completion and launch agent system
"""

import time
import subprocess
import logging
from datetime import datetime
import psycopg2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': 'localhost',
    'database': 'knowledge_base',
    'user': 'weixiangzhang',
    'port': 5432
}

def check_embedding_completion():
    """Check if embedding generation is complete"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM chunks WHERE embedding_array IS NULL")
        pending = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM chunks")
        total = cursor.fetchone()[0]
        
        embedded = total - pending
        completion_pct = (embedded / total) * 100 if total > 0 else 0
        
        conn.close()
        
        return {
            'total': total,
            'embedded': embedded,
            'pending': pending,
            'completion_pct': completion_pct,
            'is_complete': pending == 0
        }
        
    except Exception as e:
        logger.error(f"Error checking embedding status: {e}")
        return {'is_complete': False, 'error': str(e)}

def launch_agent_demo():
    """Launch agent demonstration with seed questions"""
    logger.info("🚀 Launching Agent Demonstration System!")
    
    # Generate 10 questions with different seeds
    seeds_to_try = [42, 123, 777, 1337, 2024, 5150, 8888, 9999, 1111, 3333]
    
    for i, seed in enumerate(seeds_to_try, 1):
        logger.info(f"🎲 Generating question {i}/10 with seed {seed}")
        
        try:
            # Generate question
            result = subprocess.run([
                'python3', '../seed_question_generator.py',
                '--seed', str(seed),
                '--ask-agent'
            ], capture_output=True, text=True, timeout=360)  # Increased timeout to 6 minutes
            
            if result.returncode == 0:
                logger.info(f"✅ Question {i} completed successfully")
                print(f"\n{'='*60}")
                print(f"QUESTION {i} (Seed: {seed})")
                print('='*60)
                print(result.stdout)
            else:
                logger.error(f"❌ Question {i} failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.warning(f"⏰ Question {i} timed out")
        except Exception as e:
            logger.error(f"❌ Error with question {i}: {e}")
        
        # Brief pause between questions
        time.sleep(5)
    
    logger.info("🎉 Agent demonstration complete!")

def main():
    """Main monitoring loop"""
    logger.info("🔍 Starting embedding completion monitor...")
    
    # Check initial status
    status = check_embedding_completion()
    
    if status.get('is_complete'):
        logger.info("✅ Embeddings already complete! Launching agents immediately...")
        launch_agent_demo()
        return
    
    logger.info(f"📊 Initial status: {status.get('embedded', 0)}/{status.get('total', 0)} "
               f"chunks embedded ({status.get('completion_pct', 0):.1f}%)")
    
    # Monitor until complete
    check_interval = 300  # Check every 5 minutes
    last_reported_pct = -1
    
    while True:
        status = check_embedding_completion()
        
        if status.get('error'):
            logger.error(f"Monitor error: {status['error']}")
            time.sleep(check_interval)
            continue
        
        current_pct = status.get('completion_pct', 0)
        
        # Report progress every 10% or when complete
        if current_pct - last_reported_pct >= 10 or status.get('is_complete'):
            logger.info(f"📈 Progress: {status.get('embedded', 0)}/{status.get('total', 0)} "
                       f"chunks embedded ({current_pct:.1f}%)")
            last_reported_pct = current_pct
        
        if status.get('is_complete'):
            logger.info("🎉 Embedding generation COMPLETE!")
            logger.info("🤖 Launching agent system with seed questions...")
            launch_agent_demo()
            break
        
        # Wait before next check
        time.sleep(check_interval)

if __name__ == "__main__":
    main()