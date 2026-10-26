#!/usr/bin/env python3
"""Send a WhatsApp message for every blog post added in a push.

Runs in GitHub Actions (.github/workflows/whatsapp-new-blog.yml). Two ways to send,
configured with repository secrets (Settings > Secrets and variables > Actions):

A) Meta WhatsApp Cloud API (your own business number)
   WA_TOKEN            permanent access token (system user) with whatsapp_business_messaging
   WA_PHONE_NUMBER_ID  the sending phone number ID from WhatsApp Manager / API setup
   WA_TEMPLATE         (recommended) approved template name with 2 body variables:
                       {{1}} = post title, {{2}} = post link
   WA_TEMPLATE_LANG    template language code, default en
   Without WA_TEMPLATE a plain text message is sent, which WhatsApp only delivers if the
   recipient messaged the business number in the last 24 hours.

B) CallMeBot (free, personal alerts only)
   CALLMEBOT_APIKEY    key you get after messaging the CallMeBot number to activate

WA_TO  recipient in international format without + (default 918005590095)
"""
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

SITE = "https://performanceandpixel.com/"
TO = (os.environ.get("WA_TO") or "918005590095").lstrip("+").replace(" ", "")


def new_posts():
    if os.environ.get("TEST"):
        return [("Test: WhatsApp blog alerts are working", SITE + "blog/index.html")]
    before, after = os.environ.get("BEFORE", ""), os.environ.get("AFTER", "HEAD")
    if not before or set(before) == {"0"}:
        before = after + "~1"
    out = subprocess.run(["git", "diff", "--name-only", "--diff-filter=A", before, after, "--", "blog/*.html"],
                         capture_output=True, text=True, check=True).stdout.split()
    posts = []
    for f in out:
        if f.endswith("index.html"):
            continue
        h = open(f, encoding="utf-8").read()
        m = re.search(r'"headline":\s*"([^"]+)"', h) or re.search(r"<title>(.*?)</title>", h)
        title = m.group(1) if m else f
        posts.append((title, SITE + f))
    return posts


def post_json(url, payload, token):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read().decode()[:300]


def send(title, link):
    text = f"New blog live on Performance and Pixel:\n{title}\n{link}"
    token, pid = os.environ.get("WA_TOKEN"), os.environ.get("WA_PHONE_NUMBER_ID")
    if token and pid:
        url = f"https://graph.facebook.com/v21.0/{pid}/messages"
        tpl = os.environ.get("WA_TEMPLATE")
        if tpl:
            payload = {"messaging_product": "whatsapp", "to": TO, "type": "template",
                       "template": {"name": tpl, "language": {"code": os.environ.get("WA_TEMPLATE_LANG") or "en"},
                                    "components": [{"type": "body", "parameters": [
                                        {"type": "text", "text": title[:900]}, {"type": "text", "text": link}]}]}}
        else:
            payload = {"messaging_product": "whatsapp", "to": TO, "type": "text",
                       "text": {"body": text, "preview_url": True}}
        return post_json(url, payload, token)
    key = os.environ.get("CALLMEBOT_APIKEY")
    if key:
        q = urllib.parse.urlencode({"phone": "+" + TO, "text": text, "apikey": key})
        with urllib.request.urlopen("https://api.callmebot.com/whatsapp.php?" + q, timeout=30) as r:
            return r.status, r.read().decode()[:300]
    raise SystemExit("No WhatsApp sender configured: add WA_TOKEN + WA_PHONE_NUMBER_ID, or CALLMEBOT_APIKEY, as repo secrets.")


if __name__ == "__main__":
    posts = new_posts()
    if not posts:
        print("No new blog posts in this push.")
        sys.exit(0)
    failed = 0
    for title, link in posts:
        try:
            status, body = send(title, link)
            print("sent", link, status, body)
        except Exception as e:  # keep going for other posts, fail the job at the end
            failed += 1
            print("FAILED", link, e)
    sys.exit(1 if failed else 0)
