import json
from googleapiclient.http import MediaFileUpload
import google_auth_oauthlib.flow
import googleapiclient.discovery
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os

def get_authenticated_service(generate_session=False):
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
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, scopes
            )
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as token:
            token.write(creds.to_json())
    if generate_session:
        return creds
    return googleapiclient.discovery.build(
        api_service_name, api_version, credentials=creds
    )


def upload_video(
    youtube,
    file_path,
    title,
    description,
    category_id="27",
    tags=None,
    privacy_status="unlisted",
):
    body = {
        "snippet": {
            "categoryId": category_id,
            "title": title,
            "description": description,
            "tags": tags or [],
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        },
    }
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True),
    )
    try:
        response = request.execute()
    except googleapiclient.errors.HttpError as e:
        code = e.resp.status
        if code == 403:
            dict_data = json.loads(e.content.decode('utf-8'))
            print(f"An HTTP error {e.resp.status} occurred: {dict_data['error']['message']}")
            response = "error"
        else:
            raise
    return response
