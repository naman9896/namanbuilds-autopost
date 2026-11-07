#!/usr/bin/env bash
# Publishes new videos to the gh-pages branch (served by GitHub Pages) so Instagram can download them.
# Keeps the last 14 days of videos and rewrites the branch as a single commit so the repo stays small.
set -euo pipefail
shopt -s nullglob
new=(out/videos/*.mp4)
if [ ${#new[@]} -eq 0 ]; then echo "No new videos to publish."; exit 0; fi

remote="${MEDIA_REMOTE:-https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git}"
site=$(mktemp -d)
if git clone -q --depth 1 --branch gh-pages "$remote" "$site" 2>/dev/null; then
  echo "Updating existing gh-pages branch"
else
  echo "Creating gh-pages branch"; git -C "$site" init -q -b gh-pages; git -C "$site" remote add origin "$remote"
fi

mkdir -p "$site/videos"
cp "${new[@]}" "$site/videos/"
cutoff=$(date -u -d "14 days ago" +%F)
for f in "$site"/videos/*.mp4; do
  d=$(basename "$f" | cut -c1-10)
  if [[ "$d" < "$cutoff" ]]; then rm -f "$f"; fi
done
touch "$site/.nojekyll"
{
  echo "<!doctype html><meta charset=utf-8><title>namanbuilds.ai reels</title><body style='font-family:sans-serif;background:#0F1226;color:#fff'><h1>Upcoming reels</h1><ul>"
  for f in "$site"/videos/*.mp4; do n=$(basename "$f"); echo "<li><a style='color:#00D2FF' href='videos/$n'>$n</a></li>"; done
  echo "</ul></body>"
} > "$site/index.html"

cd "$site"
git config user.name "autopost-bot"
git config user.email "autopost-bot@users.noreply.github.com"
git checkout -q --orphan fresh
git add -A
git commit -q -m "Reels as of $(date -u +%FT%TZ)"
git push -q -f origin fresh:gh-pages
echo "Published: ${new[*]}"
