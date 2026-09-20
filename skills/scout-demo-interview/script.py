"""scout-demo-interview - mint a live Scout interview link for a mock role play."""
import json
import os
import sys

import httpx

DEFAULT_BASE_URL = "https://www.sendscout.ai"
DEFAULT_PATH = "/api/admin/demo/interview-invite"
URL_KEYS = (
    "invite_url",
    "interview_url",
    "url",
    "link",
    "interview_link",
    "share_url",
    "public_url",
)


def _find_url(body):
    if not isinstance(body, dict):
        return None
    for key in URL_KEYS:
        val = body.get(key)
        if isinstance(val, str) and val.startswith("http"):
            return val
    for val in body.values():
        if isinstance(val, dict):
            found = _find_url(val)
            if found:
                return found
    return None


def main():
    inp = json.loads(os.environ.get("INPUT_JSON", "{}"))
    bearer = (os.environ.get("SENDSCOUT_ADMIN_BEARER") or "").strip()
    base_url = ((os.environ.get("SENDSCOUT_BASE_URL") or "").strip() or DEFAULT_BASE_URL).rstrip("/")
    path = (os.environ.get("SENDSCOUT_DEMO_INVITE_PATH") or "").strip() or DEFAULT_PATH
    if not path.startswith("/"):
        path = "/" + path
    endpoint = base_url + path

    if inp.get("probe"):
        print(
            json.dumps(
                {
                    "ok": True,
                    "probe": True,
                    "endpoint": endpoint,
                    "bearer_configured": bool(bearer),
                }
            )
        )
        return

    if not bearer:
        print(
            json.dumps(
                {
                    "ok": False,
                    "reason": "SENDSCOUT_ADMIN_BEARER is not set on this agent. Ask Nick to add the "
                    "Send Scout admin bearer token to the scout-demo-interview skill credentials.",
                    "endpoint": endpoint,
                }
            )
        )
        return

    role_title = (inp.get("role_title") or "").strip()
    contact_name = (inp.get("contact_name") or "").strip()
    if not role_title or not contact_name:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "role_title and contact_name are required; finish the intake before minting a link",
                    "expected": True,
                }
            )
        )
        return

    payload = {
        "demo": True,
        "source": "scout-connector",
        "role_title": role_title,
        "contact_name": contact_name,
    }
    for key in ("company", "linkedin_url", "contact_email", "must_haves", "comp_band", "location"):
        val = (inp.get(key) or "").strip()
        if val:
            payload[key] = val

    headers = {
        "authorization": "Bearer %s" % bearer,
        "content-type": "application/json",
        "accept": "application/json",
    }

    try:
        with httpx.Client(timeout=60, follow_redirects=True) as client:
            resp = client.post(endpoint, headers=headers, json=payload)
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "reason": "could not reach %s (%s: %s)" % (endpoint, type(exc).__name__, exc),
                    "endpoint": endpoint,
                }
            )
        )
        return

    try:
        body = resp.json()
    except Exception:
        body = {"raw_text": resp.text[:1000]}

    if resp.status_code == 404:
        print(
            json.dumps(
                {
                    "ok": False,
                    "reason": "route %s does not exist on %s. Ask Nick for the correct demo "
                    "interview-invite route and set SENDSCOUT_DEMO_INVITE_PATH on this skill."
                    % (path, base_url),
                    "status": 404,
                    "endpoint": endpoint,
                }
            )
        )
        return

    if resp.status_code in (401, 403):
        print(
            json.dumps(
                {
                    "ok": False,
                    "reason": "Send Scout rejected the admin bearer token (HTTP %s). Ask Nick to "
                    "refresh SENDSCOUT_ADMIN_BEARER on this skill." % resp.status_code,
                    "status": resp.status_code,
                    "endpoint": endpoint,
                }
            )
        )
        return

    invite_url = _find_url(body)
    if resp.status_code >= 400 or not invite_url:
        print(
            json.dumps(
                {
                    "ok": False,
                    "reason": "no interview link came back (HTTP %s)" % resp.status_code,
                    "status": resp.status_code,
                    "endpoint": endpoint,
                    "raw": body,
                }
            )
        )
        return

    print(json.dumps({"ok": True, "invite_url": invite_url, "status": resp.status_code, "raw": body}))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}))
        sys.exit(0)
