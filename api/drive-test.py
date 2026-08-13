from http.server import BaseHTTPRequestHandler
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            credentials = Credentials(
                token=None,
                refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.environ["GOOGLE_CLIENT_ID"],
                client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
                scopes=["https://www.googleapis.com/auth/drive"],
            )

            drive = build(
                "drive",
                "v3",
                credentials=credentials,
                cache_discovery=False,
            )

            folder_id = os.environ["GOOGLE_DRIVE_FOLDER_ID"]

            result = drive.files().get(
                fileId=folder_id,
                fields="id,name,mimeType",
            ).execute()

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8",
            )
            self.end_headers()

            response = (
                '{"success":true,'
                '"message":"Google Drive connection works",'
                '"folder_name":"' + result["name"] + '",'
                '"folder_id":"' + result["id"] + '"}'
            )

            self.wfile.write(response.encode())

        except Exception as e:
            self.send_response(500)
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8",
            )
            self.end_headers()

            response = (
                '{"success":false,'
                '"error":"' + str(e).replace('"', '\\"') + '"}'
            )

            self.wfile.write(response.encode())
