import os
import json
import httpx

# Load inputs
inp = json.loads(os.environ.get("INPUT_JSON", "{}"))

# Config from resource_requirements
WEBHOOK_URL = os.environ.get("SCOUT_WEBHOOK_URL", "https://yhhvwpadhkjjqafctngj.supabase.co/functions/v1/scout-crm-webhook")
WEBHOOK_SECRET = os.environ.get("SCOUT_WEBHOOK_SECRET", "")

headers = {
    "Content-Type": "application/json",
    "x-api-key": WEBHOOK_SECRET,
}

full_name = inp.get("full_name", "")
email = inp.get("email")
linkedin_url = inp.get("linkedin_url")
company = inp.get("company")
title = inp.get("title")
x_handle = inp.get("x_handle")
instagram_handle = inp.get("instagram_handle")
tiktok_handle = inp.get("tiktok_handle")
agent_source = inp.get("agent_source", "bd_agent")
lead_type = inp.get("lead_type", "employer")
channel = inp.get("channel", "other")
message_preview = inp.get("message_preview")
response_received = inp.get("response_received", False)
status_update = inp.get("status_update")
warmth = inp.get("warmth")

results = []

with httpx.Client(timeout=15) as client:
    # Step 1: Try to find existing lead by email or linkedin
    lead_id = None

    if email or linkedin_url:
        # Try add_lead_and_touch — if the lead already exists by email,
        # the webhook will error, so we'll fall back to log_touch
        pass

    # Step 1: Create lead + first touch in one call
    payload = {
        "action": "add_lead_and_touch",
        "data": {
            "lead": {
                "full_name": full_name,
                "email": email,
                "linkedin_url": linkedin_url,
                "x_handle": x_handle,
                "instagram_handle": instagram_handle,
                "tiktok_handle": tiktok_handle,
                "company": company,
                "title": title,
                "agent_source": agent_source,
                "lead_type": lead_type,
                "channel": "linkedin" if "linkedin" in channel else "x" if "x_" in channel else "instagram" if "instagram" in channel else "tiktok" if "tiktok" in channel else "email" if "email" in channel else "both",
            },
            "touch": {
                "agent_source": agent_source,
                "channel": channel,
                "message_preview": message_preview or "",
                "response_received": response_received,
            }
        }
    }

    resp = client.post(WEBHOOK_URL, json=payload, headers=headers)

    if resp.status_code == 200:
        data = resp.json()
        lead_id = data.get("lead", {}).get("id")
        results.append(f"Created lead '{full_name}' and logged {channel} touch")
    else:
        # Lead might already exist — try just logging a touch
        touch_payload = {
            "action": "log_touch",
            "data": {
                "lead_email": email,
                "lead_linkedin_url": linkedin_url,
                "agent_source": agent_source,
                "channel": channel,
                "message_preview": message_preview or "",
                "response_received": response_received,
            }
        }
        touch_resp = client.post(WEBHOOK_URL, json=touch_payload, headers=headers)

        if touch_resp.status_code == 200:
            touch_data = touch_resp.json()
            lead_id = touch_data.get("touch", {}).get("lead_id")
            results.append(f"Logged {channel} touch for existing lead '{full_name}'")
        else:
            results.append(f"Warning: Could not log touch — {touch_resp.text}")

    # Step 2: Update status if provided
    if status_update and (lead_id or email or linkedin_url):
        status_payload = {
            "action": "update_status",
            "data": {
                "lead_id": lead_id,
                "lead_email": email,
                "lead_linkedin_url": linkedin_url,
                "status": status_update,
            }
        }
        if warmth:
            status_payload["data"]["warmth"] = warmth

        status_resp = client.post(WEBHOOK_URL, json=status_payload, headers=headers)
        if status_resp.status_code == 200:
            results.append(f"Updated status to '{status_update}'" + (f" (warmth: {warmth})" if warmth else ""))
        else:
            results.append(f"Warning: Status update failed — {status_resp.text}")
    elif warmth and (lead_id or email or linkedin_url):
        # Just update warmth without status change
        warmth_payload = {
            "action": "update_status",
            "data": {
                "lead_id": lead_id,
                "lead_email": email,
                "lead_linkedin_url": linkedin_url,
                "status": "contacted",  # keep current
                "warmth": warmth,
            }
        }
        client.post(WEBHOOK_URL, json=warmth_payload, headers=headers)

output = {
    "success": True,
    "lead": full_name,
    "company": company,
    "actions": results,
}

print(json.dumps(output))
