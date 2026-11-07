# namanbuilds-autopost

Turns the **Content Plan** in Notion into finished "Tech in 30 Seconds" Instagram Reels and posts them automatically.

```
Notion Content Plan ──► (6 pm) write script + caption with Claude ──► render video ──► preview link in Notion
                                                                                              │
                         Instagram ◄── (Post Date, e.g. 8 am) post if Approved is ticked ◄────┘
```

## How it works

| Workflow | When | What it does |
|---|---|---|
| `Generate tomorrow's reels` | Daily 07:00 UTC (6 pm Sydney in summer) | Finds rows with **Format = Reel – Motion Graphic**, **Status = Idea/Script** and a **Post Date in the next 30 hours**. Writes the script and caption, renders the video, publishes it to this repo's GitHub Pages site, and sets the row to **Ready for review** with the **Video URL**. |
| `Post due reels` | Every 30 minutes | Posts rows that are **Ready for review + Approved** (or **Scheduled**) once their **Post Date** has passed, then sets **Posted** and fills in **Instagram URL**. |
| `Refresh Instagram token` | Mondays | Extends the Instagram token so it never expires. |

Other formats (carousels, talking reels, screen recordings) are skipped. Post those yourself.

**Your daily routine:** open the row that's Ready for review, watch the Video URL, read the Caption, and tick **Approved**. That's it.
To regenerate a reel you don't like, set its Status back to **Idea**, then run *Generate tomorrow's reels* manually with the row's page ID.

## One-time setup

### 1. GitHub
- Settings → Pages → *Deploy from a branch* → `gh-pages` / root. The branch appears after the first generate run, so do this step right after it.
- Settings → Secrets and variables → Actions → **Secrets**:

| Secret | Where to get it |
|---|---|
| `NOTION_TOKEN` | notion.so/profile/integrations → New internal integration → copy the secret. Then open the Content Plan in Notion → ••• → Connections → add the integration. |
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys |
| `IG_USER_ID` | Meta app → Instagram → API setup with Instagram login → shown next to your account |
| `IG_ACCESS_TOKEN` | Same page → *Generate token* (long-lived, 60 days) |
| `GH_PAT` *(optional)* | GitHub fine-grained token with **Secrets: read and write** on this repo, so the weekly refresh can save a new token |

- Optional **Variables**: `AUTO_APPROVE=true` (post without review), `CLAUDE_MODEL`, `NOTION_DB`.

### 2. Instagram
Instagram must be a **Professional (Creator or Business)** account. In developers.facebook.com create an app → add the **Instagram** product → *API setup with Instagram login* → add your account (accept the tester invite in Instagram → Settings → Website permissions → Apps and websites) → generate the token. Permissions needed: `instagram_business_basic`, `instagram_business_content_publish`.

## Run locally

```bash
pip install -r requirements.txt   # plus ffmpeg and libcairo2-dev
python -m autopost.template specs/examples/api.json api.mp4   # render a spec
python -m tests.dry_run                                       # full pipeline with fake Notion/Claude/Instagram
```

## Making new kinds of videos
Videos are JSON specs (see `specs/examples/`). Scene types: `hook`, `flow`, `compare`, `list`, `cta`. Icons and colours are listed in `autopost/template.py`. Add a new icon to `icon()` and to `ICONS`, and the script writer can use it straight away.

Fonts: Poppins (SIL Open Font License). Voice: Kokoro (Apache 2.0).
