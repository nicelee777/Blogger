#!/usr/bin/env python3
"""One-time local helper to obtain a Blogger OAuth refresh token.

Runs a temporary loopback HTTP server on 127.0.0.1 so Google can return the
OAuth authorization code directly to this script. Run only on your own
computer. Never commit client secrets or refresh tokens.
"""
from __future__ import annotations

import argparse
import json
import secrets
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/blogger"


class OAuthCallbackServer(HTTPServer):
    auth_params: dict[str, list[str]] | None = None


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    server: OAuthCallbackServer

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urllib.parse.urlparse(self.path)
        self.server.auth_params = urllib.parse.parse_qs(parsed.query)

        body = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<title>ShiftMate Blogger OAuth</title></head>"
            "<body style='font-family:system-ui,sans-serif;padding:32px'>"
            "<h2>Authorization complete</h2>"
            "<p>You can close this tab and return to the terminal.</p>"
            "</body></html>"
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


def exchange_code(
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
) -> dict[str, Any]:
    body = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
    ).encode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--client-secret", required=True)
    args = parser.parse_args()

    state = secrets.token_urlsafe(24)

    try:
        server = OAuthCallbackServer(("127.0.0.1", 0), OAuthCallbackHandler)
    except OSError as exc:
        raise SystemExit(f"Could not open local OAuth callback server: {exc}") from exc

    host, port = server.server_address
    redirect_uri = f"http://{host}:{port}/"

    params = {
        "client_id": args.client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    auth_url = AUTH_URL + "?" + urllib.parse.urlencode(params)

    print("Opening Google authorization in your browser...")
    print(f"Local callback: {redirect_uri}")
    print("If the browser does not open automatically, open this URL manually:\n")
    print(auth_url)

    try:
        webbrowser.open(auth_url)
        print("\nWaiting for Google authorization callback...")
        server.handle_request()
    finally:
        server.server_close()

    query = server.auth_params or {}
    if query.get("state", [""])[0] != state:
        raise SystemExit("OAuth state mismatch. Please run the helper again.")

    if query.get("error"):
        description = query.get("error_description", [query["error"][0]])[0]
        raise SystemExit(f"Google authorization failed: {description}")

    code = query.get("code", [""])[0]
    if not code:
        raise SystemExit("No authorization code was returned. Please run the helper again.")

    token = exchange_code(args.client_id, args.client_secret, code, redirect_uri)
    refresh = token.get("refresh_token")
    if not refresh:
        raise SystemExit(
            "No refresh_token returned. Revoke the app grant and retry; "
            "this helper already requests prompt=consent and access_type=offline."
        )

    print("\nAuthorization succeeded.")
    print("Add these values to GitHub Actions secrets (never commit or share them):")
    print("BLOGGER_CLIENT_ID=" + args.client_id)
    print("BLOGGER_CLIENT_SECRET=" + args.client_secret)
    print("BLOGGER_REFRESH_TOKEN=" + str(refresh))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
