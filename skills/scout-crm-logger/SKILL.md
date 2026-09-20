---
name: scout-crm-logger
display_name: "Scout CRM Logger"
description: "Logs outreach activity (leads and touches) to the Scout CRM dashboard. Call this after every outreach action — LinkedIn, X, Instagram, TikTok, email, or any follow-up — to track the lead and touch in the CRM pipeline."
category: general
icon: database
skill_type: sandbox
catalog_type: addon
tool_schema:
  name: log_crm_activity
  description: "Log a lead and outreach touch to the Scout CRM. Call this EVERY TIME you reach out to someone — whether it's a LinkedIn connection request, DM, InMail, X post/DM, Instagram DM, TikTok DM, email, or follow-up. Include the contact's details, social handles, and what type of outreach you performed."
  parameters:
    type: object
    properties:
      full_name:
        type: "string"
        description: "Full name of the person you reached out to"
      email:
        type: "string"
        description: "Email address if known"
      linkedin_url:
        type: "string"
        description: "LinkedIn profile URL if known"
      company:
        type: "string"
        description: "Company name"
      title:
        type: "string"
        description: "Job title"
      agent_source:
        type: "string"
        description: "Which agent is logging this: 'bd_agent' for employer outreach or 'talent_scout' for talent outreach"
        enum: ["bd_agent", "talent_scout"]
      lead_type:
        type: "string"
        description: "Type of lead: 'employer' for companies/hiring teams or 'talent' for candidates"
        enum: ["employer", "talent"]
      x_handle:
        type: "string"
        description: "X (Twitter) handle if known, without the @ symbol"
      instagram_handle:
        type: "string"
        description: "Instagram handle if known, without the @ symbol"
      tiktok_handle:
        type: "string"
        description: "TikTok handle if known, without the @ symbol"
      channel:
        type: "string"
        description: "The outreach channel used for this touch"
        enum: ["linkedin_connection", "linkedin_dm", "linkedin_inmail", "x_dm", "x_post", "x_reply", "instagram_dm", "instagram_comment", "tiktok_dm", "tiktok_comment", "email", "follow_up_email", "phone", "other"]
      message_preview:
        type: "string"
        description: "Brief preview of the message you sent (first ~100 chars)"
      response_received:
        type: "boolean"
        description: "Did the person respond to this outreach? Default false"
      status_update:
        type: "string"
        description: "If the lead's status changed, set it here. Only set if you know the status changed."
        enum: ["replied", "interested", "signed_up", "not_interested", "unresponsive"]
      warmth:
        type: "string"
        description: "Lead warmth level based on engagement signals"
        enum: ["cold", "warm", "hot"]
    required: [full_name, agent_source, lead_type, channel]
requirements: "httpx"
resource_requirements:
  - env_var: SCOUT_WEBHOOK_URL
    name: "Scout CRM Webhook URL"
    description: "The Supabase Edge Function URL for the Scout CRM webhook"
  - env_var: SCOUT_WEBHOOK_SECRET
    name: "Scout CRM Webhook Secret"
    description: "The x-api-key value for authenticating with the webhook"
---

# Scout CRM Logger

Logs every outreach action to the Scout CRM dashboard at sendscout.ai/admin/crm.

Call this skill **every time** you:
- Send a LinkedIn connection request, DM, or InMail
- Send an X (Twitter) DM, post, or reply
- Send an Instagram DM or comment
- Send a TikTok DM or comment
- Send an email or follow-up email
- Receive a response from a lead
- A lead's status changes (replied, interested, signed up, etc.)

The skill automatically handles creating new leads and logging touches. If a lead already exists (matched by email or LinkedIn URL), it logs a new touch against the existing lead rather than creating a duplicate.
