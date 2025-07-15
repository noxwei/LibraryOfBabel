#!/usr/bin/env python3
"""
🌪️ AUTOMATED CHAOS DEMO - No User Input Required!
================================================

Runs the OBSURD BABEL CHAOS ENGINE in full automation mode
for maximum chaos without any interruptions!
"""

import sys
import os

# Add the current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from obsurd_babel_chaos_engine import ObsurdBabelChaosEngine, ChaosModes

def run_automated_chaos_demo():
    """Run an automated demonstration of ALL chaos modes"""
    print("🚀 AUTOMATED CHAOS DEMONSTRATION BEGINNING...")
    print("   No user input required - pure chaos automation!")
    print("=" * 60)
    
    # Initialize the engine
    engine = ObsurdBabelChaosEngine()
    
    # Demo all the chaos modes
    chaos_modes_to_demo = [
        ChaosModes.RANDOM_DISCOVERY,
        ChaosModes.SEMANTIC_TSUNAMI,
        ChaosModes.BOOK_PERSONALITY,
        ChaosModes.MYSTICAL_FORTUNE,
        ChaosModes.RAINBOW_BRIDGES
    ]
    
    for i, mode in enumerate(chaos_modes_to_demo, 1):
        engine.chaos_print(f"🎭 DEMO MODE {i}/{len(chaos_modes_to_demo)}: {mode.value}", 'BOLD', 4)
        engine.chaos_print("🌟 Initiating automated chaos sequence...", 'CYAN', 2)
        
        try:
            engine.execute_chaos_mode(mode)
            engine.chaos_print("✅ Chaos mode completed successfully!", 'GREEN', 2)
        except Exception as e:
            engine.chaos_print(f"💥 Chaos overflow: {str(e)}", 'RED', 2)
        
        print("\n" + "🌈" * 60 + "\n")
    
    # Final chaos statistics
    engine.chaos_print("🎪 AUTOMATED CHAOS DEMO COMPLETE!", 'BOLD', 5)
    engine.chaos_print(f"📊 Total Chaos Level Achieved: {engine.chaos_level}", 'YELLOW', 3)
    engine.chaos_print(f"🧠 Consciousness Level: {engine.consciousness_level:.2f}", 'PURPLE', 2)
    engine.chaos_print(f"📚 Books Discovered: {len(engine.books_discovered)}", 'GREEN', 2)

if __name__ == "__main__":
    run_automated_chaos_demo()