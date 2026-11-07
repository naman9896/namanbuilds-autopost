"""Evening job: write + render tomorrow's motion-graphic reels and send them to Notion for approval.

Env: NOTION_TOKEN, ANTHROPIC_API_KEY, MODEL_DIR, PAGES_BASE (public URL of the media site),
     LOOKAHEAD_HOURS (default 30), AUTO_APPROVE ("true" to skip manual approval), ONLY_PAGE (optional page id).
Writes rendered videos to out/videos/ for the workflow to publish on GitHub Pages.
"""
import json, os, re, sys, traceback
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from . import notion, writer, template

TZ = ZoneInfo("Australia/Sydney")
AUTO_FORMAT = "Reel – Motion Graphic"


def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:50]


def main():
    now = datetime.now(TZ)
    horizon = now + timedelta(hours=float(os.environ.get("LOOKAHEAD_HOURS", "30")))
    only = os.environ.get("ONLY_PAGE", "").replace("-", "")
    auto = os.environ.get("AUTO_APPROVE", "false").lower() == "true"
    base = os.environ["PAGES_BASE"].rstrip("/")
    OUT = os.environ.get("OUT_DIR", "out")
    os.makedirs(f"{OUT}/videos", exist_ok=True); os.makedirs(f"{OUT}/specs", exist_ok=True)

    all_rows = sorted([r for r in notion.rows() if r.post_date], key=lambda r: r.post_date)
    motion = [r for r in all_rows if r.format == AUTO_FORMAT]
    if only:
        todo = [r for r in motion if r.id.replace("-", "") == only]
    else:
        todo = [r for r in motion if r.status in ("Idea", "Script") and now <= r.post_date <= horizon]
    print(f"{len(todo)} reel(s) to generate: {todo}")

    failures = 0
    for row in todo:
        later = [r for r in motion if r.post_date > row.post_date]
        nxt = later[0].topic if later else None
        name = f"{row.post_date:%Y-%m-%d}-{slug(row.topic)}"
        try:
            spec, caption, est = writer.write(row.topic, row.hook, row.notes, nxt)
            spec_path = f"{OUT}/specs/{name}.json"
            json.dump(spec, open(spec_path, "w"), indent=1, ensure_ascii=False)
            secs = template.make(spec_path, f"{OUT}/videos/{name}.mp4", workdir=f"/tmp/autopost-work/{name}")
            url = f"{base}/videos/{name}.mp4"
            notion.update(row.id, status="Scheduled" if auto else "Ready for review", caption=caption,
                          video_url=url, approved=True if auto else None,
                          log=f"{datetime.now(TZ):%d %b %H:%M} generated {secs:.0f}s video. "
                              + ("Auto-approved." if auto else "Tick Approved to post it."))
            print(f"OK {row.topic} -> {url} ({secs:.1f}s)")
        except Exception as e:
            failures += 1
            traceback.print_exc()
            notion.update(row.id, status="Failed", log=f"{datetime.now(TZ):%d %b %H:%M} generation failed: {e}")
    if failures: sys.exit(1)


if __name__ == "__main__":
    main()
