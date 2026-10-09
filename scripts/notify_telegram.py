#!/usr/bin/env python3
"""Send a message to Telegram via the Bot API.

Usage:
  notify_telegram.py "text"          # send the given text
  echo "text" | notify_telegram.py   # send text from stdin
  notify_telegram.py --hook          # read Claude Code hook JSON from stdin

Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from the environment.
In --hook mode it never fails the hook: errors go to stderr, exit code is 0.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

MAX_LEN = 4000  # Telegram limit is 4096 characters per message


def send(text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not set")
    if len(text) > MAX_LEN:
        text = text[: MAX_LEN - 1] + "…"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        with urllib.request.urlopen(url, data=data, timeout=15) as resp:
            body = json.load(resp)
    except urllib.error.HTTPError as e:
        body = json.load(e)
    if not body.get("ok"):
        raise RuntimeError(f"Telegram API error: {body.get('description')}")


def hook_text(event):
    name = event.get("hook_event_name", "")
    project = os.path.basename(event.get("cwd") or os.getcwd())
    if name == "Notification":
        return f"🔔 [{project}] {event.get('message', 'Claude ждёт вашего ответа')}"
    if name == "Stop":
        last = (event.get("last_assistant_message") or "").strip()
        return f"✅ [{project}] Claude закончил задачу" + (f"\n\n{last}" if last else "")
    return f"ℹ️ [{project}] {name}"


def main():
    args = sys.argv[1:]
    if args[:1] == ["--hook"]:
        try:
            send(hook_text(json.load(sys.stdin)))
        except Exception as e:  # a notification problem must not break Claude
            print(f"notify_telegram: {e}", file=sys.stderr)
        return 0
    text = " ".join(args) if args else sys.stdin.read()
    if not text.strip():
        print("notify_telegram: empty message", file=sys.stderr)
        return 2
    try:
        send(text)
    except Exception as e:
        print(f"notify_telegram: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
