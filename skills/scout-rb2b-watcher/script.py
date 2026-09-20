"""scout-rb2b-watcher - queue of unhandled RB2B visitor alerts in Slack."""
import json
import os
import re
import sys
import time

import httpx

SLACK_API = "https://slack.com/api"
DEFAULT_CHANNEL = "C0C332FNR0C"
MARKER = "[scout-connector]"
LI_RE = re.compile(r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/in/[A-Za-z0-9\-_%\.]+", re.I)


def _get(client, method, params, token):
    r = client.get(
        "%s/%s" % (SLACK_API, method),
        params=params,
        headers={"Authorization": "Bearer %s" % token},
    )
    return r.json()


def _post(client, method, payload, token):
    r = client.post(
        "%s/%s" % (SLACK_API, method),
        json=payload,
        headers={
            "Authorization": "Bearer %s" % token,
            "Content-Type": "application/json; charset=utf-8",
        },
    )
    return r.json()


def _urls(message):
    blob = json.dumps(message)
    seen = []
    for raw in LI_RE.findall(blob):
        url = raw.rstrip("/").split("?")[0]
        if url not in seen:
            seen.append(url)
    return seen


def list_new(client, token, channel, lookback_hours, limit):
    oldest = time.time() - (lookback_hours * 3600)
    data = _get(
        client,
        "conversations.history",
        {"channel": channel, "limit": limit, "oldest": "%.6f" % oldest},
        token,
    )
    if not data.get("ok"):
        return {
            "ok": False,
            "error": "slack conversations.history failed: %s. If it says not_in_channel, "
            "the Oya bot must be invited to the channel first." % data.get("error"),
            "expected": True,
        }

    pending = []
    skipped_handled = 0
    skipped_no_url = 0

    for msg in data.get("messages", []):
        if msg.get("subtype") in ("channel_join", "channel_leave"):
            continue
        urls = _urls(msg)
        if not urls:
            skipped_no_url += 1
            continue

        ts = msg.get("ts")
        if int(msg.get("reply_count", 0) or 0) > 0:
            replies = _get(
                client,
                "conversations.replies",
                {"channel": channel, "ts": ts, "limit": 50},
                token,
            )
            handled = False
            if replies.get("ok"):
                for rep in replies.get("messages", [])[1:]:
                    if MARKER in json.dumps(rep):
                        handled = True
                        break
            if handled:
                skipped_handled += 1
                continue

        pending.append(
            {
                "message_ts": ts,
                "linkedin_urls": urls,
                "text": (msg.get("text") or "")[:1500],
                "raw": json.dumps(msg)[:2500],
                "permalink_hint": "%s/%s" % (channel, ts),
            }
        )

    return {
        "ok": True,
        "channel": channel,
        "pending_count": len(pending),
        "pending": pending,
        "skipped_already_handled": skipped_handled,
        "skipped_no_linkedin_url": skipped_no_url,
    }


def mark_handled(client, token, channel, message_ts, status):
    data = _post(
        client,
        "chat.postMessage",
        {
            "channel": channel,
            "thread_ts": message_ts,
            "text": "%s %s" % (MARKER, status),
        },
        token,
    )
    if not data.get("ok"):
        return {
            "ok": False,
            "error": "slack chat.postMessage failed: %s" % data.get("error"),
            "expected": True,
        }
    return {"ok": True, "marked": message_ts, "status": status}


def main():
    inp = json.loads(os.environ.get("INPUT_JSON", "{}"))
    token = (os.environ.get("SLACK_BOT_TOKEN") or "").strip()
    channel = (
        (inp.get("channel") or "").strip()
        or (os.environ.get("RB2B_CHANNEL_ID") or "").strip()
        or DEFAULT_CHANNEL
    )
    action = (inp.get("action") or "list_new").strip().lower()

    if not token:
        print(json.dumps({"ok": False, "error": "SLACK_BOT_TOKEN not set - connect the Slack gateway"}))
        return

    lookback = int(inp.get("lookback_hours") or 24)
    lookback = max(1, min(lookback, 168))
    limit = int(inp.get("limit") or 50)
    limit = max(1, min(limit, 200))

    with httpx.Client(timeout=45, follow_redirects=True) as client:
        if action == "list_new":
            print(json.dumps(list_new(client, token, channel, lookback, limit)))
            return
        if action == "mark_handled":
            message_ts = (inp.get("message_ts") or "").strip()
            status = (inp.get("status") or "").strip()
            if not message_ts or not status:
                print(
                    json.dumps(
                        {
                            "ok": False,
                            "error": "mark_handled needs message_ts and status; take message_ts from a list_new result",
                            "expected": True,
                        }
                    )
                )
                return
            print(json.dumps(mark_handled(client, token, channel, message_ts, status)))
            return

        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "unknown action '%s'; use list_new or mark_handled" % action,
                    "expected": True,
                }
            )
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}))
        sys.exit(0)
