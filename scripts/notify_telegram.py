#!/usr/bin/env python3
"""Send a message to Telegram via the Bot API.

Usage:
  notify_telegram.py "text"          # send the given text
  echo "text" | notify_telegram.py   # send text from stdin
  notify_telegram.py --chat ID "text"  # send only to chat ID
  notify_telegram.py --hook          # read Claude Code hook JSON from stdin

Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from the environment.
TELEGRAM_CHAT_ID may hold several ids separated by commas: "111,222".
Long texts are split into several messages on line boundaries.
In --hook mode it never fails the hook: errors go to stderr, exit code is 0.
Hooks are skipped when the file .no-telegram-hooks exists in the project root
(scheduled digest runs create it so that only the digest is sent).
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

MAX_LEN = 4000  # Telegram limit is 4096 characters per message


def send_one(token, chat_id, text):
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        with urllib.request.urlopen(url, data=data, timeout=15) as resp:
            body = json.load(resp)
    except urllib.error.HTTPError as e:
        body = json.load(e)
    if not body.get("ok"):
        raise RuntimeError(f"chat {chat_id}: {body.get('description')}")


def split(text):
    parts, cur = [], ""
    for line in text.splitlines(keepends=True):
        while len(line) > MAX_LEN:  # a single overlong line is cut hard
            parts.append(cur + line[: MAX_LEN - len(cur)])
            line, cur = line[MAX_LEN - len(cur):], ""
        if len(cur) + len(line) > MAX_LEN:
            parts.append(cur)
            cur = ""
        cur += line
    if cur.strip():
        parts.append(cur)
    return parts


def send(text, chat_ids=None):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if chat_ids is None:
        chat_ids = [c.strip() for c in os.environ.get("TELEGRAM_CHAT_ID", "").split(",") if c.strip()]
    if not token or not chat_ids:
        raise RuntimeError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not set")
    errors = []
    for chat_id in chat_ids:  # one bad chat must not block the others
        try:
            for part in split(text):
                send_one(token, chat_id, part)
        except Exception as e:
            errors.append(str(e))
    if errors:
        raise RuntimeError("Telegram API error: " + "; ".join(errors))


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
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        if os.path.exists(os.path.join(project_dir, ".no-telegram-hooks")):
            return 0
        try:
            send(hook_text(json.load(sys.stdin)))
        except Exception as e:  # a notification problem must not break Claude
            print(f"notify_telegram: {e}", file=sys.stderr)
        return 0
    chat_ids = None
    if args[:1] == ["--chat"] and len(args) >= 2:
        chat_ids, args = [args[1]], args[2:]
    text = " ".join(args) if args else sys.stdin.read()
    if not text.strip():
        print("notify_telegram: empty message", file=sys.stderr)
        return 2
    try:
        send(text, chat_ids)
    except Exception as e:
        print(f"notify_telegram: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
