"""Small TF-IDF vector-space matcher using only the Python standard library."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from image_utils import image_similarity

STOP_WORDS = {
    "a", "an", "and", "are", "at", "be", "by", "for", "from", "in", "is",
    "it", "of", "on", "or", "the", "to", "was", "with", "near", "left",
    "found", "lost", "item",
}


def _text(record: dict[str, Any]) -> str:
    return " ".join(str(record.get(key, "") or "") for key in ("item_name", "description")).strip()


def _terms(text: str) -> list[str]:
    words = [word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOP_WORDS]
    bigrams = [f"{first}_{second}" for first, second in zip(words, words[1:])]
    return words + bigrams


def _tfidf_vectors(documents: list[str]) -> list[dict[str, float]]:
    term_counts = [Counter(_terms(document)) for document in documents]
    document_frequency = Counter()
    for counts in term_counts:
        document_frequency.update(counts.keys())
    total_documents = max(1, len(documents))
    inverse_document_frequency = {
        term: math.log((1 + total_documents) / (1 + frequency)) + 1
        for term, frequency in document_frequency.items()
    }

    vectors: list[dict[str, float]] = []
    for counts in term_counts:
        weights = {
            term: (1 + math.log(count)) * inverse_document_frequency[term]
            for term, count in counts.items()
        }
        length = math.sqrt(sum(value * value for value in weights.values())) or 1.0
        vectors.append({term: value / length for term, value in weights.items()})
    return vectors


def _cosine(first: dict[str, float], second: dict[str, float]) -> float:
    if len(first) > len(second):
        first, second = second, first
    return sum(value * second.get(term, 0.0) for term, value in first.items())


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def _location_similarity(first: str, second: str) -> float:
    a, b = _tokens(first), _tokens(second)
    return len(a & b) / len(a | b) if a and b else 0.0


def find_matches(query: dict[str, Any], reports: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    """Rank open reports of the opposite type. Scores are not probabilities."""
    if query.get("status") not in {"lost", "found"}:
        return []
    opposite = "found" if query["status"] == "lost" else "lost"
    candidates = [
        item for item in reports
        if item.get("status") == opposite
        and not item.get("resolved", False)
        and item.get("id") != query.get("id")
    ]
    if not candidates:
        return []

    vectors = _tfidf_vectors([_text(query)] + [_text(item) for item in candidates])
    category = str(query.get("category", "")).strip().casefold()
    color = str(query.get("color", "")).strip().casefold()
    ranked = []
    for index, candidate in enumerate(candidates, start=1):
        text_score = _cosine(vectors[0], vectors[index])
        same_category = bool(category and category == str(candidate.get("category", "")).strip().casefold())
        same_color = bool(color and color not in {"not specified", "unknown"}
                          and color == str(candidate.get("color", "")).strip().casefold())
        location_score = _location_similarity(
            str(query.get("location", "")), str(candidate.get("location", ""))
        )
        visual_score = image_similarity(query, candidate)

        components = [(0.50, text_score)]
        if category:
            components.append((0.18, float(same_category)))
        if query.get("location"):
            components.append((0.08, location_score))
        if color and color not in {"not specified", "unknown"}:
            components.append((0.04, float(same_color)))
        if visual_score is not None:
            components.append((0.20, visual_score))
        score = sum(weight * value for weight, value in components) / sum(
            weight for weight, _ in components
        )

        reasons = []
        if same_category:
            reasons.append("Same item category")
        if same_color:
            reasons.append("Same color")
        if location_score >= 0.25:
            reasons.append("Location names overlap")
        if text_score >= 0.12:
            reasons.append("Description uses similar words")
        if visual_score is not None:
            reasons.append(f"Image similarity signal {visual_score:.0%}")
        if not reasons:
            reasons.append("Highest available similarity")
        ranked.append({
            **candidate,
            "match_score": float(score),
            "text_similarity": float(text_score),
            "visual_similarity": visual_score,
            "reasons": reasons,
        })
    return sorted(ranked, key=lambda item: item["match_score"], reverse=True)[:limit]
