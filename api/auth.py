from http.server import BaseHTTPRequestHandler
from urllib.parse import urlencode
import os


CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")

REDIRECT_URI = "https://youtube-downloader-opal-one.vercel.app/api/auth"

SCOPES = "https://www.googleapis.com/auth/drive"


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        if not CLIENT_ID:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"GOOGLE_CLIENT_ID is not configured")
            return

        params = {
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": SCOPES,
            "access_type": "offline",
            "prompt": "consent",
        }

        auth_url = (
            "https://accounts.google.com/o/oauth2/v2/auth?"
            + urlencode(params)
        )

        self.send_response(302)
        self.send_header("Location", auth_url)
        self.end_headers()
