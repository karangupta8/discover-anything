"""Collapse reprints: find near-duplicate passages before counting events.

The same newspaper story travels across many papers. Counting each reprint as
a separate report inflates the evidence. Word-shingle Jaccard similarity is
crude but robust to OCR noise and transparent to check by hand.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

MAX_PASSAGES = 20_000  # O(n^2) comparison; block or pre-filter larger sets


def shingles(text: str, size: int = 5) -> frozenset[str]:
    words = re.findall(r"\w+", text.lower())
    if len(words) < size:
        return frozenset({" ".join(words)}) if words else frozenset()
    return frozenset(" ".join(words[i:i + size]) for i in range(len(words) - size + 1))


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def near_duplicates(texts: Sequence[str], threshold: float = 0.5,
                    size: int = 5) -> tuple[tuple[int, int, float], ...]:
    """Pairs (i, j, similarity) with similarity >= threshold, i < j."""
    if not 0 < threshold <= 1:
        raise ValueError("threshold must be in (0, 1]")
    if len(texts) > MAX_PASSAGES:
        raise ValueError(f"{len(texts):,} passages; split by date or source first "
                         f"(limit {MAX_PASSAGES:,})")
    sets = [shingles(t, size) for t in texts]
    pairs = []
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            sim = jaccard(sets[i], sets[j])
            if sim >= threshold:
                pairs.append((i, j, round(sim, 4)))
    return tuple(pairs)


def group_duplicates(n: int, pairs: Sequence[tuple[int, int, float]]) -> tuple[tuple[int, ...], ...]:
    """Connected groups of indices; singletons included. Each group is one event."""
    parent = list(range(n))

    def root(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, j, _ in pairs:
        parent[root(i)] = root(j)
    groups: dict[int, list[int]] = {}
    for idx in range(n):
        groups.setdefault(root(idx), []).append(idx)
    return tuple(tuple(g) for g in sorted(groups.values(), key=lambda g: g[0]))
