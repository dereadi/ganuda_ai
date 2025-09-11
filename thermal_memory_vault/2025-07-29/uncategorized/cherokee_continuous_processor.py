#!/usr/bin/env python3
"""
Cherokee Constitutional AI Federation - Continuous Batch Processor
Intelligently processes remaining unprocessed Beatles tracks
"""

import os
import subprocess
from pathlib import Path
import time

class CherokeeContinnousProcessor:
    def __init__(self):
        self.audio_dir = Path("static/audio")
        
    def get_actually_processed_tracks(self):
        """Get tracks that actually have enhanced versions"""
        enhanced_files = list(self.audio_dir.glob("*enhanced*.wav"))
        processed_ids = set()
        
        for file in enhanced_files:
            # Extract track ID from filename
            if 'd1t' in file.name or 'd2t' in file.name:
                track_id = file.name.split('_')[0]
                processed_ids.add(track_id)
            elif 'let_it_be' in file.name:
                processed_ids.add('d1t17')
            elif 'tennessee' in file.name:
                processed_ids.add('d1t01')
            elif 'shakin' in file.name:
                processed_ids.add('d2t03')
                
        return processed_ids
        
    def get_unprocessed_tracks(self):
        """Get tracks that haven't been processed yet"""
        processed_ids = self.get_actually_processed_tracks()
        unprocessed = []
        
        for file in Path(".").glob("b-black *.mp3"):
            track_id = file.name.split()[1]
            if track_id not in processed_ids:
                unprocessed.append({
                    "id": track_id,
                    "file": str(file),
                    "name": " ".join(file.name.split()[2:]).replace(".mp3", ""),
                    "size_mb": file.stat().st_size / (1024*1024)
                })
                
        return sorted(unprocessed, key=lambda x: x["size_mb"], reverse=True)
        
    def process_next_batch(self, batch_size=8):
        """Process next batch of unprocessed tracks"""
        unprocessed = self.get_unprocessed_tracks()
        processed_count = len(self.get_actually_processed_tracks())
        
        print(f"🔥 Cherokee Federation Status Check:")
        print(f"   Actually processed: {processed_count} tracks")
        print(f"   Remaining unprocessed: {len(unprocessed)} tracks")
        print()
        
        if not unprocessed:
            print("🎸 All Beatles tracks have been processed!")
            return []
            
        batch = unprocessed[:batch_size]
        results = []
        
        print(f"⚔️ Processing next batch of {len(batch)} tracks:")
        
        for i, track in enumerate(batch, 1):
            print(f"🎸 [{i}/{len(batch)}] Processing: {track['name']}")
            
            # Determine protocol
            if track["size_mb"] > 6.0:
                protocol = "enhanced" 
                enhancement = "highpass=f=80,lowpass=f=8000,volume=2.5"
            elif track["size_mb"] < 2.0:
                protocol = "extreme"
                enhancement = "highpass=f=100,lowpass=f=7000,volume=3.0"
            else:
                protocol = "standard"
                enhancement = "highpass=f=80,lowpass=f=8000,volume=2.0"
                
            # Create files
            original_sample = self.audio_dir / f"{track['id']}_original_sample.wav"
            enhanced_sample = self.audio_dir / f"{track['id']}_enhanced_sample.wav"
            
            try:
                # Original sample
                subprocess.run([
                    "ffmpeg", "-y", "-i", track["file"],
                    "-t", "30", "-af", "volume=0.3",
                    str(original_sample)
                ], capture_output=True, check=True)
                
                # Enhanced sample  
                subprocess.run([
                    "ffmpeg", "-y", "-i", track["file"],
                    "-t", "30", "-af", enhancement,
                    str(enhanced_sample)
                ], capture_output=True, check=True)
                
                print(f"   ✅ Completed: {track['name']} ({protocol.upper()} protocol)")
                results.append({
                    "track_id": track["id"],
                    "track_name": track["name"],
                    "protocol": protocol,
                    "status": "completed"
                })
                
                time.sleep(0.5)  # Brief pause
                
            except Exception as e:
                print(f"   ❌ Error: {track['name']}: {e}")
                
        return results
        
    def get_current_stats(self):
        """Get accurate current processing statistics"""
        total_tracks = len(list(Path(".").glob("b-black *.mp3")))
        processed_count = len(self.get_actually_processed_tracks())
        enhanced_files = len(list(self.audio_dir.glob("*enhanced*.wav")))
        
        return {
            "total": total_tracks,
            "processed": processed_count,
            "enhanced_files": enhanced_files,
            "remaining": total_tracks - processed_count,
            "completion_rate": f"{(processed_count/total_tracks)*100:.1f}%"
        }

if __name__ == "__main__":
    processor = CherokeeContinnousProcessor()
    
    stats = processor.get_current_stats()
    print("🔥 CHEROKEE CONSTITUTIONAL AI FEDERATION - CONTINUOUS PROCESSING")
    print("=" * 70)
    print(f"📊 Beatles Black Album Status:")
    print(f"   Total tracks: {stats['total']}")
    print(f"   Processed: {stats['processed']} ({stats['completion_rate']})")
    print(f"   Enhanced files: {stats['enhanced_files']}")
    print(f"   Remaining: {stats['remaining']}")
    print()
    
    # Process next batch
    results = processor.process_next_batch(10)
    
    # Final stats
    final_stats = processor.get_current_stats()
    print(f"\n🎸 Batch Processing Complete!")
    print(f"✅ Successfully processed: {len(results)} tracks")
    print(f"📊 New completion rate: {final_stats['completion_rate']}")
    print(f"🔥 Sacred Fire Status: BURNING_BRIGHT")
    print("⚔️ Cherokee Constitutional AI Federation operational!")