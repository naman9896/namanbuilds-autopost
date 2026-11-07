"""Minimal Notion API client for the Content Plan database."""
import os
from datetime import datetime
import requests

API = "https://api.notion.com/v1"
VERSION = "2022-06-28"


def _h():
    return {"Authorization": f"Bearer {os.environ['NOTION_TOKEN']}", "Notion-Version": VERSION,
            "Content-Type": "application/json"}


def _text(prop):
    if not prop: return ""
    t = prop.get("type")
    if t in ("title", "rich_text"): return "".join(x.get("plain_text", "") for x in prop[t])
    if t == "select": return (prop["select"] or {}).get("name", "")
    if t == "status": return (prop["status"] or {}).get("name", "")
    if t == "url": return prop["url"] or ""
    if t == "checkbox": return prop["checkbox"]
    if t == "date": return (prop["date"] or {}).get("start", "")
    if t == "number": return prop["number"]
    return ""


class Row:
    def __init__(self, page):
        self.id = page["id"]; p = page["properties"]
        self.topic = _text(p.get("Topic")); self.format = _text(p.get("Format"))
        self.status = _text(p.get("Status")); self.hook = _text(p.get("Hook"))
        self.notes = _text(p.get("Notes")); self.caption = _text(p.get("Caption"))
        self.video_url = _text(p.get("Video URL")); self.approved = bool(_text(p.get("Approved")))
        ds = _text(p.get("Post Date"))
        self.post_date = datetime.fromisoformat(ds) if ds else None

    def __repr__(self): return f"<Row {self.topic!r} {self.status} {self.post_date}>"


def rows():
    db = os.environ.get("NOTION_DB", "bba18f84174c4357a20d8fd9c2fed3ed")
    out, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor: body["start_cursor"] = cursor
        r = requests.post(f"{API}/databases/{db}/query", headers=_h(), json=body, timeout=60)
        r.raise_for_status(); j = r.json()
        out += [Row(p) for p in j["results"]]
        if not j.get("has_more"): break
        cursor = j["next_cursor"]
    return out


def _rt(s): return {"rich_text": [{"type": "text", "text": {"content": s[i:i + 1900]}} for i in range(0, len(s), 1900)][:20]}


def update(page_id, status=None, caption=None, video_url=None, instagram_url=None, approved=None, log=None):
    props = {}
    if status: props["Status"] = {"status": {"name": status}}
    if caption is not None: props["Caption"] = _rt(caption); props["Caption Done"] = {"checkbox": True}
    if video_url is not None: props["Video URL"] = {"url": video_url}
    if instagram_url is not None: props["Instagram URL"] = {"url": instagram_url}
    if approved is not None: props["Approved"] = {"checkbox": approved}
    if log is not None: props["Automation Log"] = _rt(log[-1900:])
    r = requests.patch(f"{API}/pages/{page_id}", headers=_h(), json={"properties": props}, timeout=60)
    if r.status_code >= 300: raise RuntimeError(f"Notion update failed {r.status_code}: {r.text[:400]}")
