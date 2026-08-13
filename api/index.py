from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/auth":
            query = parse_qs(parsed.query)

            if "code" in query:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()

                self.wfile.write(
                    b"""
                    <html>
                    <body>
                    <h2>Google OAuth callback received successfully.</h2>
                    <p>Authorization code received.</p>
                    </body>
                    </html>
                    """
                )
                return

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()

            self.wfile.write(
                b"""
                <html>
                <body>
                <h2>OAuth endpoint is working.</h2>
                </body>
                </html>
                """
            )
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        self.wfile.write(
            b'{"success":true,"message":"YouTube Downloader API is running"}'
        )
