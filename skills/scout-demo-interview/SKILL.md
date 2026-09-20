---
name: scout-demo-interview
description: "Mint a live Scout interview link at the end of a mock role play, so a prospect can click through the candidate experience for the role they just described. Call this once per role play, after the intake is confirmed. Never invent or guess an interview URL - if this returns ok=false, tell the prospect the link is coming and alert Nick."
category: sales
icon: link
skip_summarization_on_structured: true
resource_requirements:
  - name: Send Scout admin bearer token
    env_var: SENDSCOUT_ADMIN_BEARER
    description: "Bearer token for the Send Scout admin API routes, stored in this agent's skill credentials."
  - name: Send Scout base URL
    env_var: SENDSCOUT_BASE_URL
    optional: true
    description: "Base URL for the Send Scout app, no trailing slash. Defaults to https://www.sendscout.ai."
  - name: Demo invite route
    env_var: SENDSCOUT_DEMO_INVITE_PATH
    optional: true
    description: "Path of the API route that creates a demo role and returns an interview invite URL. Defaults to /api/admin/demo/interview-invite."
tool_schema:
  name: scout_demo_interview
  description: "Create a demo role from a prospect's intake and return a live interview link to send them."
  parameters:
    type: object
    required:
      - role_title
      - contact_name
    properties:
      role_title:
        type: string
        description: "The role the prospect said they are hiring for, in their words, e.g. 'Enterprise AE, fintech'."
      contact_name:
        type: string
        description: "The prospect's full name as it appears on their LinkedIn profile."
      company:
        type: string
        description: "The prospect's company, from the RB2B alert or their profile."
      linkedin_url:
        type: string
        description: "The prospect's LinkedIn profile URL, e.g. https://www.linkedin.com/in/jane-doe."
      contact_email:
        type: string
        description: "The prospect's email if RB2B supplied one. Optional."
      must_haves:
        type: string
        description: "The two or three disqualifiers they gave during intake, as one line."
      comp_band:
        type: string
        description: "Comp band they named, as one line. Optional."
      location:
        type: string
        description: "Location or remote policy they named. Optional."
      probe:
        type: boolean
        description: "Set true to report the configured base URL and route without creating anything. Use only when Nick asks you to check the setup."
---

# scout-demo-interview

The payoff of the Scout Connector role play. Takes what the prospect told you in LinkedIn DMs and
returns a real interview link they can open and walk through as if they were the candidate.

## Rules

- Call it **once** per role play, after the prospect has confirmed your intake summary.
- Send the returned `invite_url` verbatim. Never shorten, rewrite, or construct a URL yourself.
- If the result is `ok: false`, say the link is on its way, post the `reason` to #rb2b-scout for
  Nick, and do not retry more than once.
- `probe: true` tells you which base URL and route the skill is pointed at. It creates nothing.

## Result

`{ok: true, invite_url: "...", raw: {...}}` on success. On failure, `ok` is false and `reason`
explains what to tell Nick — most often that the route or the admin bearer token is not configured
on this agent yet.
