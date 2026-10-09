#!/usr/bin/env python3
"""Fetch the lex.uz and norma.uz RSS feeds and print items not seen before.

Usage:
  fetch_feeds.py              # print new items as JSON, do not touch the state
  fetch_feeds.py --commit     # print new items and mark them as seen
  fetch_feeds.py --all        # print every item in the feeds (ignore the state)

The state lives in state/seen.json: {link: first-seen date}. lex.uz puts the
adoption date into pubDate and adds documents days later, so new items are
detected by link, not by date. Entries older than KEEP_DAYS are pruned.
"""
import datetime as dt
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

FEEDS = [
    ("lex.uz", "https://lex.uz/ru/rss"),
    ("norma.uz", "https://www.norma.uz/ru/scripts/rss/1882,2218,3950,630,4365,4315,4382"),
]
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "state", "seen.json")
KEEP_DAYS = 120


def fetch(source, url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().lstrip(b"\xef\xbb\xbf")
    items = []
    for it in ET.fromstring(raw).iter("item"):
        link = urljoin(url, (it.findtext("link") or "").strip())
        items.append({
            "source": source,
            "title": (it.findtext("title") or "").strip(),
            "link": link,
            "date": (it.findtext("pubDate") or "").strip(),
            "description": (it.findtext("description") or "").strip(),
        })
    return items


def load_state():
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_state(state):
    cutoff = (dt.date.today() - dt.timedelta(days=KEEP_DAYS)).isoformat()
    state = {k: v for k, v in state.items() if v >= cutoff}
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=0, sort_keys=True)
        f.write("\n")


def main():
    args = set(sys.argv[1:])
    items, errors = [], []
    for source, url in FEEDS:
        try:
            items += fetch(source, url)
        except Exception as e:  # one broken feed must not hide the other
            errors.append(f"{source}: {e}")
    state = load_state()
    new = items if "--all" in args else [i for i in items if i["link"] not in state]
    if "--commit" in args:
        today = dt.date.today().isoformat()
        for i in items:
            state.setdefault(i["link"], today)
        save_state(state)
    json.dump({"errors": errors, "items": new}, sys.stdout, ensure_ascii=False, indent=1)
    print()
    return 1 if len(errors) == len(FEEDS) else 0


if __name__ == "__main__":
    sys.exit(main())
