"""Posting job (runs every 30 min): posts approved reels whose Post Date has arrived.

Env: NOTION_TOKEN, IG_USER_ID, IG_ACCESS_TOKEN, MAX_LATE_HOURS (default 12).
"""
import os, sys, traceback
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests

from . import notion, instagram

TZ = ZoneInfo("Australia/Sydney")


def ready(r, now, max_late):
    if not r.post_date or not r.video_url or not r.caption: return False
    approved = r.status == "Scheduled" or (r.status == "Ready for review" and r.approved)
    return approved and r.post_date <= now and now - r.post_date <= max_late


def main():
    now = datetime.now(TZ)
    max_late = timedelta(hours=float(os.environ.get("MAX_LATE_HOURS", "12")))
    due = [r for r in notion.rows() if ready(r, now, max_late)]
    print(f"{len(due)} reel(s) due: {due}")
    failures = 0
    for row in due:
        try:
            h = requests.head(row.video_url, timeout=60, allow_redirects=True)
            if h.status_code != 200:  # GitHub Pages may still be deploying; try again next run
                print(f"SKIP {row.topic}: video link not reachable yet ({h.status_code})"); continue
            notion.update(row.id, status="Posting")
            mid, link = instagram.publish_reel(row.video_url, row.caption)
            notion.update(row.id, status="Posted", instagram_url=link or None,
                          log=f"{datetime.now(TZ):%d %b %H:%M} posted to Instagram: {link}")
            print(f"POSTED {row.topic} -> {link}")
        except Exception as e:
            failures += 1
            traceback.print_exc()
            notion.update(row.id, status="Failed", log=f"{datetime.now(TZ):%d %b %H:%M} posting failed: {e}")
    if failures: sys.exit(1)


if __name__ == "__main__":
    main()
