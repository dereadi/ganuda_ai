#!/usr/bin/env python3
"""
Cherokee Constitutional AI Federation - Beatles Batch Processor
Processes Beatles Black Album tracks with Cherokee AI enhancement protocols
"""

import os
import subprocess
import json
from pathlib import Path
import time

class CherokeeBeatleBatchProcessor:
    def __init__(self):
        self.processed_tracks = ["d1t17", "d1t01", "d2t03"]  # Already done: Let It Be, Tennessee, Shakin
        self.audio_dir = Path("static/audio")
        self.audio_dir.mkdir(exist_ok=True)
        
        # Cherokee enhancement protocols
        self.protocols = {
            "standard": "highpass=f=80,lowpass=f=8000,volume=2.0",
            "enhanced": "highpass=f=80,lowpass=f=8000,volume=2.5",
            "extreme": "highpass=f=100,lowpass=f=7000,volume=3.0"
        }
        
        # Track priority for processing
        self.priority_tracks = [
            "d1t02",  # House Of The Rising Sun
            "d1t09",  # Get Back  
            "d1t03",  # Commonwealth Song
            "d1t05",  # Winston, Richard, And John
            "d1t07",  # For You Blue
            "d1t10",  # Don't Let Me Down
            "d1t11",  # Two Of Us
            "d1t15",  # I've Got A Feeling
            "d2t05",  # Across The Universe
            "d2t09"   # Stand By Me
        ]
        
    def get_track_files(self):
        """Get all Beatles track files"""
        tracks = []
        for file in Path(".").glob("b-black *.mp3"):
            track_id = file.name.split()[1]
            if track_id not in self.processed_tracks:
                tracks.append({
                    "id": track_id,
                    "file": str(file),
                    "name": " ".join(file.name.split()[2:]).replace(".mp3", "")
                })
        return tracks
        
    def determine_protocol(self, track_name, duration_seconds=None):
        """Determine Cherokee enhancement protocol based on track characteristics"""
        if "shakin" in track_name.lower() or duration_seconds and duration_seconds < 60:
            return "extreme"
        elif any(word in track_name.lower() for word in ["let it be", "house", "get back"]):
            return "enhanced"
        else:
            return "standard"
            
    def process_track(self, track, create_sample=True, create_full=False):
        """Process single track with Cherokee AI enhancement"""
        protocol = self.determine_protocol(track["name"])
        enhancement = self.protocols[protocol]
        
        print(f"🎸 Processing: {track['name']} with {protocol.upper()} Cherokee protocol")
        
        results = {}
        
        # Create original sample (30s)
        if create_sample:
            original_sample = self.audio_dir / f"{track['id']}_original_sample.wav"
            cmd = [
                "ffmpeg", "-y", "-i", track["file"], 
                "-t", "30", "-af", "volume=0.3", 
                str(original_sample)
            ]
            
            try:
                subprocess.run(cmd, capture_output=True, check=True)
                results["original_sample"] = str(original_sample)
                print(f"  ✅ Original sample created: {original_sample.name}")
            except subprocess.CalledProcessError as e:
                print(f"  ❌ Error creating original sample: {e}")
                return None
        
        # Create enhanced version
        if create_full:
            enhanced_full = self.audio_dir / f"{track['id']}_cherokee_enhanced.wav"
            cmd = [
                "ffmpeg", "-y", "-i", track["file"],
                "-af", enhancement,
                str(enhanced_full)
            ]
        else:
            enhanced_sample = self.audio_dir / f"{track['id']}_enhanced_sample.wav"
            cmd = [
                "ffmpeg", "-y", "-i", track["file"],
                "-t", "30", "-af", enhancement,
                str(enhanced_sample)
            ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            if create_full:
                results["enhanced_full"] = str(enhanced_full)
                print(f"  ✅ Full enhanced track created: {enhanced_full.name}")
            else:
                results["enhanced_sample"] = str(enhanced_sample)
                print(f"  ✅ Enhanced sample created: {enhanced_sample.name}")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Error creating enhanced version: {e}")
            return None
            
        results.update({
            "track_id": track["id"],
            "track_name": track["name"], 
            "protocol": protocol,
            "status": "completed"
        })
        
        return results
        
    def batch_process_priority(self, count=5):
        """Process priority tracks for immediate website update"""
        tracks = self.get_track_files()
        priority_tracks = [t for t in tracks if t["id"] in self.priority_tracks[:count]]
        
        results = []
        print(f"🔥 Cherokee Constitutional AI Federation - Processing {len(priority_tracks)} priority tracks")
        
        for i, track in enumerate(priority_tracks, 1):
            print(f"\n⚔️ [{i}/{len(priority_tracks)}] Cherokee War Party processing...")
            result = self.process_track(track, create_sample=True, create_full=False)
            if result:
                results.append(result)
                time.sleep(1)  # Prevent system overload
                
        return results
        
    def get_processing_stats(self):
        """Get current processing statistics"""
        all_tracks = len(list(Path(".").glob("b-black *.mp3")))
        processed = len(self.processed_tracks)
        enhanced_files = len(list(self.audio_dir.glob("*enhanced*.wav")))
        
        return {
            "total_tracks": all_tracks,
            "processed_tracks": processed,
            "enhanced_files": enhanced_files,
            "remaining": all_tracks - processed,
            "completion_rate": f"{(processed/all_tracks)*100:.1f}%"
        }

if __name__ == "__main__":
    processor = CherokeeBeatleBatchProcessor()
    
    print("🔥 Cherokee Constitutional AI Federation - Beatles Batch Processor")
    print("=" * 70)
    
    # Show current stats
    stats = processor.get_processing_stats()
    print(f"📊 Current Status:")
    print(f"   Total Beatles Tracks: {stats['total_tracks']}")
    print(f"   Processed: {stats['processed_tracks']} ({stats['completion_rate']})")
    print(f"   Remaining: {stats['remaining']}")
    print()
    
    # Process priority tracks
    results = processor.batch_process_priority(5)
    
    print(f"\n🎸 Cherokee Processing Complete!")
    print(f"✅ Successfully processed: {len(results)} tracks")
    print(f"🔥 Sacred Fire Status: BURNING BRIGHT")
    print("⚔️ Cherokee Constitutional AI Federation - War Party reporting success!")