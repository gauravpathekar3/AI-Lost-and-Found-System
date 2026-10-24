"""Evaluate ranking on fictional demonstration pairs."""

from __future__ import annotations

import json
from pathlib import Path

from matcher import find_matches

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "items.json"
OUTPUT_PATH = ROOT / "artifacts" / "matching_evaluation.json"
PAIRS = {
    "demo-lost-blue-bottle": "demo-found-blue-bottle",
    "demo-lost-red-umbrella": "demo-found-red-umbrella",
    "demo-lost-wallet": "demo-found-wallet",
    "demo-lost-usb": "demo-found-usb",
}


def main() -> None:
    reports = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    cases = []
    for query_id, expected_id in PAIRS.items():
        query = next(item for item in reports if item["id"] == query_id)
        matches = find_matches(query, reports, limit=5)
        top = matches[0] if matches else None
        cases.append({
            "query_id": query_id,
            "expected_match_id": expected_id,
            "top_match_id": top["id"] if top else None,
            "correct_at_1": bool(top and top["id"] == expected_id),
            "top_score": round(top["match_score"], 4) if top else None,
            "image_signal_used": bool(top and top.get("visual_similarity") is not None),
        })
    correct = sum(case["correct_at_1"] for case in cases)
    result = {
        "note": "Small fictional demonstration set; not a real-world accuracy estimate.",
        "queries": len(cases),
        "correct_at_1": correct,
        "top_1_match_rate": correct / len(cases) if cases else 0.0,
        "cases": cases,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
