#!/usr/bin/env python3
"""
Dual-GPU Whisper Transcription
Split audio file and process on both GPUs simultaneously
"""

import subprocess
import os
from pathlib import Path
import json
import sys

def split_audio(input_file, output_dir):
    """Split audio file into two halves"""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    # Get duration
    duration_cmd = [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', str(input_file)
    ]
    duration = float(subprocess.check_output(duration_cmd).decode().strip())
    half_duration = duration / 2

    print(f"📊 Total duration: {duration:.1f}s, splitting at {half_duration:.1f}s")

    # Split into two parts
    part1 = output_dir / "part1.mp4"
    part2 = output_dir / "part2.mp4"

    # First half
    subprocess.run([
        'ffmpeg', '-i', str(input_file),
        '-t', str(half_duration),
        '-c', 'copy', '-y', str(part1)
    ], check=True, capture_output=True)

    # Second half
    subprocess.run([
        'ffmpeg', '-i', str(input_file),
        '-ss', str(half_duration),
        '-c', 'copy', '-y', str(part2)
    ], check=True, capture_output=True)

    print(f"✅ Split complete: {part1.name}, {part2.name}")
    return part1, part2

def transcribe_on_gpu(audio_file, gpu_id, model='large'):
    """Transcribe audio file on specific GPU"""

    whisper_path = "/home/dereadi/cherokee_venv/bin/whisper"
    output_dir = Path(f"/tmp/bootleg_transcription/gpu{gpu_id}")
    output_dir.mkdir(exist_ok=True, parents=True)

    env = os.environ.copy()
    env['CUDA_VISIBLE_DEVICES'] = str(gpu_id)

    cmd = [
        whisper_path,
        str(audio_file),
        '--model', model,
        '--task', 'transcribe',
        '--language', 'en',
        '--temperature', '0.0',
        '--beam_size', '5',
        '--best_of', '5',
        '--output_format', 'json',
        '--output_dir', str(output_dir),
        '--fp16', 'True',
        '--word_timestamps', 'True'
    ]

    print(f"🎤 GPU {gpu_id}: Starting transcription of {audio_file.name}...")

    result = subprocess.run(cmd, env=env, capture_output=True, text=True)

    # Read result
    json_file = output_dir / f"{audio_file.stem}.json"
    if json_file.exists():
        with open(json_file, 'r') as f:
            data = json.load(f)
            print(f"✅ GPU {gpu_id}: Complete! ({len(data.get('text', ''))} chars)")
            return data
    else:
        print(f"❌ GPU {gpu_id}: Failed!")
        return None

def merge_transcripts(part1_data, part2_data):
    """Merge two transcript parts"""
    if not part1_data or not part2_data:
        return None

    # Combine texts
    full_text = part1_data.get('text', '') + ' ' + part2_data.get('text', '')

    # Combine segments with adjusted timestamps for part 2
    segments = part1_data.get('segments', [])
    part1_duration = segments[-1]['end'] if segments else 0

    part2_segments = part2_data.get('segments', [])
    for seg in part2_segments:
        seg['start'] += part1_duration
        seg['end'] += part1_duration
        segments.append(seg)

    return {
        'text': full_text,
        'segments': segments,
        'language': 'en'
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 whisper_dual_gpu_transcribe.py <video_file> [model]")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    model = sys.argv[2] if len(sys.argv) > 2 else 'large'

    if not input_file.exists():
        print(f"❌ File not found: {input_file}")
        sys.exit(1)

    print(f"🔥 DUAL-GPU WHISPER TRANSCRIPTION")
    print(f"📀 Input: {input_file}")
    print(f"🤖 Model: {model}")
    print("=" * 60)

    # Split audio
    split_dir = Path("/tmp/bootleg_transcription/split")
    part1, part2 = split_audio(input_file, split_dir)

    # Launch parallel transcription on both GPUs
    import multiprocessing

    with multiprocessing.Pool(processes=2) as pool:
        results = [
            pool.apply_async(transcribe_on_gpu, (part1, 0, model)),
            pool.apply_async(transcribe_on_gpu, (part2, 1, model))
        ]

        print("\n🚀 Processing on both GPUs simultaneously...")

        part1_result = results[0].get()
        part2_result = results[1].get()

    # Merge results
    print("\n🔗 Merging transcripts...")
    final_data = merge_transcripts(part1_result, part2_result)

    if final_data:
        # Save merged transcript
        output_file = input_file.parent / f"{input_file.stem}_transcript.txt"
        with open(output_file, 'w') as f:
            f.write(final_data['text'])

        # Save JSON
        json_file = input_file.parent / f"{input_file.stem}_transcript.json"
        with open(json_file, 'w') as f:
            json.dump(final_data, f, indent=2)

        print(f"\n✅ TRANSCRIPTION COMPLETE")
        print(f"📄 Text: {output_file}")
        print(f"📄 JSON: {json_file}")
        print(f"📏 Length: {len(final_data['text'])} characters")
        print(f"📝 Segments: {len(final_data['segments'])}")
        print(f"\n🔥 The Sacred Fire burns twice as bright with dual GPUs!")
    else:
        print("\n❌ Transcription failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
