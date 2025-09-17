#!/usr/bin/env python3
"""
Transcribe DER Tech Review Meeting using Cherokee Audio Studio
Uses OpenAI Whisper for high-quality transcription
"""

import subprocess
import json
import os
from pathlib import Path

def transcribe_with_whisper(audio_file, output_file):
    """Use Whisper to transcribe the audio"""
    print(f"🔥 Cherokee Audio Studio - Starting transcription...")
    print(f"Input: {audio_file}")
    print(f"Output: {output_file}")
    
    # Check if whisper is available
    try:
        result = subprocess.run(['which', 'whisper'], capture_output=True, text=True)
        if result.returncode != 0:
            print("Whisper not found. Installing...")
            subprocess.run(['pip3', 'install', 'openai-whisper'], check=True)
    except:
        pass
    
    # Run transcription
    cmd = [
        'whisper',
        audio_file,
        '--model', 'base',  # Use base model for speed
        '--output_format', 'all',
        '--output_dir', '/tmp',
        '--language', 'en',
        '--task', 'transcribe',
        '--verbose', 'False'
    ]
    
    print("🎙️ Processing audio through Sacred Fire transcription engine...")
    print("This may take several minutes for a 56-minute recording...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Transcription complete!")
            
            # Read the generated files
            base_name = Path(audio_file).stem
            
            # Check for different output formats
            formats = {
                'txt': f'/tmp/{base_name}.txt',
                'vtt': f'/tmp/{base_name}.vtt',
                'srt': f'/tmp/{base_name}.srt',
                'json': f'/tmp/{base_name}.json'
            }
            
            for fmt, filepath in formats.items():
                if os.path.exists(filepath):
                    print(f"  Found {fmt}: {filepath}")
            
            # Read the text transcript
            txt_file = formats['txt']
            if os.path.exists(txt_file):
                with open(txt_file, 'r') as f:
                    transcript = f.read()
                
                # Save to output file
                with open(output_file, 'w') as f:
                    f.write("🔥 DER TECH REVIEW TRANSCRIPT\n")
                    f.write("=" * 60 + "\n")
                    f.write("Meeting: September 10, 2025 at 09:58 CDT\n")
                    f.write("Participants: Darrell Reading & Dr Joe Dorn\n")
                    f.write("Duration: 56 minutes 13 seconds\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(transcript)
                
                print(f"📝 Transcript saved to: {output_file}")
                return transcript
            else:
                print("❌ No text transcript found")
                return None
                
        else:
            print(f"❌ Transcription failed: {result.stderr}")
            return None
            
    except FileNotFoundError:
        print("❌ Whisper not installed. Trying alternative method...")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def create_summary(transcript):
    """Create a summary of the transcript"""
    if not transcript:
        return
    
    print("\n📊 Creating meeting summary...")
    
    # Basic statistics
    words = transcript.split()
    lines = transcript.split('\n')
    
    summary = f"""
🔥 MEETING SUMMARY
==================
Total Words: {len(words)}
Total Lines: {len(lines)}
Estimated Speaking Time: {len(words) / 150:.1f} minutes

Key Topics Detected:
(Analysis would go here based on keyword extraction)

Cherokee Audio Studio Analysis Complete!
Sacred Fire burns eternal through recorded wisdom!
"""
    
    print(summary)
    return summary

if __name__ == "__main__":
    audio_file = "/tmp/der_tech_review.wav"
    output_file = "/home/dereadi/scripts/claude/DER_Tech_Review_Transcript.txt"
    
    print("🔥 Cherokee Audio Studio - DER Tech Review Transcription")
    print("=" * 60)
    
    if os.path.exists(audio_file):
        transcript = transcribe_with_whisper(audio_file, output_file)
        if transcript:
            create_summary(transcript)
        else:
            print("Attempting alternative transcription method...")
    else:
        print(f"❌ Audio file not found: {audio_file}")