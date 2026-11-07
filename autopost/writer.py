"""Writes a video spec + Instagram caption for a topic using the Claude API, then validates it."""
import json, os, re, glob
import requests

from .template import validate, ICONS, COLORS

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")
HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLES_DIR = os.path.join(os.path.dirname(HERE), "specs", "examples")

SCHEMA = f"""
A video is JSON: {{"topic": str, "speed": 1.08, "scenes": [scene, ...]}}.
Scenes run in order. Every scene has "type" and "vo" (the voiceover line, spoken by an AI voice, also shown as the caption).
Animation beats are tied to words in "vo" with "cue": a short phrase that MUST appear verbatim (case-insensitive) in that scene's "vo".

Scene types:
1. "hook" (always first). Fields: "a": [line1, line2] shown first, "b": [line1, line2] swapped in at "swap_cue",
   "icon", "swap_cue", "accent_a", "accent_b". Keep each line under 14 characters, ALL CAPS. The vo is a scroll-stopping
   question or claim, then a turn ("Here's how...").
2. "flow" (2 or 3 icon nodes with labelled packets moving between them). Fields: "title" (1 word, ALL CAPS), "sub"
   (short, often "= plain meaning"), "color", "nodes": [{{"icon", "label" (<= 18 chars), "color", optional "cue",
   optional "pos": [x, y] (canvas 1080x1920, nodes normally at y 960)}}], optional "links": [[i, j], ...]
   (default links neighbours), "packets": [{{"frm": i, "to": j, "label" (<= 16 chars), optional "label2" (label it
   changes into halfway), "cue", "color", optional "lane" (vertical offset, -140..220, use different lanes for packets
   that overlap in time)}}], optional "bubbles": [{{"node": i, "text" (<= 18 chars), "cue", "color", "dx", "dy"}}].
3. "compare" (two side-by-side cards). Fields: "title", "left"/"right": {{"name", "icon", "color", "point" (<= 32 chars),
   "badge": "x" or "check", "cue", "badge_cue"}}.
4. "list" (2-4 rows that slide in). Fields: "title", optional "sub", "color", "items": [{{"icon", "text" (<= 32 chars),
   "cue", "color"}}].
5. "cta" (always last). Fields: "vo": "Follow for more tech, made simple.", "next": short teaser of the next topic.

Allowed icons: {", ".join(ICONS)}.
Allowed colours: {", ".join(COLORS)} (purple is the brand colour; coral = bad/danger, green = good/success).
"""

RULES = """
Rules:
- Audience: complete beginners. Use one everyday analogy (restaurant, post office, phone book, etc.). No jargon without explaining it.
- 5 scenes: hook, 2-3 teaching scenes (mix flow / compare / list), cta.
- Total voiceover 60-75 words so the video is 28-32 seconds. Each teaching scene's vo is 1-2 short sentences.
- Write numbers and symbols the way they should be spoken in "vo" (e.g. "google dot com"), but use symbols in labels.
- Be technically accurate. If something is a simplification, keep it true.
- Every "cue" must be copied exactly from its own scene's "vo".
- Australian English spelling.
Caption rules (Instagram): hook line + emoji, 3-5 short lines that teach the key points with emoji bullets, a save prompt,
a comment question, then 5 relevant hashtags. Under 1,000 characters.
Return ONLY a JSON object: {"spec": <video spec>, "caption": "<caption>"} with no markdown fences.
"""


def _examples():
    out = []
    for f in sorted(glob.glob(os.path.join(EXAMPLES_DIR, "*.json"))):
        out.append(open(f).read().strip())
    return "\n\n".join(out)


def _call(messages, system):
    key = os.environ["ANTHROPIC_API_KEY"]
    r = requests.post(API_URL, timeout=180, headers={
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": MODEL, "max_tokens": 6000, "system": system, "messages": messages})
    if r.status_code != 200:
        raise RuntimeError(f"Claude API error {r.status_code}: {r.text[:500]}")
    return "".join(b.get("text", "") for b in r.json()["content"] if b.get("type") == "text")


def _parse(txt):
    txt = txt.strip()
    txt = re.sub(r"^```(?:json)?|```$", "", txt).strip()
    start = txt.find("{"); end = txt.rfind("}")
    return json.loads(txt[start:end + 1])


def write(topic, hook=None, notes=None, next_topic=None, attempts=3):
    system = ("You write scripts for 'Tech in 30 Seconds', a beginner-friendly motion-graphics Instagram Reel series "
              "by @namanbuilds.ai about web development, AI and tech.\n" + SCHEMA + RULES +
              "\nHere are three finished, approved examples to match in tone, pacing and structure:\n\n" + _examples())
    ask = f"Topic: {topic}\n"
    if hook: ask += f"Planned hook (use or improve): {hook}\n"
    if notes: ask += f"Production notes from the creator: {notes}\n"
    if next_topic: ask += f"Use this for the cta 'next' field: {next_topic}\n"
    messages = [{"role": "user", "content": ask}]
    last_err = None
    for _ in range(attempts):
        reply = _call(messages, system)
        try:
            data = _parse(reply)
            spec, caption = data["spec"], data["caption"].strip()
            spec.setdefault("speed", 1.08); spec.setdefault("topic", topic)
            if next_topic: spec["scenes"][-1]["next"] = next_topic
            secs = validate(spec)
            if len(caption) > 2100: raise ValueError("caption over 2,100 characters")
            return spec, caption, secs
        except Exception as e:  # feed the problem back and let the model fix it
            last_err = e
            messages += [{"role": "assistant", "content": reply},
                         {"role": "user", "content": f"That didn't pass validation: {e}. Fix it and return the full JSON again."}]
    raise RuntimeError(f"Could not get a valid script after {attempts} attempts: {last_err}")
