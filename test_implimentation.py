import os
import instaloader

def create_directory(username):
    # Safe directory name that removes any OS-unfriendly characters
    safe_username = "".join([c for c in username if c.isalnum() or c in "_- "]).rstrip()
    directory = os.path.join(".", safe_username)  # Use relative path correctly
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def download_video(video_url, directory, filename):
    local_filename = os.path.join(directory, filename)
    L = instaloader.Instaloader()
    L.download_post(video_url, local_filename)
    return local_filename

directory = create_directory('perfect_trading_ebook')
print("Directory created:", directory)
filename = download_video('https://www.instagram.com/p/C-Ai8Cktb4g/', directory, 'aa.mp4')
print("File downloaded as:", filename)
