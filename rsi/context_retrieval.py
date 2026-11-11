"""Bounded RSI context retrieval. Embeddings are optional, never a COMSOL gate.

This module never retrieves held-out records: search results are advisory and
must not leak the evaluation split into policy improvement.
"""
from __future__ import annotations

import math
import re
from typing import Any, Iterable

_TOKENS = re.compile(r"[^\W_]+", re.UNICODE)


def _words(text: str) -> set[str]:
    return {t.casefold() for t in _TOKENS.findall(text)}


def _lexical_score(query: str, candidate: str) -> float:
    a, b = _words(query), _words(candidate)
    if not a or not b:
        return 0.0
    return len(a & b) / math.sqrt(len(a) * len(b))


def _cosine(a: Iterable[float], b: Iterable[float]) -> float:
    a, b = list(a), list(b)
    if len(a) != len(b) or not a:
        raise ValueError("Embedding dimensions must match and be nonempty")
    if not all(math.isfinite(float(v)) for v in a + b):
        raise ValueError("Embeddings must contain only finite numbers")
    dot = sum(float(x) * float(y) for x, y in zip(a, b))
    norm = math.sqrt(sum(float(x) ** 2 for x in a) * sum(float(y) ** 2 for y in b))
    return dot / norm if norm else 0.0


def _text(record: dict[str, Any]) -> str:
    parts = [
        str(record.get("task_family") or ""),
        str(record.get("context") or ""),
        str(record.get("failure_type") or ""),
        str(record.get("diagnosis") or ""),
        str(record.get("repair") or ""),
        str(record.get("repair_result") or ""),
        str(record.get("lesson_learned") or ""),
    ]
    return " | ".join(p for p in parts if p and p != "None")


def retrieve_context(
    records: Iterable[dict[str, Any]],
    query: str,
    *,
    embedder: Any = None,
    task_family: str | None = None,
    max_records: int = 4,
    max_chars: int = 2400,
    min_similarity: float = 0.0,
) -> dict[str, Any]:
    """Return source-linked snippets subject to a hard character budget.

    embedder is an optional injected object exposing encode(list[str]).
    Without it, use deterministic lexical matching; no model downloads,
    HTTP requests, or inference are triggered implicitly.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be nonempty")
    if max_records < 1 or max_chars < 1:
        raise ValueError("max_records and max_chars must be positive")
    if not -1 <= min_similarity <= 1:
        raise ValueError("min_similarity must be between -1 and 1")

    candidates: list[tuple[dict[str, Any], str]] = []
    seen: set[str] = set()
    for record in records:
        if record.get("dataset_split") == "held_out":
            continue
        if task_family is not None and record.get("task_family") != task_family:
            continue
        content = _text(record)
        # Duplicate content consumes context without contributing new evidence.
        key = content.casefold().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        candidates.append((record, content))

    if not candidates:
        return {"method": "embedding" if embedder is not None else "lexical",
                "items": [], "chars_used": 0, "held_out_excluded": True}

    if embedder is None:
        scores = [_lexical_score(query, content) for _, content in candidates]
    else:
        vectors = embedder.encode([query] + [c for _, c in candidates])
        if len(vectors) != len(candidates) + 1:
            raise ValueError("Embedding provider returned the wrong number of vectors")
        scores = [_cosine(vectors[0], v) for v in vectors[1:]]

    ranked = sorted(zip(candidates, scores), key=lambda item: -item[1])
    items: list[dict[str, Any]] = []
    used = 0
    for (record, content), score in ranked:
        if score <= 0 or score < min_similarity or len(items) >= max_records:
            continue
        available = max_chars - used
        if available <= 0:
            break
        snippet = content[:available]
        items.append({
            "experience_id": record.get("experience_id"),
            "task_id": record.get("task_id"),
            "task_family": record.get("task_family"),
            "source_split": record.get("dataset_split"),
            "scientific_validation": record.get("scientific_validation"),
            "similarity": round(float(score), 6),
            "snippet": snippet,
            "truncated": len(snippet) < len(content),
            "role": "untrusted_historical_context",
        })
        used += len(snippet)
    return {
        "method": "embedding" if embedder is not None else "lexical",
        "items": items,
        "chars_used": used,
        "held_out_excluded": True,
    }
