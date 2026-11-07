"""Publish a Reel with the Instagram API (Instagram Login, professional account)."""
import os, time
import requests

VERSION = os.environ.get("IG_API_VERSION", "v25.0")
BASE = f"https://graph.instagram.com/{VERSION}"


def _tok(): return os.environ["IG_ACCESS_TOKEN"]
def _uid(): return os.environ["IG_USER_ID"]


def _check(r):
    if r.status_code >= 300:
        raise RuntimeError(f"Instagram API error {r.status_code}: {r.text[:500]}")
    return r.json()


def publish_reel(video_url, caption, log=print, max_wait=900):
    c = _check(requests.post(f"{BASE}/{_uid()}/media", timeout=60, data={
        "media_type": "REELS", "video_url": video_url, "caption": caption,
        "share_to_feed": "true", "access_token": _tok()}))
    cid = c["id"]; log(f"container {cid} created, waiting for Instagram to process the video")
    waited = 0
    while True:
        s = _check(requests.get(f"{BASE}/{cid}", timeout=60,
                                params={"fields": "status_code,status", "access_token": _tok()}))
        code = s.get("status_code")
        if code == "FINISHED": break
        if code in ("ERROR", "EXPIRED"): raise RuntimeError(f"Instagram could not process the video: {s}")
        if waited >= max_wait: raise RuntimeError(f"Instagram still processing after {max_wait}s: {s}")
        time.sleep(15); waited += 15
    m = _check(requests.post(f"{BASE}/{_uid()}/media_publish", timeout=60,
                             data={"creation_id": cid, "access_token": _tok()}))
    mid = m["id"]
    info = _check(requests.get(f"{BASE}/{mid}", timeout=60, params={"fields": "permalink", "access_token": _tok()}))
    return mid, info.get("permalink", "")


def refresh_token():
    """Extends a long-lived token by 60 days. Returns (token, expires_in) or None if not refreshable yet."""
    r = requests.get("https://graph.instagram.com/refresh_access_token", timeout=60,
                     params={"grant_type": "ig_refresh_token", "access_token": _tok()})
    if r.status_code >= 300: return None
    j = r.json(); return j.get("access_token"), j.get("expires_in")
