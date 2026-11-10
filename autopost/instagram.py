"""Publish a Reel to an Instagram professional account.

Works with both kinds of token Meta issues:
  - Instagram Login tokens (start with "IGAA")  -> graph.instagram.com
  - Facebook Login for Business tokens ("EAA")   -> graph.facebook.com
The content-publishing calls are the same on both hosts.
"""
import os, time
import requests

VERSION = os.environ.get("IG_API_VERSION", "v25.0")


def _tok(): return os.environ["IG_ACCESS_TOKEN"].strip()
def _uid(): return os.environ["IG_USER_ID"].strip()


def token_kind(token=None):
    t = (token or _tok())
    return "instagram" if t.startswith("IG") else "facebook"


def base():
    host = "graph.instagram.com" if token_kind() == "instagram" else "graph.facebook.com"
    return f"https://{host}/{VERSION}"


def _check(r):
    if r.status_code >= 300:
        raise RuntimeError(f"Instagram API error {r.status_code}: {r.text[:500]}")
    return r.json()


def whoami():
    """Cheap read-only call used by the connection test."""
    return _check(requests.get(f"{base()}/{_uid()}", timeout=60,
                               params={"fields": "username", "access_token": _tok()}))


def publish_reel(video_url, caption, log=print, max_wait=900):
    B = base()
    c = _check(requests.post(f"{B}/{_uid()}/media", timeout=60, data={
        "media_type": "REELS", "video_url": video_url, "caption": caption,
        "share_to_feed": "true", "access_token": _tok()}))
    cid = c["id"]; log(f"container {cid} created, waiting for Instagram to process the video")
    waited = 0
    while True:
        s = _check(requests.get(f"{B}/{cid}", timeout=60,
                                params={"fields": "status_code,status", "access_token": _tok()}))
        code = s.get("status_code")
        if code == "FINISHED": break
        if code in ("ERROR", "EXPIRED"): raise RuntimeError(f"Instagram could not process the video: {s}")
        if waited >= max_wait: raise RuntimeError(f"Instagram still processing after {max_wait}s: {s}")
        time.sleep(15); waited += 15
    m = _check(requests.post(f"{B}/{_uid()}/media_publish", timeout=60,
                             data={"creation_id": cid, "access_token": _tok()}))
    mid = m["id"]
    info = _check(requests.get(f"{B}/{mid}", timeout=60, params={"fields": "permalink", "access_token": _tok()}))
    return mid, info.get("permalink", "")


def refresh_token():
    """Extend a long-lived token. Returns (token, expires_in_seconds) or None if not possible right now."""
    if token_kind() == "instagram":
        r = requests.get("https://graph.instagram.com/refresh_access_token", timeout=60,
                         params={"grant_type": "ig_refresh_token", "access_token": _tok()})
    else:
        app_id, secret = os.environ.get("FB_APP_ID"), os.environ.get("FB_APP_SECRET")
        if not (app_id and secret):
            print("Facebook-type token: add FB_APP_ID and FB_APP_SECRET secrets to enable automatic renewal.")
            return None
        r = requests.get(f"https://graph.facebook.com/{VERSION}/oauth/access_token", timeout=60, params={
            "grant_type": "fb_exchange_token", "client_id": app_id, "client_secret": secret, "fb_exchange_token": _tok()})
    if r.status_code >= 300:
        print(f"Refresh not possible: {r.status_code} {r.text[:300]}"); return None
    j = r.json(); return j.get("access_token"), j.get("expires_in")
