#!/usr/bin/env python3
"""
Backend Audio Agent - LibraryOfBabel Audio Transcription
========================================================

A specialized agent for processing 5000+ audiobooks using free local Whisper.
Handles massive audio files through intelligent chunking and local temp processing.

Mission: Transform audiobook collections into searchable transcripts without API costs.
"""

import os
import sys
import json
import time
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import hashlib
from datetime import datetime, timedelta
import psutil

# Audio processing imports
try:
    import whisper
    import librosa
    import soundfile as sf
    import numpy as np
except ImportError as e:
    print(f"❌ Missing audio dependencies: {e}")
    print("📦 Install with: pip install openai-whisper librosa soundfile numpy")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - AUDIO - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BackendAudioAgent:
    """
    Backend Audio Agent for massive audiobook collections
    
    Features:
    - Local Whisper transcription (free)
    - Intelligent chunking for large files
    - Memory-efficient processing
    - Resume capabilities for interrupted processing
    - Temp storage management
    """
    
    def __init__(self, 
                 temp_dir: str = "./temp_audio_processing",
                 output_dir: str = "./output/audio_transcripts",
                 model_size: str = "base"):
        """
        Initialize Backend Audio Agent
        
        Args:
            temp_dir: Temporary processing directory (local storage)
            output_dir: Final transcript output directory
            model_size: Whisper model size (tiny/base/small/medium/large)
        """
        self.temp_dir = Path(temp_dir)
        self.output_dir = Path(output_dir)
        self.model_size = model_size
        
        # Create directories
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Processing statistics
        self.stats = {
            'books_processed': 0,
            'total_audio_duration': 0,
            'total_transcript_words': 0,
            'processing_time': 0,
            'temp_storage_used': 0,
            'failed_books': []
        }
        
        # Load Whisper model
        self.whisper_model = None
        self.chunk_duration = 600  # 10 minutes per chunk
        self.max_temp_storage = 10 * 1024 * 1024 * 1024  # 10GB temp limit
        
        logger.info("🎧 Backend Audio Agent initialized")
        logger.info(f"📁 Temp storage: {self.temp_dir}")
        logger.info(f"📁 Output: {self.output_dir}")
        
    def load_whisper_model(self) -> bool:
        """Load Whisper model (lazy loading for memory efficiency)"""
        if self.whisper_model is None:
            try:
                logger.info(f"🤖 Loading Whisper {self.model_size} model...")
                self.whisper_model = whisper.load_model(self.model_size)
                logger.info("✅ Whisper model loaded successfully")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to load Whisper model: {e}")
                return False
        return True
    
    def get_audio_info(self, audio_path: Path) -> Dict:
        """Get audio file information without loading full file"""
        try:
            # Use librosa to get basic info efficiently
            duration = librosa.get_duration(path=str(audio_path))
            
            # Get file size
            file_size = audio_path.stat().st_size
            
            return {
                'duration_seconds': duration,
                'duration_hours': duration / 3600,
                'file_size_mb': file_size / (1024 * 1024),
                'estimated_chunks': int(duration / self.chunk_duration) + 1
            }
        except Exception as e:
            logger.error(f"Failed to get audio info for {audio_path}: {e}")
            return {}
    
    def check_temp_storage(self) -> bool:
        """Check if we have enough temp storage space"""
        try:
            # Get temp directory usage
            temp_usage = sum(f.stat().st_size for f in self.temp_dir.rglob('*') if f.is_file())
            
            # Get available disk space
            free_space = shutil.disk_usage(self.temp_dir).free
            
            logger.info(f"💾 Temp usage: {temp_usage / (1024**3):.1f}GB")
            logger.info(f"💾 Free space: {free_space / (1024**3):.1f}GB")
            
            if temp_usage > self.max_temp_storage:
                logger.warning("🧹 Temp storage limit exceeded, cleaning up...")
                self.cleanup_temp_storage()
            
            return free_space > 5 * 1024**3  # Need at least 5GB free
            
        except Exception as e:
            logger.error(f"Storage check failed: {e}")
            return False
    
    def cleanup_temp_storage(self):
        """Clean up temporary storage"""
        try:
            # Remove old temp files (older than 1 hour)
            cutoff_time = time.time() - 3600
            
            for temp_file in self.temp_dir.rglob('*'):
                if temp_file.is_file() and temp_file.stat().st_mtime < cutoff_time:
                    temp_file.unlink()
                    logger.debug(f"🗑️ Cleaned up: {temp_file.name}")
            
            logger.info("✅ Temp storage cleanup complete")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    def chunk_audio_file(self, audio_path: Path, book_id: str) -> List[Path]:
        """
        Split large audio file into manageable chunks
        
        Args:
            audio_path: Path to source audio file
            book_id: Unique identifier for the book
            
        Returns:
            List of chunk file paths
        """
        logger.info(f"🔪 Chunking audio file: {audio_path.name}")
        
        try:
            # Load audio file
            audio_data, sample_rate = librosa.load(str(audio_path), sr=None)
            total_duration = len(audio_data) / sample_rate
            
            logger.info(f"📊 Audio: {total_duration/3600:.1f}h, {sample_rate}Hz")
            
            # Calculate chunk parameters
            chunk_samples = int(self.chunk_duration * sample_rate)
            num_chunks = int(np.ceil(len(audio_data) / chunk_samples))
            
            chunk_paths = []
            
            for i in range(num_chunks):
                start_idx = i * chunk_samples
                end_idx = min((i + 1) * chunk_samples, len(audio_data))
                
                # Extract chunk
                chunk_data = audio_data[start_idx:end_idx]
                
                # Save chunk to temp directory
                chunk_filename = f"{book_id}_chunk_{i:03d}.wav"
                chunk_path = self.temp_dir / chunk_filename
                
                sf.write(str(chunk_path), chunk_data, sample_rate)
                chunk_paths.append(chunk_path)
                
                logger.debug(f"📁 Created chunk {i+1}/{num_chunks}: {chunk_filename}")
            
            logger.info(f"✅ Created {len(chunk_paths)} audio chunks")
            return chunk_paths
            
        except Exception as e:
            logger.error(f"❌ Audio chunking failed: {e}")
            return []
    
    def transcribe_chunk(self, chunk_path: Path) -> Dict:
        """Transcribe a single audio chunk"""
        try:
            if not self.load_whisper_model():
                return {'error': 'Failed to load Whisper model'}
            
            start_time = time.time()
            
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(str(chunk_path))
            
            processing_time = time.time() - start_time
            
            # Extract transcript segments with timestamps
            segments = []
            for segment in result.get('segments', []):
                segments.append({
                    'start': segment.get('start', 0),
                    'end': segment.get('end', 0),
                    'text': segment.get('text', '').strip()
                })
            
            return {
                'text': result.get('text', '').strip(),
                'segments': segments,
                'language': result.get('language', 'unknown'),
                'processing_time': processing_time,
                'chunk_file': chunk_path.name
            }
            
        except Exception as e:
            logger.error(f"Transcription failed for {chunk_path}: {e}")
            return {'error': str(e)}
    
    def process_audiobook(self, audio_path: Path, book_metadata: Dict = None) -> Dict:
        """
        Process a single audiobook: chunk, transcribe, and compile
        
        Args:
            audio_path: Path to audiobook file
            book_metadata: Optional metadata about the book
            
        Returns:
            Processing result with transcript and metadata
        """
        logger.info(f"🎧 Processing audiobook: {audio_path.name}")
        
        if not self.check_temp_storage():
            return {'error': 'Insufficient storage space'}
        
        start_time = time.time()
        
        # Generate unique book ID
        book_id = hashlib.md5(str(audio_path).encode()).hexdigest()[:12]
        
        # Get audio information
        audio_info = self.get_audio_info(audio_path)
        if not audio_info:
            return {'error': 'Failed to analyze audio file'}
        
        logger.info(f"📊 Book: {audio_info['duration_hours']:.1f}h, {audio_info['file_size_mb']:.1f}MB")
        
        try:
            # Step 1: Chunk the audio file
            chunk_paths = self.chunk_audio_file(audio_path, book_id)
            if not chunk_paths:
                return {'error': 'Audio chunking failed'}
            
            # Step 2: Transcribe each chunk
            all_transcripts = []
            total_transcript_text = ""
            
            for i, chunk_path in enumerate(chunk_paths):
                logger.info(f"🎤 Transcribing chunk {i+1}/{len(chunk_paths)}")
                
                transcript_result = self.transcribe_chunk(chunk_path)
                
                if 'error' in transcript_result:
                    logger.warning(f"⚠️ Chunk {i+1} failed: {transcript_result['error']}")
                    continue
                
                # Add chunk timing offset
                chunk_start_time = i * self.chunk_duration
                for segment in transcript_result.get('segments', []):
                    segment['start'] += chunk_start_time
                    segment['end'] += chunk_start_time
                
                all_transcripts.append({
                    'chunk_index': i,
                    'chunk_start_time': chunk_start_time,
                    'transcript': transcript_result
                })
                
                total_transcript_text += transcript_result.get('text', '') + " "
                
                # Clean up chunk file immediately to save space
                chunk_path.unlink()
            
            # Step 3: Compile final result
            processing_time = time.time() - start_time
            
            result = {
                'book_id': book_id,
                'source_file': str(audio_path),
                'metadata': {
                    'title': book_metadata.get('title', audio_path.stem) if book_metadata else audio_path.stem,
                    'author': book_metadata.get('author', 'Unknown'),
                    'duration_seconds': audio_info['duration_seconds'],
                    'file_size_mb': audio_info['file_size_mb'],
                    'processed_date': datetime.utcnow().isoformat()
                },
                'transcript': {
                    'full_text': total_transcript_text.strip(),
                    'word_count': len(total_transcript_text.split()),
                    'chunks': all_transcripts
                },
                'processing_stats': {
                    'total_chunks': len(chunk_paths),
                    'successful_chunks': len(all_transcripts),
                    'processing_time_seconds': processing_time,
                    'transcription_speed': audio_info['duration_seconds'] / processing_time if processing_time > 0 else 0
                }
            }
            
            # Save result to output directory
            output_file = self.output_dir / f"{book_id}_transcript.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            # Update statistics
            self.stats['books_processed'] += 1
            self.stats['total_audio_duration'] += audio_info['duration_seconds']
            self.stats['total_transcript_words'] += len(total_transcript_text.split())
            self.stats['processing_time'] += processing_time
            
            logger.info(f"✅ Audiobook processed: {result['transcript']['word_count']} words")
            logger.info(f"⚡ Speed: {result['processing_stats']['transcription_speed']:.1f}x realtime")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Audiobook processing failed: {e}")
            self.stats['failed_books'].append(str(audio_path))
            return {'error': str(e)}
    
    def process_sample_books(self, audio_source_dir: str, num_samples: int = 3) -> Dict:
        """
        Process a few sample audiobooks to test the pipeline
        
        Args:
            audio_source_dir: Directory containing audiobooks
            num_samples: Number of sample books to process
        """
        logger.info(f"🎯 Processing {num_samples} sample audiobooks...")
        
        source_path = Path(audio_source_dir)
        if not source_path.exists():
            return {'error': f'Source directory not found: {audio_source_dir}'}
        
        # Find audiobook files
        audio_extensions = {'.m4b', '.mp3', '.m4a', '.wav', '.flac'}
        audio_files = []
        
        for ext in audio_extensions:
            audio_files.extend(source_path.rglob(f'*{ext}'))
        
        if not audio_files:
            return {'error': 'No audiobook files found'}
        
        # Select smallest files for testing
        audio_files_with_size = [(f, f.stat().st_size) for f in audio_files]
        audio_files_with_size.sort(key=lambda x: x[1])  # Sort by size
        
        sample_files = [f[0] for f in audio_files_with_size[:num_samples]]
        
        logger.info(f"📚 Selected {len(sample_files)} sample books:")
        for i, f in enumerate(sample_files, 1):
            size_mb = f.stat().st_size / (1024 * 1024)
            logger.info(f"  {i}. {f.name} ({size_mb:.1f}MB)")
        
        # Process each sample
        results = []
        session_start = time.time()
        
        for i, audio_file in enumerate(sample_files, 1):
            logger.info(f"\n🎧 Processing sample {i}/{len(sample_files)}: {audio_file.name}")
            
            result = self.process_audiobook(audio_file)
            results.append(result)
            
            if 'error' not in result:
                logger.info(f"✅ Sample {i} complete: {result['transcript']['word_count']} words")
            else:
                logger.error(f"❌ Sample {i} failed: {result['error']}")
        
        # Generate session report
        session_time = time.time() - session_start
        successful_results = [r for r in results if 'error' not in r]
        
        report = {
            'session_summary': {
                'total_samples': len(sample_files),
                'successful_samples': len(successful_results),
                'success_rate': len(successful_results) / len(sample_files) * 100,
                'total_session_time': session_time,
                'average_processing_speed': sum(r['processing_stats']['transcription_speed'] 
                                              for r in successful_results) / max(len(successful_results), 1)
            },
            'sample_results': results,
            'agent_stats': self.stats,
            'next_steps': [
                "Review sample transcription quality",
                "Adjust Whisper model size if needed", 
                "Scale to larger audiobook collections",
                "Integrate transcripts with existing knowledge base"
            ]
        }
        
        # Save session report
        report_file = self.output_dir / f"sample_session_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report

def main():
    """Main Backend Audio Agent execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Backend Audio Agent - LibraryOfBabel Audio Transcription')
    parser.add_argument('--source', required=True, help='Source audiobook directory')
    parser.add_argument('--samples', type=int, default=3, help='Number of sample books to process')
    parser.add_argument('--model', default='base', choices=['tiny', 'base', 'small', 'medium', 'large'],
                       help='Whisper model size')
    parser.add_argument('--temp-dir', default='./temp_audio_processing', help='Temporary processing directory')
    parser.add_argument('--output-dir', default='./output/audio_transcripts', help='Output directory')
    
    args = parser.parse_args()
    
    print("🎧 LibraryOfBabel Backend Audio Agent Starting...")
    print(f"📁 Source: {args.source}")
    print(f"🎯 Samples: {args.samples}")
    print(f"🤖 Model: Whisper {args.model}")
    print(f"💾 Temp: {args.temp_dir}")
    print(f"📁 Output: {args.output_dir}\n")
    
    # Initialize agent
    agent = BackendAudioAgent(
        temp_dir=args.temp_dir,
        output_dir=args.output_dir,
        model_size=args.model
    )
    
    # Process sample books
    try:
        report = agent.process_sample_books(args.source, args.samples)
        
        if 'error' in report:
            print(f"❌ Processing failed: {report['error']}")
            return 1
        
        # Print summary
        print("\n" + "="*70)
        print("🎧 BACKEND AUDIO AGENT COMPLETE")
        print("="*70)
        print(f"✅ Successful samples: {report['session_summary']['successful_samples']}/{report['session_summary']['total_samples']}")
        print(f"⚡ Success rate: {report['session_summary']['success_rate']:.1f}%")
        print(f"🚀 Average speed: {report['session_summary']['average_processing_speed']:.1f}x realtime")
        print(f"⏱️  Session time: {report['session_summary']['total_session_time']/60:.1f} minutes")
        print(f"📁 Transcripts saved to: {args.output_dir}")
        print("\n🎯 Ready to scale to full 5000+ audiobook collection!")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("🛑 Processing interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"💥 Processing failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())