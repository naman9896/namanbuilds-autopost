"""Dry run of both jobs with Notion, Claude and Instagram replaced by fakes. Run: python -m tests.dry_run"""
import json, os, sys, types
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
TZ = ZoneInfo("Australia/Sydney")
from autopost import notion, writer, instagram, run_generate, run_publish, template

now = datetime.now(TZ)
def page(pid, topic, fmt, status, when, **extra):
    r = notion.Row.__new__(notion.Row)
    r.id, r.topic, r.format, r.status, r.post_date = pid, topic, fmt, status, when
    r.hook, r.notes, r.caption, r.video_url, r.approved = "", "", extra.get("caption", ""), extra.get("video_url", ""), extra.get("approved", False)
    return r
DB = [page("p1", "HTTP vs HTTPS", "Reel – Motion Graphic", "Idea", now + timedelta(hours=14)),
      page("p2", "10 Git commands", "Carousel", "Idea", now + timedelta(hours=20)),
      page("p3", "What is an API?", "Reel – Motion Graphic", "Idea", now + timedelta(days=3)),
      page("p4", "Old approved reel", "Reel – Motion Graphic", "Ready for review", now - timedelta(minutes=10),
           caption="cap", video_url="https://example.com/v.mp4", approved=True),
      page("p5", "Not approved", "Reel – Motion Graphic", "Ready for review", now - timedelta(minutes=10),
           caption="cap", video_url="https://example.com/v.mp4", approved=False)]
updates = []
notion.rows = lambda: DB
notion.update = lambda pid, **kw: updates.append((pid, kw))
spec = json.load(open("specs/examples/https.json"))
writer.write = lambda topic, hook, notes, nxt: (dict(spec, scenes=spec["scenes"][:-1] + [dict(spec["scenes"][-1], next=nxt)]), "Test caption #git", 31.0)
os.environ.update(PAGES_BASE="https://naman9896.github.io/namanbuilds-autopost", OUT_DIR="/home/claude/test/out")
run_generate.main()
print("GENERATE updates:", json.dumps(updates, indent=1, default=str))
assert [u[0] for u in updates] == ["p1"], updates
assert updates[0][1]["status"] == "Ready for review"
vids = [f for f in os.listdir("/home/claude/test/out/videos") if f.endswith(".mp4")]
assert len(vids) == 1 and os.listdir("/home/claude/test/out/videos") == vids and os.path.getsize("/home/claude/test/out/videos/" + vids[0]) > 100000, os.listdir("/home/claude/test/out/videos")
updates.clear()
posted = []
instagram.publish_reel = lambda url, cap: (posted.append(url) or ("123", "https://www.instagram.com/reel/TEST/"))
run_publish.requests = types.SimpleNamespace(head=lambda *a, **k: types.SimpleNamespace(status_code=200))
run_publish.main()
print("PUBLISH updates:", updates)
assert posted == ["https://example.com/v.mp4"] and updates[-1][1]["status"] == "Posted" and updates[-1][0] == "p4"
print("ALL CHECKS PASSED")
