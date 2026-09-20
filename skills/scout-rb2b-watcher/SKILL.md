---
name: scout-rb2b-watcher
description: "Read the RB2B Slack channel (#rb2b-scout) for identified website-visitor alerts and return the ones not yet handled, each with its LinkedIn profile URL and raw text. Also marks a visitor handled by posting a status reply in that message's thread, which is the dedupe record. Use list_new at the start of every invite run and mark_handled immediately after each connection request is sent or skipped."
category: sales
icon: radar
skip_summarization_on_structured: true
resource_requirements:
  - name: Slack Bot Token
    env_var: SLACK_BOT_TOKEN
    description: "Slack bot OAuth token (xoxb-...), injected by the connected Slack gateway."
  - name: RB2B channel id
    env_var: RB2B_CHANNEL_ID
    optional: true
    description: "Default Slack channel id for RB2B visitor alerts. Falls back to C0C332FNR0C when unset."
tool_schema:
  name: scout_rb2b_watcher
  description: "List unhandled RB2B visitor alerts from Slack, or mark one handled with a threaded status reply."
  parameters:
    type: object
    required:
      - action
    properties:
      action:
        type: string
        enum:
          - list_new
          - mark_handled
        description: "list_new returns unhandled visitor alerts (no other arguments required). mark_handled REQUIRES message_ts and status, and posts the status as a thread reply on that alert."
      channel:
        type: string
        description: "Slack channel id, e.g. C0C332FNR0C. Optional; defaults to the RB2B_CHANNEL_ID env var."
      message_ts:
        type: string
        description: "REQUIRED for mark_handled. The Slack ts of the visitor alert, exactly as list_new returned it (e.g. 1758300000.123456)."
      status:
        type: string
        description: "REQUIRED for mark_handled. Short status line to post in the thread, e.g. 'invite sent to linkedin.com/in/jane-doe' or 'skipped: already a connection'."
      lookback_hours:
        type: integer
        description: "How far back to scan. Default 24, max 168."
      limit:
        type: integer
        description: "Max messages to scan. Default 50, max 200."
---

# scout-rb2b-watcher

The lead source for the Scout Connector funnel. RB2B posts one Slack message per identified
sendscout.ai visitor; this skill turns that channel into a clean work queue.

## list_new

Scans the channel and returns only alerts that carry a LinkedIn profile URL **and** have no
`[scout-connector]` reply in their thread. Each item has:

- `message_ts` — pass this back to `mark_handled`
- `linkedin_urls` — every `linkedin.com/in/...` URL found in the message, blocks and attachments
- `text` — the raw alert text, so you can read the name, company and pages visited yourself
- `permalink_hint` — channel and ts for reference

Anything already replied to is filtered out, so calling `list_new` twice in a row is safe.

## mark_handled

Posts `[scout-connector] <status>` as a thread reply on the alert. This is the dedupe record —
call it after **every** outcome, including skips, or the visitor will be picked up again on the
next run. Mark handled as soon as the send succeeds, before moving to the next visitor.
