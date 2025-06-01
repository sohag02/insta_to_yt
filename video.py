import subprocess
import os
from utils import get_green_screen_data, get_png_data, get_gif_data
from config import Config

config = Config()

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


def overlay_green_screen(
    background_path: str,
    green_screen_path: str,
    output_path: str,
    start_time: float = 0,
    end_time: float = None
) -> None:
    """
    Overlays a green screen video at the center of the background video,
    even if they have different sizes but the same aspect ratio.
    """

    # Enable expression for timing interval
    if end_time is not None:
        enable_expr = f"between(t,{start_time},{end_time})"
    else:
        enable_expr = f"gte(t,{start_time})"

    # FFmpeg filter for centering the overlay
    filter_complex = (
        f"[1:v]chromakey=0x00FF00:0.3:0[fg];"
        f"[0:v][fg]overlay=(W-w)/2:(H-h)/2:enable='{enable_expr}'"
    )

    command = [
        'ffmpeg',
        '-i', background_path,
        '-i', green_screen_path,
        '-filter_complex', filter_complex,
        '-c:a', 'copy',
        output_path
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Overlay completed successfully: {output_path}")
    else:
        print(f"Error: {result.stderr}")

def overlay_image_on_video(
    video_path: str,
    image_path: str,
    output_path: str,
    start_time: float,
    end_time: float,
    width_ratio: float = 0.1,   # 10% of video width
    height_ratio: float = 0.1,  # 10% of video height
    x: str = "0",
    y: str = "0"
):
    """
    Overlays a dynamically scaled PNG image on a video for a given time interval.
    """
    if not (0 < width_ratio <= 1 and 0 < height_ratio <= 1):
        raise ValueError("Width and height ratios must be between 0 and 1.")
    if end_time <= start_time:
        raise ValueError("end_time must be greater than start_time.")

    filter_complex = (
        f"[1][0]scale2ref=w=iw*{width_ratio}:h=ih*{height_ratio}[overlay][base];"
        f"[base][overlay]overlay={x}:{y}:enable='between(t,{start_time},{end_time})'"
    )

    command = [
        "ffmpeg", "-i", video_path, "-i", image_path,
        "-filter_complex", filter_complex,
        "-c:a", "copy", output_path
    ]

    try:
        subprocess.run(command, check=True)
        print(f"Image Overlay complete. Output saved to: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error Image during overlay: {e}")

def overlay_gif_on_video(
    video_path: str,
    gif_path: str,
    output_path: str,
    start_time: float,
    end_time: float,
    width_ratio: float = 0.1,
    height_ratio: float = 0.1,
    x: str = "0",
    y: str = "0"
):
    """
    Overlays a dynamically scaled GIF on a video for a given time interval.
    """
    if not (0 < width_ratio <= 1 and 0 < height_ratio <= 1):
        raise ValueError("Width and height ratios must be between 0 and 1.")
    if end_time <= start_time:
        raise ValueError("end_time must be greater than start_time.")

    filter_complex = (
        f"[1:v]scale=iw*{width_ratio}:ih*{height_ratio}[gif_scaled];"
        f"[0:v][gif_scaled]overlay={x}:{y}:enable='between(t,{start_time},{end_time})'"
    )

    command = [
        "ffmpeg", "-i", video_path, "-ignore_loop", "0", "-i", gif_path,
        "-filter_complex", filter_complex,
        "-map", "0:a?",  # maps audio if it exists
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "copy",
        output_path
    ]

    try:
        subprocess.run(command, check=True)
        print(f"GIF overlay complete. Output saved to: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error during overlay: {e}")

def preprocess_video(video_path: str, save_path: str, filename: str):
    final_path = video_path
    if config.green_screen.do:
        for i, green_screen in enumerate(get_green_screen_data()):
            overlay_green_screen(
                final_path,
                green_screen.path,
                f'{save_path}/{filename}__green_screen_overlay_{i}.mp4',
                start_time=green_screen.start_time,
                end_time=green_screen.end_time
            )
            os.remove(final_path)
            final_path = f'{save_path}/{filename}__green_screen_overlay_{i}.mp4'

    if config.png_overlay.do:
        # x, y = position_map[config.png_overlay.position]
        for i, png_overlay in enumerate(get_png_data()):
            overlay_image_on_video(
                final_path,
                png_overlay.path,
                f'{save_path}/{filename}_png_overlay_{i}.mp4',
                start_time=png_overlay.start_time,
                end_time=png_overlay.end_time,
                x=png_overlay.x,
                y=png_overlay.y,
                width_ratio=png_overlay.width / 100,
                height_ratio=png_overlay.height / 100
            )
            os.remove(final_path)
            final_path = f'{save_path}/{filename}_png_overlay_{i}.mp4'

    if config.gif_overlay.do:
        # x, y = position_map[config.gif_overlay.position]
        for i, gif_overlay in enumerate(get_gif_data()):
            overlay_gif_on_video(
                final_path,
                gif_overlay.path,
                f'{save_path}/{filename}_gif_overlay_{i}.mp4',
                start_time=gif_overlay.start_time,
                end_time=gif_overlay.end_time,
                x=gif_overlay.x,
                y=gif_overlay.y,
                width_ratio=gif_overlay.width / 100,
                height_ratio=gif_overlay.height / 100
            )
            os.remove(final_path)
            final_path = f'{save_path}/{filename}_gif_overlay_{i}.mp4'
        

    return final_path

# Example usage:
if __name__ == "__main__":
    overlay_image_on_video(
        'base.mp4',
        'image.png',  # path to the image
        'output_png.mp4',
        start_time=2,
        end_time=8,
        x=0,  # x position of the image
        y=0,  # y position of the image
        width_ratio=0.3,  # width ratio of the image
        height_ratio=0.3  # height ratio of the image
    )

