import requests
import json
import os
from datetime import datetime,timezone,timedelta

def get_instagram_posts(username):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'x-ig-app-id': '936619743392459'
    }

    # Get user info to find out the total number of posts
    user_info_url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
    response = requests.get(user_info_url, headers=headers)
    user_data = response.json()
    user_id = user_data['data']['user']['id']
    total_posts = user_data['data']['user']['edge_owner_to_timeline_media']['count']

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
        response = requests.get(graphql_url, headers=headers, params=params)
        data = response.json()

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

        page_info = data['data']['user']['edge_owner_to_timeline_media']['page_info']
        if not page_info['has_next_page']:
            break
        variables['after'] = page_info['end_cursor']

    return posts

def download_video(url, filename):
    response = requests.get(url, stream=True)
    with open(filename, 'wb') as file:
        for chunk in response.iter_content(chunk_size=1):
            if chunk:
                file.write(chunk)
    print(f"Downloaded {filename}")
    
username = 'perfect_trading_ebook'
post_links = get_instagram_posts(username)
one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
live_videos = [video for video in post_links if datetime.fromtimestamp(video['date'], tz=timezone.utc) > one_day_ago]
for post in live_videos:
    print(post['date'])
    print(post['video_url'])
    print(post['description'])
if len(post_links) >= 14:
    video_info = post_links[25]  # Index 13 corresponds to the 14th post
    video_url = 'https://www.instagram.com/p/C-Ai8Cktb4g/'
    filename = "14th_video.mp4"
    download_video(video_url, filename)
    print(f"URL: {video_info['url']}")
    print(f"Title: {video_info['title']}")
    print(f"Description: {video_info['description']}")
else:
    print("Less than 14 video posts available.")
