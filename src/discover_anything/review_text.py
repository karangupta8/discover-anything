"""Shared markers for review stubs, so gates can tell stubs from real reviews."""

REVIEW_PLACEHOLDER = "<paste the reviewer's findings>"
RESPONSE_HEADER = "| # | Finding | Fixed / disputed | What changed or why | Evidence |"


MIN_REVIEW_WORDS = 40
MIN_RESPONSE_WORDS = 20


def _words(text: str) -> int:
    return len([w for w in text.split() if any(c.isalnum() for c in w)])


def is_review_filled(text: str) -> bool:
    return REVIEW_PLACEHOLDER not in text and _words(text) >= MIN_REVIEW_WORDS


def _cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def is_response_filled(text: str) -> bool:
    """A response table row needs a finding and a disposition; prose needs real length."""
    rows = [ln for ln in text.splitlines() if ln.strip().startswith("|")]
    data_rows = [r for r in rows if r.strip() != RESPONSE_HEADER and not set(r.strip()) <= set("|- :")
                 and _cells(r)[0].lower() not in ("#", "")]
    answered = [r for r in data_rows if len(_cells(r)) >= 3 and all(_cells(r)[1:3])]
    if answered:
        return True
    prose = "\n".join(ln for ln in text.splitlines() if not ln.strip().startswith(("|", "#")))
    return RESPONSE_HEADER not in text and _words(prose) >= MIN_RESPONSE_WORDS
