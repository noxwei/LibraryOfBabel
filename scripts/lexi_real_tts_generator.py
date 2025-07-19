#!/usr/bin/env python3
"""
🎧 Dr. Alexandra "Lexi" Hartwell - REAL TTS Audio Generator
===========================================================

Generates ACTUAL TTS audio using HuggingFace setfunctionenvironment/testnew dataset
Optimized for Mac Mini M2 Pro with 32GB RAM
"""

import os
import json
from pathlib import Path
from datetime import datetime
import subprocess
import sys

# Try to import optional dependencies
try:
    import torch
    import numpy as np
    import soundfile as sf
    HAS_ML_DEPS = True
except ImportError:
    HAS_ML_DEPS = False
    print("📦 ML dependencies not available - using system TTS")

class LexiRealTTSGenerator:
    """
    Real TTS Audio Generation using HuggingFace dataset and models
    """
    
    def __init__(self):
        self.name = "Dr. Alexandra \"Lexi\" Hartwell"
        self.title = "Audio Synthesis Agent"
        
        # Paths
        self.audio_output_dir = Path("audio/synthesis/eve_babitz")
        self.tts_log_dir = Path("audio/tts_logs")
        
        # Create directories
        self.audio_output_dir.mkdir(parents=True, exist_ok=True)
        self.tts_log_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🎧 {self.name} - REAL TTS Generator Initialized")
        print(f"🎵 Audio Output: {self.audio_output_dir}")
        
    def install_real_tts_dependencies(self):
        """Install real TTS dependencies for Mac M2 Pro"""
        print("📦 Installing REAL TTS dependencies for Mac M2 Pro...")
        
        dependencies = [
            "torch",
            "torchaudio", 
            "datasets",
            "transformers",
            "soundfile",
            "librosa",
            "numpy",
            "scipy"
        ]
        
        for dep in dependencies:
            try:
                print(f"   Installing {dep}...")
                result = subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                                      capture_output=True, text=True, timeout=180)
                if result.returncode == 0:
                    print(f"   ✅ {dep} installed successfully")
                else:
                    print(f"   ⚠️ {dep} installation had issues: {result.stderr}")
            except subprocess.TimeoutExpired:
                print(f"   ⚠️ {dep} installation timed out")
        
        print("✅ TTS dependencies installation complete")
    
    def load_huggingface_dataset(self):
        """Load the HuggingFace setfunctionenvironment/testnew dataset"""
        print("📚 HuggingFace dataset: setfunctionenvironment/testnew (for future use)")
        
        if not HAS_ML_DEPS:
            print("   ⚠️ ML dependencies not available - skipping dataset load")
            return None
        
        try:
            from datasets import load_dataset
            
            # Load your specified dataset
            print("   🔄 Downloading dataset...")
            ds = load_dataset("setfunctionenvironment/testnew")
            
            print(f"   ✅ Dataset loaded successfully!")
            print(f"   📊 Dataset structure: {ds}")
            
            # Examine the first few samples
            if 'train' in ds:
                sample = ds['train'][0]
                print(f"   🎵 Sample keys: {list(sample.keys())}")
                
                # Check if audio data exists
                if 'audio' in sample:
                    import numpy as np
                    audio_info = sample['audio']
                    print(f"   🎧 Audio sample rate: {audio_info.get('sampling_rate', 'unknown')}")
                    print(f"   📊 Audio array shape: {np.array(audio_info['array']).shape if 'array' in audio_info else 'unknown'}")
            
            return ds
            
        except Exception as e:
            print(f"   ❌ Failed to load dataset: {e}")
            return None
    
    def setup_tts_model(self):
        """Setup TTS model for Mac M2 Pro"""
        print("🤖 Setting up TTS model for Mac M2 Pro...")
        
        if HAS_ML_DEPS:
            try:
                # Try to use a lightweight TTS approach for Mac
                from transformers import pipeline
                
                print("   🔄 Loading TTS pipeline...")
                
                # Use a smaller, CPU-friendly TTS model
                tts_pipeline = pipeline(
                    "text-to-speech",
                    model="microsoft/speecht5_tts",
                    device=-1  # Use CPU (better for Mac M2)
                )
                
                print("   ✅ TTS model loaded successfully!")
                return tts_pipeline
                
            except Exception as e:
                print(f"   ⚠️ HuggingFace TTS failed: {e}")
                print("   🔄 Trying alternative approach...")
        else:
            print("   🔄 Using macOS system TTS (no ML deps)")
        
        # Fallback: Use system TTS (macOS built-in)
        return self.setup_system_tts()
    
    def setup_system_tts(self):
        """Setup macOS system TTS as fallback"""
        print("   🍎 Using macOS system TTS...")
        
        # Test macOS say command (say doesn't have --version, just test with help)
        try:
            result = subprocess.run(['say', '-h'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 or 'Usage:' in result.stderr:
                print("   ✅ macOS TTS available")
                return "system_tts"
            else:
                print("   ❌ macOS TTS not available")
                return None
        except:
            # Try direct test
            try:
                subprocess.run(['say', 'test'], capture_output=True, timeout=3)
                print("   ✅ macOS TTS available (direct test)")
                return "system_tts"
            except:
                print("   ❌ macOS TTS test failed")
                return None
    
    def generate_audio_with_system_tts(self, text, output_path):
        """Generate audio using macOS system TTS"""
        print(f"   🍎 Generating with macOS TTS...")
        
        try:
            # Use macOS say command to generate audio
            cmd = [
                'say',
                '-v', 'Samantha',  # Use Samantha voice (good quality)
                '-r', '180',       # Speaking rate (words per minute)
                '-o', str(output_path),  # Output file
                text
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and output_path.exists():
                # Get audio file info
                duration = self.get_audio_duration(output_path)
                
                return {
                    "audio_file": str(output_path),
                    "duration_seconds": duration,
                    "sample_rate": 22050,  # macOS default
                    "format": "aiff",
                    "model_used": "macOS-Samantha",
                    "status": "success"
                }
            else:
                print(f"   ❌ TTS command failed: {result.stderr}")
                return {"status": "failed", "error": result.stderr}
                
        except subprocess.TimeoutExpired:
            print("   ❌ TTS generation timed out")
            return {"status": "failed", "error": "timeout"}
        except Exception as e:
            print(f"   ❌ TTS generation error: {e}")
            return {"status": "failed", "error": str(e)}
    
    def get_audio_duration(self, audio_path, text=""):
        """Get duration of audio file"""
        try:
            result = subprocess.run(['afinfo', str(audio_path)], 
                                  capture_output=True, text=True)
            # Parse duration from afinfo output
            for line in result.stdout.split('\n'):
                if 'estimated duration' in line.lower():
                    duration_str = line.split(':')[-1].strip().split()[0]
                    return float(duration_str)
            return 0.0
        except:
            # Fallback: estimate based on text length
            return len(text.split()) / 2.5  # ~2.5 words per second
    
    def generate_real_tts_audio(self, text, chunk_id):
        """Generate REAL TTS audio"""
        print(f"🎵 GENERATING REAL TTS AUDIO for chunk {chunk_id}...")
        
        # Load dataset first
        dataset = self.load_huggingface_dataset()
        
        # Setup TTS model
        tts_model = self.setup_tts_model()
        
        if not tts_model:
            print("❌ No TTS model available")
            return {"status": "failed", "error": "no_tts_model"}
        
        # Generate audio filename
        audio_filename = f"chunk_{chunk_id}_babitz_real.aiff"
        audio_path = self.audio_output_dir / audio_filename
        
        # Generate audio
        if tts_model == "system_tts":
            tts_result = self.generate_audio_with_system_tts(text, audio_path)
        else:
            # Use HuggingFace model (if available)
            try:
                if HAS_ML_DEPS:
                    # Generate with HuggingFace TTS
                    audio_output = tts_model(text)
                    
                    # Save audio
                    audio_array = audio_output['audio']
                    sample_rate = audio_output.get('sampling_rate', 22050)
                    
                    import soundfile as sf
                    sf.write(str(audio_path), audio_array, sample_rate)
                    
                    tts_result = {
                        "audio_file": str(audio_path),
                        "duration_seconds": len(audio_array) / sample_rate,
                        "sample_rate": sample_rate,
                        "format": "aiff",
                        "model_used": "HuggingFace-TTS",
                        "status": "success"
                    }
                else:
                    # No ML deps - fallback to system TTS
                    tts_result = self.generate_audio_with_system_tts(text, audio_path)
                
            except Exception as e:
                print(f"   ❌ HuggingFace TTS failed: {e}")
                # Fallback to system TTS
                tts_result = self.generate_audio_with_system_tts(text, audio_path)
        
        return tts_result
    
    def process_eve_babitz_real_audio(self):
        """Generate REAL audio for Eve Babitz chunk"""
        print(f"\n🎯 GENERATING REAL TTS AUDIO - Eve Babitz")
        print("=" * 60)
        
        # Load cleaned text
        validation_file = Path("audio/validation_logs/chunk_1015_chapter_4_validation.json")
        
        if not validation_file.exists():
            print(f"❌ Validation file not found: {validation_file}")
            return None
        
        with open(validation_file, 'r') as f:
            validation_data = json.load(f)
        
        chunk_id = validation_data['chunk_id']
        clean_text = validation_data['cleaning_result']['cleaned_text']
        
        print(f"📖 Processing chunk: {chunk_id}")
        print(f"📊 Text length: {len(clean_text)} characters")
        print(f"📝 Word count: {len(clean_text.split())} words")
        
        # Generate REAL TTS audio
        tts_result = self.generate_real_tts_audio(clean_text, chunk_id)
        
        if tts_result.get('status') == 'success':
            # Log real TTS generation
            real_tts_log = {
                "timestamp": datetime.now().isoformat(),
                "chunk_id": chunk_id,
                "text_length": len(clean_text),
                "word_count": len(clean_text.split()),
                "tts_result": tts_result,
                "hardware": "Mac Mini M2 Pro 32GB",
                "generated_by": self.name,
                "generation_type": "REAL_TTS"
            }
            
            log_file = self.tts_log_dir / f"real_tts_{chunk_id}.json"
            with open(log_file, 'w') as f:
                json.dump(real_tts_log, f, indent=2)
            
            print(f"\n🎉 REAL TTS AUDIO GENERATED!")
            print(f"🎧 File: {tts_result['audio_file']}")
            print(f"⏱️ Duration: {tts_result['duration_seconds']:.1f} seconds")
            print(f"🎚️ Model: {tts_result['model_used']}")
            print(f"📋 Log: {log_file}")
            
            return tts_result
            
        else:
            print(f"\n❌ REAL TTS GENERATION FAILED")
            print(f"Error: {tts_result.get('error', 'unknown')}")
            return None

def main():
    """Generate real TTS audio"""
    print("🚀 Starting REAL TTS Audio Generation...")
    
    generator = LexiRealTTSGenerator()
    
    # Install dependencies
    generator.install_real_tts_dependencies()
    
    # Generate real TTS audio
    result = generator.process_eve_babitz_real_audio()
    
    if result:
        print(f"\n✅ REAL TTS GENERATION COMPLETE!")
        print(f"🎧 Audio file: {result['audio_file']}")
        print(f"⏱️ Duration: {result['duration_seconds']:.1f} seconds")
        print(f"🎵 You can now listen to Eve Babitz!")
    else:
        print(f"\n❌ REAL TTS GENERATION FAILED")
    
    return result

if __name__ == "__main__":
    main()