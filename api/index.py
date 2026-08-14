from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import os
import json
import tempfile
import yt_dlp


def send_json(handler, status, data):
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

            # -----------------------------
            # Health check
            # -----------------------------
            if parsed.path in ["/", "/api"]:
                send_json(
                    self,
                    200,
                    {
                        "success": True,
                        "message": "YouTube Downloader API is running"
                    }
                )
                return

            # -----------------------------
            # Download endpoint
            # -----------------------------
            if parsed.path == "/api/download":

                if "url" not in query:
                    send_json(
                        self,
                        400,
                        {
                            "success": False,
                            "error": "Missing YouTube URL"
                        }
                    )
                    return

                youtube_url = query["url"][0].strip()

                if not youtube_url:
                    send_json(
                        self,
                        400,
                        {
                            "success": False,
                            "error": "YouTube URL is empty"
                        }
                    )
                    return

                # Temporary directory
                temp_dir = tempfile.mkdtemp()

                output_template = os.path.join(
                    temp_dir,
                    "%(title)s.%(ext)s"
                )

                # -----------------------------
                # YouTube download
                # -----------------------------
                ydl_opts = {
                    "format": "best[ext=mp4]/best",
                    "outtmpl": output_template,
                    "noplaylist": True,
                    "quiet": True,
                    "no_warnings": True,
                    "restrictfilenames": False,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(
                        youtube_url,
                        download=True
                    )

                # Find downloaded file
                downloaded_file = None

                for filename in os.listdir(temp_dir):
                    full_path = os.path.join(
                        temp_dir,
                        filename
                    )

                    if os.path.isfile(full_path):
                        downloaded_file = full_path
                        break

                if not downloaded_file:
                    raise Exception(
                        "Downloaded file was not found"
                    )

                file_name = os.path.basename(
                    downloaded_file
                )

                # -----------------------------
                # Google Drive
                # -----------------------------
                drive = get_drive_service()

                folder_id = os.environ[
                    "GOOGLE_DRIVE_FOLDER_ID"
                ]

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

                # -----------------------------
                # Response
                # -----------------------------
                send_json(
                    self,
                    200,
                    {
                        "success": True,
                        "message": "Video downloaded and uploaded to Google Drive",
                        "title": info.get("title"),
                        "file_name": uploaded.get("name"),
                        "file_id": uploaded.get("id"),
                        "web_view_link": uploaded.get("webViewLink"),
                        "download_link": uploaded.get("webContentLink"),
                    }
                )

                return

            # -----------------------------
            # Unknown endpoint
            # -----------------------------
            send_json(
                self,
                404,
                {
                    "success": False,
                    "error": "Endpoint not found"
                }
            )

        except Exception as e:

            send_json(
                self,
                500,
                {
                    "success": False,
                    "error": str(e)
                }
            )
