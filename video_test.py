from video import improve_video_quality

input_path = "videos/test.mp4"

output_path = improve_video_quality(input_path, input_path)
print(f"Video quality improved and saved to {output_path}")