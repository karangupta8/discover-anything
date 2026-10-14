"""Shared markers for review stubs, so gates can tell stubs from real reviews."""

REVIEW_PLACEHOLDER = "<paste the reviewer's findings>"
RESPONSE_HEADER = "| # | Finding | Fixed / disputed | What changed or why | Evidence |"


def is_review_filled(text: str) -> bool:
    return REVIEW_PLACEHOLDER not in text and len(text.strip()) > 80


def is_response_filled(text: str) -> bool:
    rows = [ln for ln in text.splitlines() if ln.strip().startswith("|")]
    data_rows = [r for r in rows if r.strip() != RESPONSE_HEADER and not set(r) <= set("|- :")]
    return bool(data_rows) or (RESPONSE_HEADER not in text and len(text.strip()) > 80)
