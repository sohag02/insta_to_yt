import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

def get_authenticated_service():
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "clients_secret.json"
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

def upload_video(youtube, file_path, title, description, category_id, tags, channel_id, privacy_status):
    body = {
        "snippet": {
            "categoryId": category_id,
            "title": title,
            "description": description,
            "tags": tags,
            "channelId": channel_id
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True)
    )
    response = request.execute()
    return response

def main():
    youtube = get_authenticated_service()
    file_path = "14th_video.mp4"
    title = "Exploring Smart Trading Strategies"
    description = "Dive into smart trading strategies that can help boost your financial growth. Learn tips and tricks for effective trading!"
    category_id = "27"
    tags = ["money", "trading"]
    channel_id = "UCfXJNwgGKDieGJvGLc98ZjA"
    privacy_status = "unlisted"
    
    try:
        print("Uploading file...")
        response = upload_video(youtube, file_path, title, description, category_id, tags, channel_id, privacy_status)
        print("Upload successful.")
        print(response)
    except googleapiclient.errors.HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")
    except googleapiclient.errors.ResumableUploadError as e:
        print(f"A resumable upload error occurred: {e.resp.status}\n{e.content}")
    
    if 'error' in response:
        print("Error uploading video:", response['error']['message'])
    else:
        print("Upload successful.")

if __name__ == "__main__":
    main()
