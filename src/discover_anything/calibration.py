"""Domain-neutral calibration: known-answer recovery and judge agreement.

``score_known_answers`` is the "buried wristwatch": did the pipeline find the
things already known to be in the data? ``judge_agreement`` checks a cheap
judge model against a labelled set before it is trusted to filter a corpus.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

DEFAULT_ALIASES = (1.0, 0.5, 2.0)


def _value_matches(found: float, known: float, rel_tol: float,
                   aliases: Sequence[float]) -> bool:
    if known == 0:
        return abs(found) <= rel_tol
    return any(abs(found / (known * k) - 1) <= rel_tol for k in aliases)


def score_known_answers(known: Sequence[Mapping[str, Any]], found: Sequence[Mapping[str, Any]],
                        key: str, value: str | None = None, rel_tol: float = 0.01,
                        aliases: Sequence[float] = DEFAULT_ALIASES) -> dict[str, Any]:
    """Match found items to known answers by key, optionally checking a numeric value.

    Returns recall, and the lists of recovered, missed and wrong-value answers.
    A known answer found with a value outside tolerance (and its aliases)
    counts as wrong, not recovered.
    """
    if not known:
        raise ValueError("known answers list is empty; calibration needs at least one")
    found_by_key: dict[str, list[Mapping[str, Any]]] = {}
    for item in found:
        found_by_key.setdefault(str(item[key]).strip(), []).append(item)
    recovered, missed, wrong = [], [], []
    for answer in known:
        k = str(answer[key]).strip()
        hits = found_by_key.get(k, [])
        if not hits:
            missed.append(k)
        elif value is None:
            recovered.append(k)
        elif any(_value_matches(float(h[value]), float(answer[value]), rel_tol, aliases)
                 for h in hits):
            recovered.append(k)
        else:
            wrong.append({"key": k, "known": float(answer[value]),
                          "found": [float(h[value]) for h in hits]})
    return {"n_known": len(known), "recall": len(recovered) / len(known),
            "recovered": recovered, "missed": missed, "wrong_value": wrong,
            "rel_tol": rel_tol, "aliases": list(aliases)}


def judge_agreement(expected: Mapping[str, str], predicted: Mapping[str, str]) -> dict[str, Any]:
    """Compare judge answers with labels, keyed by item id.

    Returns accuracy, Cohen's kappa, per-label precision/recall, the confusion
    counts, and ids with no prediction.
    """
    ids = [i for i in expected if i in predicted]
    if not ids:
        raise ValueError("no item ids in common between labels and predictions")
    pairs = [(str(expected[i]).strip().lower(), str(predicted[i]).strip().lower()) for i in ids]
    n = len(pairs)
    observed = sum(e == p for e, p in pairs) / n
    exp_counts = Counter(e for e, _ in pairs)
    pred_counts = Counter(p for _, p in pairs)
    labels = sorted(set(exp_counts) | set(pred_counts))
    chance = sum(exp_counts[label] * pred_counts[label] for label in labels) / (n * n)
    kappa = 1.0 if chance == 1 else (observed - chance) / (1 - chance)
    per_label = {}
    for label in labels:
        tp = sum(e == label and p == label for e, p in pairs)
        per_label[label] = {
            "precision": tp / pred_counts[label] if pred_counts[label] else None,
            "recall": tp / exp_counts[label] if exp_counts[label] else None,
            "support": exp_counts[label],
        }
    confusion = Counter(f"{e} -> {p}" for e, p in pairs if e != p)
    return {"n": n, "accuracy": observed, "kappa": kappa, "per_label": per_label,
            "confusions": dict(confusion.most_common()),
            "unpredicted": [i for i in expected if i not in predicted]}
