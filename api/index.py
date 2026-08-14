from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import os
import json
import tempfile
import subprocess


def json_response(handler, status, data):
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.end_headers()
    handler.wfile.write(
        json.dumps(data, ensure_ascii=False).encode("utf-8")
    )


def get_drive_service():
    credentials = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        scopes=["https://www.googleapis.com/auth/drive"],
    )

    return build(
        "drive",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)

            # Health check
            if parsed.path == "/" or parsed.path == "/api":
                json_response(
                    self,
                    200,
                    {
                        "success": True,
                        "message": "YouTube Downloader API is running"
                    },
                )
                return

            # Download endpoint
            if parsed.path == "/api/download":

                if "url" not in query:
                    json_response(
                        self,
                        400,
                        {
                            "success": False,
                            "error": "Missing YouTube URL"
                        },
                    )
                    return

                youtube_url = query["url"][0].strip()

                if not youtube_url:
                    json_response(
                        self,
                        400,
                        {
                            "success": False,
                            "error": "YouTube URL is empty"
                        },
                    )
                    return

                # Temporary directory available during the function execution
                temp_dir = tempfile.mkdtemp()
                output_template = os.path.join(
                    temp_dir,
                    "%(title)s.%(ext)s"
                )

                # Download video
                command = [
                    "yt-dlp",
                    "--no-playlist",
                    "-f",
                    "best[ext=mp4]/best",
                    "-o",
                    output_template,
                    youtube_url,
                ]

                process = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=8,
                )

                if process.returncode != 0:
                    raise Exception(
                        "YouTube download failed: "
                        + process.stderr[-1500:]
                    )

                downloaded_file = None

                for filename in os.listdir(temp_dir):
                    path = os.path.join(temp_dir, filename)

                    if os.path.isfile(path):
                        downloaded_file = path
                        break

                if not downloaded_file:
                    raise Exception("Downloaded file was not found")

                # Connect to Google Drive
                drive = get_drive_service()

                folder_id = os.environ["GOOGLE_DRIVE_FOLDER_ID"]

                file_name = os.path.basename(downloaded_file)

                metadata = {
                    "name": file_name,
                    "parents": [folder_id],
                }

                media = MediaFileUpload(
                    downloaded_file,
                    mimetype="video/mp4",
                    resumable=False,
                )

                uploaded = drive.files().create(
                    body=metadata,
                    media_body=media,
                    fields="id,name,webViewLink,webContentLink",
                ).execute()

                json_response(
                    self,
                    200,
                    {
                        "success": True,
                        "message": "Video downloaded and uploaded to Google Drive",
                        "file_name": uploaded.get("name"),
                        "file_id": uploaded.get("id"),
                        "web_view_link": uploaded.get("webViewLink"),
                        "download_link": uploaded.get("webContentLink"),
                    },
                )
                return

            json_response(
                self,
                404,
                {
                    "success": False,
                    "error": "Endpoint not found"
                },
            )

        except subprocess.TimeoutExpired:
            json_response(
                self,
                504,
                {
                    "success": False,
                    "error": "Download timed out. Try a smaller video."
                },
            )

        except Exception as e:
            json_response(
                self,
                500,
                {
                    "success": False,
                    "error": str(e)
                },
            )
