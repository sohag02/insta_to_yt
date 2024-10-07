import instaloader
import requests
import json
import os
import shutil
import googleapiclient.discovery
import google_auth_oauthlib.flow
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import schedule
import time
import random
import googleapiclient.errors
from datetime import datetime, timezone, timedelta

# Define the Scrapfly API key and proxy URL
SCRAPFLY_API_KEY = "scp-live-0793983fd35e43cebd278a24def8ece4"
PROXY_URL = f"https://proxy.scrapfly.io/?key={SCRAPFLY_API_KEY}"

# Load titles and descriptions from a JSON file
def load_titles():
    with open('titles.json', 'r') as file:
        data = json.load(file)
    return data['Titles']

# List to track uploaded videos
uploaded_videos = []

# Global incrementer
daily_increment = [0]

# Read Instagram username from file
def read_username():
    with open('username.txt', 'r') as file:
        return file.readline().strip()

# Create directory for downloads
def create_directory(username):
    directory = f"./{username}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

# Remove directory and its contents
def remove_directory(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)

# Get Instagram posts using proxy (via Scrapfly)
def get_instagram_posts_with_proxy(username):
    headers = {
        "x-ig-app-id": "936619743392459",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "*/*",
    }

    # URL to get user profile info
    user_info_url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
    response = requests.get(user_info_url, headers=headers, proxies={"https": PROXY_URL})
    
    if response.status_code == 200:
        user_data = response.json()
        user_id = user_data['data']['user']['id']
        total_posts = user_data['data']['user']['edge_owner_to_timeline_media']['count']

        # GraphQL API request to get post details
        graphql_url = 'https://www.instagram.com/graphql/query/'
        query_hash = 'e769aa130647d2354c40ea6a439bfc08'
        variables = {
            "id": user_id,
            "first": 12,
            "after": None
        }

        posts = []
        while len(posts) < total_posts:
            params = {
                'query_hash': query_hash,
                'variables': json.dumps(variables)
            }

            # Send GraphQL request using proxy
            response = requests.get(graphql_url, headers=headers, params=params, proxies={"https": PROXY_URL})
            data = response.json()

            # Extract post data
            edges = data['data']['user']['edge_owner_to_timeline_media']['edges']
            for edge in edges:
                node = edge['node']
                if node['is_video']:
                    post_info = {
                        'url': f"https://www.instagram.com/p/{node['shortcode']}/",
                        'title': node.get('title', ''),
                        'date': node.get('timestamp', node.get('taken_at_timestamp')),
                        'description': node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', ''),
                        'video_url': node['video_url']
                    }
                    posts.append(post_info)

            # Check if there are more pages of posts
            page_info = data['data']['user']['edge_owner_to_timeline_media']['page_info']
            if not page_info['has_next_page']:
                break
            variables['after'] = page_info['end_cursor']

        return posts

    else:
        print(f"Failed to retrieve data: {response.status_code}")
        return None

# Fetch Instagram posts (without proxy)
def get_instagram_posts(username):
    headers = {
        "x-ig-app-id": "936619743392459",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "*/*",
    }
    
    user_info_url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
    response = requests.get(user_info_url, headers=headers)
    user_data = response.json()
    user_id = user_data['data']['user']['id']
    total_posts = user_data['data']['user']['edge_owner_to_timeline_media']['count']

    graphql_url = 'https://www.instagram.com/graphql/query/'
    query_hash = 'e769aa130647d2354c40ea6a439bfc08'
    variables = {"id": user_id, "first": 12, "after": None}

    posts = []
    while len(posts) < total_posts:
        params = {'query_hash': query_hash, 'variables': json.dumps(variables)}
        response = requests.get(graphql_url, headers=headers, params=params)
        data = response.json()
        edges = data['data']['user']['edge_owner_to_timeline_media']['edges']
        
        # Extract video post details
        for edge in edges:
            node = edge['node']
            if node['is_video']:
                description = node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', 'Forex trading for the beginners earn money while learning')
                post_info = {
                    'url': f"https://www.instagram.com/p/{node['shortcode']}/",
                    'description': description,
                    'date': node.get('timestamp', node.get('taken_at_timestamp')),
                    'video_url': node['video_url']
                }
                posts.append(post_info)

        page_info = data['data']['user']['edge_owner_to_timeline_media']['page_info']
        if not page_info['has_next_page']:
            break
        variables['after'] = page_info['end_cursor']
        time.sleep(5)
    return posts

# Store Instagram posts in the global videos list
videos = []
def store_posts():
    global videos
    username = read_username()
    videos.extend(get_instagram_posts(username))

# Authenticate YouTube API
def get_authenticated_service():
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "client_secrets.json"
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    token_file = "token.json"
    
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes=scopes)
    else:
        creds = None

    # Check and refresh token if expired
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
            creds = flow.run_local_server(port=0)
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    return googleapiclient.discovery.build(api_service_name, api_version, credentials=creds)

# Upload video to YouTube
def upload_video(youtube, file_path, title, description, category_id="27", tags=None, privacy_status="unlisted"):
    body = {
        "snippet": {
            "categoryId": category_id,
            "title": title,
            "description": description,
            "tags": tags or []
        },
        "status": {
            "privacyStatus": privacy_status
        }
    }
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True)
    )
    try:
        response = request.execute()
    except googleapiclient.errors.HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")
        response = 'error'
    return response

# Upload old videos to YouTube
def old_videos_uploads():
    store_posts()
    
    with open('daily_increment.txt', 'r') as file:
        number = int(file.read().strip())

    global uploaded_videos, videos
    username = read_username()
    youtube = get_authenticated_service()
    download_directory = create_directory(username)

    video_indices = [-2 - number, -1 - number]
    selected_videos = [videos[i] for i in video_indices if i < len(videos) and i >= -len(videos)]

    # Download videos using Instaloader
    L = instaloader.Instaloader()

    for video in selected_videos:
        shortcode = video['url'].split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=post.owner_username)
        
        video_name = f"{datetime.fromtimestamp(video['date'], tz=timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')}_UTC.mp4"
        file_path = os.path.join(download_directory, video_name)

        titles = load_titles()
        if video_name not in uploaded_videos:
            index = random.randint(0, len(titles) - 1)
            title = titles[index] + '#shorts'
            description = title + '\n' + video['description']
            response = upload_video(youtube, file_path, title, description, tags=["money", "trading", "ebook"])
            if 'id' in response:
                uploaded_videos.append(video_name)
                print(f"Uploaded video: {title} - Response: {response}")

    remove_directory(download_directory)
    number += 2
    with open('daily_increment.txt', 'w') as file:
        file.write(str(number))

# Upload live videos to YouTube
def live_videos_upload():
    global daily_increment, uploaded_videos, videos
    youtube = get_authenticated_service()
    username = read_username()
    download_directory = create_directory(username)
    one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
    live_videos = [video for video in videos if datetime.fromtimestamp(video['date'], tz=timezone.utc) > one_day_ago]

    L = instaloader.Instaloader()

    for video in live_videos:
        shortcode = video['url'].split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=post.owner_username)
        
        video_name = f"{datetime.fromtimestamp(video['date'], tz=timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')}_UTC.mp4"
        file_path = os.path.join(download_directory, video_name)

        titles = load_titles()
        if video_name not in uploaded_videos:
            index = random.randint(0, len(titles) - 1)
            title = titles[index] + '#shorts'
            description = title + '\n' + video['description']
            response = upload_video(youtube, file_path, title, description, tags=["money", "trading", "ebook"])
            if 'id' in response:
                uploaded_videos.append(video_name)
                print(f"Uploaded video: {title} - Response: {response}")
    
    remove_directory(download_directory)
    videos.clear()
    print(len(videos))

# Read schedule times from file
def read_schedule_file(file_path="schedule.txt"):
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the absolute path of the schedule file
    abs_file_path = os.path.join(script_dir, file_path)
    
    if not os.path.exists(abs_file_path):
        print(f"Error: The file '{abs_file_path}' was not found. Please create it with two times, one for live video uploads and one for old video uploads.")
        return []
    
    with open(abs_file_path, 'r') as file:
        times = [line.strip() for line in file.readlines() if line.strip()]
    return times

# Schedule jobs based on times from file
def schedule_jobs_from_file():
    times = read_schedule_file()
    if len(times) >= 2:
        schedule.every().day.at(times[0]).do(live_videos_upload)
        schedule.every().day.at(times[1]).do(old_videos_uploads)
        print(f"Scheduled jobs for times: {times}")
    else:
        print("Error: Schedule file does not have enough times. Please provide two times in 'schedule.txt'.")

# Main loop to schedule tasks
if __name__ == "__main__":
    schedule_jobs_from_file()  # Schedule jobs based on file contents
    while True:
        schedule.run_pending()
        time.sleep(1)
