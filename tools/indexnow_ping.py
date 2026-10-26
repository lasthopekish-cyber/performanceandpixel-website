#!/usr/bin/env python3
"""Tell IndexNow search engines (Bing, which powers ChatGPT search and Copilot, plus Yandex,
Seznam and Naver) about pages added or changed in a push. Runs in GitHub Actions.
ALL=1 submits every URL in sitemap.xml instead."""
import json, os, re, subprocess, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = "performanceandpixel.com"
KEY = (ROOT / "tools/indexnow.key").read_text().strip()


def changed_urls():
    if os.environ.get("ALL"):
        return re.findall(r"<loc>(.*?)</loc>", (ROOT / "sitemap.xml").read_text())
    before, after = os.environ.get("BEFORE", ""), os.environ.get("AFTER", "HEAD")
    if not before or set(before) == {"0"}:
        before = after + "~1"
    files = subprocess.run(["git", "diff", "--name-only", "--diff-filter=AM", before, after],
                           capture_output=True, text=True, check=True, cwd=ROOT).stdout.split()
    urls = []
    for f in files:
        if not f.endswith(".html") or f.startswith(("content/", "seo/", "tools/", ".github/")) or f == "404.html" or re.fullmatch(r"google[0-9a-f]+\.html", f):
            continue
        urls.append(f"https://{HOST}/" if f == "index.html" else f"https://{HOST}/{f}")
    return urls


if __name__ == "__main__":
    urls = changed_urls()
    if not urls:
        print("No changed pages.")
        raise SystemExit(0)
    body = {"host": HOST, "key": KEY, "keyLocation": f"https://{HOST}/{KEY}.txt", "urlList": urls[:10000]}
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("IndexNow", r.status, "for", len(urls), "URLs")
    except urllib.error.HTTPError as e:
        print("IndexNow error", e.code, e.read().decode()[:300])
        raise SystemExit(0 if e.code in (202,) else 1)
    for u in urls:
        print(" ", u)
