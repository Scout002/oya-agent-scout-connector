"""Fact-check a draft message against source evidence.

Reads {draft, evidence, strict?} from INPUT_JSON, calls Claude Haiku once
to enumerate the concrete claims in the draft and locate each in the
evidence, returns a structured pass/fail result.

`direct_relay: true` so the verifier's JSON reaches the parent agent
verbatim — the wrap_with_standalone_llm wrapper is exactly the kind of
LLM hop that has hallucinated tool results in the past, and this skill
exists to catch those hallucinations rather than introduce another one.

Note: no `from __future__ import annotations` here on purpose — the
sandbox executor prepends env-injection statements before single-file
scripts, which would put the future-import after real statements and
SyntaxError. The executor now hoists future imports, but this skill
ships without one to keep it portable to older runners.
"""
import json
import os
import re
import sys


_MODEL = "claude-haiku-4-5-20251001"
_MAX_DRAFT = 8000   # chars
_MAX_EVIDENCE = 60000  # chars — Haiku 4.5 has plenty of context but bound it
# Output budget. Was 2000, which a multi-claim draft overran: the response was cut
# off mid-string and surfaced as "verifier_returned_non_json", which pointed at the
# wrong thing entirely (2026-08-20, "SZ Accounting Product & Success Engine").
_MAX_OUTPUT_TOKENS = 8000


def _emit(payload: dict, exit_code: int | None = None) -> None:
    # A completed verification ALWAYS exits 0 — including when passed=false.
    # `passed=false` means "the draft has unsupported claims", which is the
    # skill's expected, documented output (the agent reads it from JSON via
    # direct_relay and rewrites the draft), NOT an execution failure. Exiting
    # non-zero there made the sandbox executor treat a correct result as a
    # crash: it fired the ops failure-alert email + Slack notice and raised
    # SkillExecutionError, killing the agent run. Only genuine errors (bad
    # input, missing key, verifier call failed, non-JSON) exit non-zero, and
    # every such path passes exit_code=1 explicitly below.
    print(json.dumps(payload, ensure_ascii=False))
    sys.exit(exit_code if exit_code is not None else 0)


def _strip_code_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        # ```json\n...\n``` or ```\n...\n```
        m = re.match(r"^```(?:json)?\s*\n(.*?)\n```\s*$", t, re.DOTALL)
        if m:
            return m.group(1).strip()
    return t


def _build_prompt(draft: str, evidence: str, strict: bool, compact: bool = False) -> str:
    strict_clause = (
        "STRICT MODE: flag any claim that requires inference, even reasonable arithmetic — "
        "the value must appear DIRECTLY in evidence."
        if strict else
        "RELAXED MODE: accept obvious restatements (e.g. summing two listed counts, "
        "trivial unit conversion). Still flag anything that materially differs from evidence."
    )
    compact_clause = (
        "\n\nThe previous attempt ran out of output room. Be MAXIMALLY terse: omit "
        "evidence_snippet and reason for every supported claim, and shorten claim "
        "spans."
        if compact else ""
    )
    return f"""You are a strict fact-checker. List every CONCRETE CLAIM in the DRAFT — \
numbers, percentages, counts, durations, dates, times, names, emails, IDs, URLs, \
status statements (e.g. "X completed", "Y failed", "Z is overdue").

For each claim, find a supporting span in the EVIDENCE.

{strict_clause}

Mark `supported = false` when:
- the value appears nowhere in evidence
- evidence contradicts the draft
- the claim is an inference the evidence doesn't directly state (and STRICT MODE is on)

Output ONLY this JSON (no prose, no code fence):
{{
  "claims": [
    {{
      "claim": "<exact span from draft, max 120 chars>",
      "supported": true,
      "evidence_snippet": "<exact span from evidence, max 160 chars>",
      "reason": "<max 100 chars>"
    }}
  ]
}}

Stay inside those length limits. Truncated JSON is unusable, so keep every field
short: for a SUPPORTED claim the snippet may be omitted entirely, and `reason` may
be omitted. Spend the detail only on claims you mark unsupported.{compact_clause}

If the DRAFT contains no concrete claims (pure templated text), return {{"claims": []}}.

DRAFT:
{draft}

EVIDENCE:
{evidence}"""


def main() -> None:
    inp = json.loads(os.environ.get("INPUT_JSON") or "{}")
    draft = (inp.get("draft") or "").strip()
    evidence = (inp.get("evidence") or "").strip()
    strict = bool(inp.get("strict", True))

    if not draft:
        _emit({"ok": False, "passed": False, "error": "draft_required"}, exit_code=1)
    if not evidence:
        _emit({"ok": False, "passed": False, "error": "evidence_required",
               "detail": "Pass the raw tool output the draft is derived from."}, exit_code=1)
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        _emit({"ok": False, "passed": False, "error": "no_anthropic_key"}, exit_code=1)

    # Hard cap input sizes to stay well under context limits and keep latency low.
    if len(draft) > _MAX_DRAFT:
        draft = draft[:_MAX_DRAFT] + "\n...(draft truncated)"
    if len(evidence) > _MAX_EVIDENCE:
        evidence = evidence[:_MAX_EVIDENCE] + "\n...(evidence truncated)"

    import anthropic  # type: ignore[import-not-found]
    client = anthropic.Anthropic(api_key=api_key)

    def _ask(compact: bool):
        """One verifier call. Returns (text, truncated)."""
        try:
            resp = client.messages.create(
                model=_MODEL,
                max_tokens=_MAX_OUTPUT_TOKENS,
                messages=[{"role": "user", "content":
                           _build_prompt(draft, evidence, strict, compact=compact)}],
            )
        except Exception as exc:
            _emit({"ok": False, "passed": False, "error": "verifier_call_failed",
                   "detail": f"{type(exc).__name__}: {exc}"}, exit_code=1)
        body = ""
        for block in (resp.content or []):
            if getattr(block, "type", "") == "text":
                body += getattr(block, "text", "") or ""
        # `max_tokens` means the model was cut off mid-sentence, so the JSON is
        # unparseable through no fault of its own. Knowing that is the difference
        # between "the verifier misbehaved" and "we did not give it enough room",
        # which is what a JSONDecodeError alone hid.
        return _strip_code_fence(body), getattr(resp, "stop_reason", "") == "max_tokens"

    text, truncated = _ask(compact=False)
    if truncated:
        # Retry once, asking it to drop the snippets it only needs for failures.
        # Most claims are supported, so this is a large size win.
        text, truncated = _ask(compact=True)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        if truncated:
            _emit({"ok": False, "passed": False, "error": "verifier_output_truncated",
                   "detail": f"The verifier hit the {_MAX_OUTPUT_TOKENS}-token output "
                             "cap twice, even in compact mode. The draft probably has "
                             "too many claims to check in one pass; split it.",
                   "raw": text[:500]}, exit_code=1)
        _emit({"ok": False, "passed": False, "error": "verifier_returned_non_json",
               "detail": str(e), "raw": text[:500]}, exit_code=1)

    claims = parsed.get("claims") or []
    if not isinstance(claims, list):
        _emit({"ok": False, "passed": False, "error": "verifier_bad_shape",
               "raw": text[:500]}, exit_code=1)

    unsupported = [c for c in claims if isinstance(c, dict) and not c.get("supported")]
    passed = len(unsupported) == 0
    _emit({
        "ok": True,
        "passed": passed,
        "claims": claims,
        "unsupported_count": len(unsupported),
        "unsupported_claims": unsupported,
        "summary": f"{len(claims) - len(unsupported)}/{len(claims)} claims supported"
                   if claims else "no concrete claims in draft",
        "model": _MODEL,
    })


if __name__ == "__main__":
    main()
