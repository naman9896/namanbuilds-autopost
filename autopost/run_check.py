"""'Test connections' job: checks every secret without generating or posting anything."""
import os, sys
import requests

from . import notion, instagram

# Kept here (not imported from writer.py) so this check only needs 'requests'.
API_URL = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")

NEEDED = ["Topic", "Post Date", "Format", "Status", "Hook", "Caption", "Approved", "Video URL", "Instagram URL", "Automation Log"]


def check(name, fn):
    try:
        msg = fn(); print(f"PASS  {name}: {msg}"); return True
    except Exception as e:
        print(f"FAIL  {name}: {e}"); return False


def notion_ok():
    rows = notion.rows()
    if not rows: raise RuntimeError("connected, but the Content Plan has no rows (is the integration connected to it?)")
    db = os.environ.get("NOTION_DB", "bba18f84174c4357a20d8fd9c2fed3ed")
    r = requests.get(f"{notion.API}/databases/{db}", headers=notion._h(), timeout=60); r.raise_for_status()
    missing = [p for p in NEEDED if p not in r.json()["properties"]]
    if missing: raise RuntimeError(f"Content Plan is missing properties: {missing}")
    auto = [x for x in rows if x.format == "Reel – Motion Graphic"]
    return f"{len(rows)} rows, {len(auto)} motion-graphic reels"


def claude_ok():
    r = requests.post(API_URL, timeout=60, headers={
        "x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": MODEL, "max_tokens": 5, "messages": [{"role": "user", "content": "Reply OK"}]})
    if r.status_code != 200: raise RuntimeError(f"{r.status_code}: {r.text[:300]}")
    return f"key works with model {MODEL}"


def instagram_ok():
    me = instagram.whoami()
    return f"@{me.get('username')} via {instagram.token_kind()} token ({instagram.base().split('/')[2]})"


if __name__ == "__main__":
    results = [check("Notion", notion_ok), check("Claude API", claude_ok), check("Instagram", instagram_ok)]
    print("\nAll good. The automation is ready." if all(results) else "\nFix the FAIL lines above, then run this again.")
    sys.exit(0 if all(results) else 1)