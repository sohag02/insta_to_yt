import subprocess
import os

def improve_video_quality(input_path: str, output_path: str):
    output_path = add_processed_suffix(output_path)
    command = [
        '.local/bin/ffmpeg',             # Path to the ffmpeg executable
        '-i', input_path,                # Input file
        '-vf', 'hqdn3d=3.0:2.0:6.0:4.5,unsharp=5:5:1.0',  # Denoise and sharpen
        '-c:v', 'libx264',               # Video codec (H.264)
        '-b:v', '3M',                    # Video bitrate (3 Mbps for good quality)
        '-c:a', 'aac',                   # Audio codec (AAC)
        '-b:a', '192k',                  # Audio bitrate (192 kbps)
        '-movflags', '+faststart',       # Fast streaming
        '-preset', 'slow',               # Better quality at the cost of encoding speed
        '-crf', '20',                    # Constant rate factor (lower means better quality)
        '-y',                            # Overwrite output if exists
        output_path
    ]

    try:
        subprocess.run(command, check=True)
        print(f"Video quality improved and saved to {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error during video processing: {e}")

    return output_path

def add_processed_suffix(filename: str) -> str:
    name, ext = os.path.splitext(filename)
    return f"{name}_processed{ext}"
