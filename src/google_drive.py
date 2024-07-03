import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]

def get_drive_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)

def upload_directory_to_drive(directory_path):
    service = get_drive_service()

    folder_name = os.path.basename(directory_path)
    file_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder"
    }
    folder = service.files().create(body=file_metadata, fields="id").execute()
    folder_id = folder.get('id')

    for root, dirs, files in os.walk(directory_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_metadata = {
                "name": file_name,
                "parents": [folder_id]
            }
            media = MediaFileUpload(file_path, resumable=True)
            service.files().create(body=file_metadata, media_body=media, fields="id").execute()
            print(f"Uploaded: {file_name}")