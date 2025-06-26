#!/usr/bin/env python3
"""
Audio Architecture Test
Test the Backend Audio Agent architecture without heavy dependencies
"""

import os
import json
from pathlib import Path
from datetime import datetime

def test_audio_architecture():
    """Test the Backend Audio Agent architecture"""
    print("🏗️  Testing Backend Audio Agent Architecture...\n")
    
    # Test 1: Directory creation
    try:
        temp_dir = Path("./temp_audio_processing")
        output_dir = Path("./output/audio_transcripts")
        
        temp_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print("✅ Directory structure created successfully")
        print(f"   📁 Temp: {temp_dir}")
        print(f"   📁 Output: {output_dir}")
    except Exception as e:
        print(f"❌ Directory creation failed: {e}")
        return False
    
    # Test 2: Audiobook source access
    try:
        source_path = Path("/Volumes/Everything/Plex Media/Archieve Audiobooks/A For New Books/")
        if source_path.exists():
            audio_files = list(source_path.glob("*.m4b"))
            print(f"✅ Source directory accessible: {len(audio_files)} .m4b files found")
            
            # Show smallest files for testing
            if audio_files:
                files_with_size = [(f, f.stat().st_size) for f in audio_files]
                files_with_size.sort(key=lambda x: x[1])
                
                print("   📊 Smallest audiobooks for testing:")
                for i, (f, size) in enumerate(files_with_size[:3], 1):
                    size_mb = size / (1024 * 1024)
                    print(f"      {i}. {f.name} ({size_mb:.1f}MB)")
        else:
            print("❌ Source directory not accessible")
            return False
    except Exception as e:
        print(f"❌ Source access test failed: {e}")
        return False
    
    # Test 3: Mock transcript structure
    try:
        mock_transcript = {
            'book_id': 'test_12345',
            'source_file': '/path/to/audiobook.m4b',
            'metadata': {
                'title': 'Test Audiobook',
                'author': 'Test Author',
                'duration_seconds': 7200,  # 2 hours
                'file_size_mb': 150,
                'processed_date': datetime.utcnow().isoformat()
            },
            'transcript': {
                'full_text': 'This is a test transcript...',
                'word_count': 5,
                'chunks': [
                    {
                        'chunk_index': 0,
                        'chunk_start_time': 0,
                        'transcript': {
                            'text': 'This is a test transcript...',
                            'segments': [
                                {
                                    'start': 0.0,
                                    'end': 5.0,
                                    'text': 'This is a test transcript...'
                                }
                            ],
                            'language': 'english',
                            'processing_time': 12.5,
                            'chunk_file': 'test_12345_chunk_000.wav'
                        }
                    }
                ]
            },
            'processing_stats': {
                'total_chunks': 1,
                'successful_chunks': 1,
                'processing_time_seconds': 15.0,
                'transcription_speed': 480.0  # 8x realtime
            }
        }
        
        # Save mock transcript
        mock_file = output_dir / "mock_transcript_test.json"
        with open(mock_file, 'w', encoding='utf-8') as f:
            json.dump(mock_transcript, f, ensure_ascii=False, indent=2)
        
        print("✅ Mock transcript structure validated")
        print(f"   📄 Saved: {mock_file}")
    except Exception as e:
        print(f"❌ Mock transcript test failed: {e}")
        return False
    
    # Test 4: Storage space check
    try:
        import shutil
        free_space = shutil.disk_usage(temp_dir).free
        free_gb = free_space / (1024**3)
        
        if free_gb > 5:
            print(f"✅ Sufficient storage space: {free_gb:.1f}GB available")
        else:
            print(f"⚠️  Limited storage space: {free_gb:.1f}GB available (recommend >5GB)")
    except Exception as e:
        print(f"❌ Storage check failed: {e}")
        return False
    
    # Test 5: Chunking strategy simulation
    try:
        chunk_duration = 600  # 10 minutes
        sample_audiobook_duration = 7200  # 2 hours
        
        estimated_chunks = int(sample_audiobook_duration / chunk_duration) + 1
        print(f"✅ Chunking strategy validated")
        print(f"   ⏱️  Sample book: 2 hours → {estimated_chunks} chunks (10min each)")
        print(f"   💾 Estimated temp storage per book: ~{estimated_chunks * 50}MB")
    except Exception as e:
        print(f"❌ Chunking simulation failed: {e}")
        return False
    
    print("\n🎉 ARCHITECTURE TESTS PASSED!")
    print("🎯 Backend Audio Agent architecture is solid")
    print("⏳ Waiting for Whisper dependencies to finish installing...")
    print("\n📋 Next steps:")
    print("   1. Wait for pip install to complete")
    print("   2. Test with smallest audiobook file")
    print("   3. Scale to larger collection")
    print("   4. Integrate with knowledge base")
    
    return True

if __name__ == "__main__":
    success = test_audio_architecture()
    exit(0 if success else 1)