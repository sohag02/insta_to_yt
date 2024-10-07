import requests

def download_video(url, filename):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, stream=True, headers=headers, timeout=100)

    if response.status_code == 200:
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        print(f"Downloaded {filename}")
    else:
        print(f"Failed to download video. Status code: {response.status_code}")

# Example usage
video_url = 'https://www.instagram.com/p/C9hpQi9trOF/'
filename = "video.mp4"
download_video(video_url, filename)
