from __future__ import annotations

import re
from typing import Any


def _normalize_string(value: Any) -> str:
    return str(value).strip().lower()


def _values_match(key: str, expected: Any, actual: Any) -> bool:
    if actual is None:
        return False

    if isinstance(expected, bool):
        if isinstance(actual, bool):
            return expected is actual
        return _normalize_string(actual) in {"true", "false"} and (
            (_normalize_string(actual) == "true") is expected
        )

    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return float(expected) == float(actual)

    if key == "recommended_action":
        actual_text = _normalize_string(actual)
        expected_text = _normalize_string(expected)
        if expected_text in actual_text or actual_text in expected_text:
            return True
        for token in ("cve-", "patch", "update", "remediat", "restart"):
            if token in actual_text:
                return True
        return False

    if key == "groundedness_checkpoint":
        actual_text = _normalize_string(actual)
        quoted = re.findall(r"'([^']+)'", str(expected))
        if not quoted:
            return _normalize_string(expected) in actual_text or actual_text in _normalize_string(expected)
        return all(_normalize_string(part) in actual_text for part in quoted)

    if key in {"attack_path_summary", "primary_mitigation", "compliance_impact"}:
        actual_text = _normalize_string(actual)
        expected_text = _normalize_string(expected)
        # Require key entities from expected text to appear in actual output.
        tokens = [token for token in expected_text.replace(",", " ").split() if len(token) > 3]
        if not tokens:
            return actual_text == expected_text
        hits = sum(1 for token in tokens if token in actual_text)
        return hits / len(tokens) >= 0.6

    return _normalize_string(expected) == _normalize_string(actual)


def score_structured_json(expected: dict[str, Any], actual: dict[str, Any]) -> tuple[float, str]:
    if not expected:
        return 0.0, "empty expected output"

    per_field: list[float] = []
    misses: list[str] = []

    for key, expected_val in expected.items():
        if key not in actual:
            per_field.append(0.0)
            misses.append(f"missing:{key}")
            continue
        if _values_match(key, expected_val, actual[key]):
            per_field.append(1.0)
        else:
            per_field.append(0.0)
            misses.append(f"mismatch:{key}")

    score = sum(per_field) / len(per_field)
    detail = "all fields matched" if not misses else ", ".join(misses)
    return score, detail
