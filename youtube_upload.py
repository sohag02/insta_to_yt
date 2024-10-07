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

# Load titles and descriptions from JSON
def load_titles():
    with open('titles.json', 'r') as file:
        data = json.load(file)
    return data['Titles']

# List to track uploaded videos
uploaded_videos = []

# Global incrementer
daily_increment = [0]

# Read username from file
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

# Get Instagram posts
def get_instagram_posts(username):
    headers = headers={
        # this is internal ID of an instegram backend app. It doesn't change often.
        "x-ig-app-id": "936619743392459",
        # use browser-like features
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
        with open('check_data.txt', 'w') as file:
            file.write(json.dumps(data))

        edges = data['data']['user']['edge_owner_to_timeline_media']['edges']
        for edge in edges:
            node = edge['node']
            if node['is_video']:
                post_info = {
                    'url': f"https://www.instagram.com/p/{node['shortcode']}/",
                    'description': node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', ''),
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

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, scopes)
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
    try : response = request.execute()
    except googleapiclient.errors.HttpError as e : 
        print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")
        response = 'error'
    return response

# Handle video uploads
def handle_video_uploads():
    global daily_increment, uploaded_videos
    username = read_username()
    videos = get_instagram_posts(username)
    youtube = get_authenticated_service()
    download_directory = create_directory(username)

    video_indices = [0, 1, -2 - daily_increment[0], -1 - daily_increment[0]]
    selected_videos = [videos[i] for i in video_indices if i < len(videos) and i >= -len(videos)]

    # Create an instance of Instaloader
    L = instaloader.Instaloader()
    USERNAME = 'mad.hav1236'
    PASSWORD = 'bigB_123567'
    L.login(USERNAME, PASSWORD)

    for video in selected_videos:
        shortcode = video['url'].split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=post.owner_username)
        
        video_name = f"{datetime.fromtimestamp(video['date'],tz=timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')}_UTC.mp4"
        file_path = os.path.join(download_directory, video_name)

        titles = load_titles()
        if video_name not in uploaded_videos:
            index = random.randint(0, len(titles) - 1)
            title = titles[index] + '#shorts'
            description = title + '\n' + video['description']
            response = upload_video(youtube, file_path, title, description, tags=["money", "trading", "ebook"])
            if 'id' in response:  # Assuming a successful upload returns an 'id'
                uploaded_videos.append(video_name)
                print(f"Uploaded video: {title} - Response: {response}")

    remove_directory(download_directory)
    daily_increment[0] += 2  # Increment for next day

if __name__ == "__main__":
    # Scheduling the script
    print('Script Starting')
    schedule.every().day.at("20:49").do(handle_video_uploads)
    while True:
        schedule.run_pending()
        time.sleep(1)
