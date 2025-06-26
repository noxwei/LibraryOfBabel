#!/usr/bin/env python3
"""
Test Audio Setup - Verify Dependencies
Quick test to check if all audio processing dependencies are working
"""

def test_dependencies():
    """Test if all required audio dependencies are available"""
    print("🔧 Testing Backend Audio Agent dependencies...\n")
    
    # Test 1: Basic imports
    try:
        import whisper
        print("✅ OpenAI Whisper imported successfully")
    except ImportError as e:
        print(f"❌ Whisper import failed: {e}")
        return False
    
    try:
        import librosa
        print("✅ Librosa imported successfully")
    except ImportError as e:
        print(f"❌ Librosa import failed: {e}")
        return False
    
    try:
        import soundfile as sf
        print("✅ SoundFile imported successfully")
    except ImportError as e:
        print(f"❌ SoundFile import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ NumPy imported successfully")
    except ImportError as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    # Test 2: Load smallest Whisper model
    try:
        print("\n🤖 Loading Whisper 'tiny' model for testing...")
        model = whisper.load_model("tiny")
        print("✅ Whisper model loaded successfully")
    except Exception as e:
        print(f"❌ Whisper model loading failed: {e}")
        return False
    
    # Test 3: Test Backend Audio Agent import
    try:
        import sys
        sys.path.append('/Users/weixiangzhang/Local Dev/LibraryOfBabel/src')
        from backend_audio_agent import BackendAudioAgent
        print("✅ Backend Audio Agent imported successfully")
    except ImportError as e:
        print(f"❌ Backend Audio Agent import failed: {e}")
        return False
    
    # Test 4: Initialize agent
    try:
        agent = BackendAudioAgent(model_size="tiny")
        print("✅ Backend Audio Agent initialized successfully")
    except Exception as e:
        print(f"❌ Backend Audio Agent initialization failed: {e}")
        return False
    
    print("\n🎉 ALL TESTS PASSED! Backend Audio Agent is ready.")
    print("🎯 Ready to process audiobooks with free local Whisper transcription!")
    return True

if __name__ == "__main__":
    success = test_dependencies()
    exit(0 if success else 1)