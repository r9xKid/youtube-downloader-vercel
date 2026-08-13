from http.server import BaseHTTPRequestHandler
from urllib.parse import urlencode, urlparse, parse_qs
from urllib.request import Request, urlopen
import json
import os


CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

REDIRECT_URI = "https://youtube-downloader-opal-one.vercel.app/api/auth"

SCOPES = "https://www.googleapis.com/auth/drive"


def exchange_code(code):
    data = urlencode({
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()

    request = Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        },
        method="POST",
    )

    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode())


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        # Google returned an error
        if "error" in query:
            self.send_response(400)
            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8"
            )
            self.end_headers()

            error = query["error"][0]

            self.wfile.write(
                f"""
                <html>
                <body>
                <h2>Google OAuth Error</h2>
                <p>{error}</p>
                </body>
                </html>
                """.encode()
            )
            return

        # Google returned authorization code
        if "code" in query:

            try:
                token_data = exchange_code(query["code"][0])

                refresh_token = token_data.get("refresh_token")

                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    "text/html; charset=utf-8"
                )
                self.end_headers()

                if refresh_token:

                    html = """
                    <html>
                    <body>
                    <h2>Google OAuth SUCCESS</h2>

                    <p>Refresh Token was successfully generated.</p>

                    <p>
                    <strong>IMPORTANT:</strong>
                    Do not publish this token or put it in GitHub.
                    </p>

                    <textarea
                    style="width:100%;height:120px;"
                    readonly
                    >""" + refresh_token + """</textarea>

                    <p>
                    Copy this value into Vercel as:
                    <strong>GOOGLE_REFRESH_TOKEN</strong>
                    </p>

                    </body>
                    </html>
                    """

                else:

                    html = """
                    <html>
                    <body>
                    <h2>OAuth completed</h2>
                    <p>
                    Google did not return a refresh token.
                    </p>
                    </body>
                    </html>
                    """

                self.wfile.write(html.encode())
                return

            except Exception as e:

                self.send_response(500)
                self.send_header(
                    "Content-Type",
                    "text/html; charset=utf-8"
                )
                self.end_headers()

                self.wfile.write(
                    f"""
                    <html>
                    <body>
                    <h2>Token exchange failed</h2>
                    <pre>{str(e)}</pre>
                    </body>
                    </html>
                    """.encode()
                )
                return

        # Start OAuth flow
        if not CLIENT_ID or not CLIENT_SECRET:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(
                b"Google OAuth environment variables are missing."
            )
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
