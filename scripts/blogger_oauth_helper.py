#!/usr/bin/env python3
"""One-time local helper to obtain a Blogger OAuth refresh token.
Run only on your own computer. Never commit client secrets or refresh tokens.
"""
from __future__ import annotations
import argparse, json, secrets, urllib.parse, urllib.request, webbrowser
AUTH_URL="https://accounts.google.com/o/oauth2/v2/auth"; TOKEN_URL="https://oauth2.googleapis.com/token"; SCOPE="https://www.googleapis.com/auth/blogger"; REDIRECT_URI="http://localhost"
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--client-id",required=True); ap.add_argument("--client-secret",required=True); args=ap.parse_args(); state=secrets.token_urlsafe(16)
    params={"client_id":args.client_id,"redirect_uri":REDIRECT_URI,"response_type":"code","scope":SCOPE,"access_type":"offline","prompt":"consent","state":state}; auth_url=AUTH_URL+"?"+urllib.parse.urlencode(params)
    print("Open this URL and approve Blogger access:\n\n"+auth_url)
    try: webbrowser.open(auth_url)
    except Exception: pass
    redirected=input("\nAfter approval, paste the FULL redirected localhost URL here:\n> ").strip(); q=urllib.parse.parse_qs(urllib.parse.urlparse(redirected).query)
    if q.get("state",[""])[0]!=state: raise SystemExit("OAuth state mismatch")
    code=q.get("code",[""])[0]
    if not code: raise SystemExit("No authorization code found in redirected URL")
    body=urllib.parse.urlencode({"client_id":args.client_id,"client_secret":args.client_secret,"code":code,"grant_type":"authorization_code","redirect_uri":REDIRECT_URI}).encode()
    req=urllib.request.Request(TOKEN_URL,data=body,headers={"Content-Type":"application/x-www-form-urlencoded"},method="POST")
    with urllib.request.urlopen(req,timeout=30) as resp: token=json.load(resp)
    refresh=token.get("refresh_token")
    if not refresh: raise SystemExit("No refresh_token returned. Revoke the app grant and retry with prompt=consent.")
    print("\nAdd these values to GitHub Actions secrets (never commit them):")
    print("BLOGGER_CLIENT_ID="+args.client_id); print("BLOGGER_CLIENT_SECRET="+args.client_secret); print("BLOGGER_REFRESH_TOKEN="+refresh)
    return 0
if __name__=="__main__": raise SystemExit(main())
