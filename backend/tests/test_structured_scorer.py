from app.evals.context import build_eval_user_message, extract_prompt_facts
from app.evals.structured_scorer import score_structured_json


def test_extract_prompt_facts():
    prompt = (
        "Qualys Scan Alert on Asset 10.1.2.3 (Linux Server, Env: Production). "
        "Detected CVE-2024-3094 (XZ Utils Backdoor) with CVSS 10.0."
    )
    facts = extract_prompt_facts(prompt)
    assert facts["cve_id"] == "CVE-2024-3094"
    assert facts["asset_ip"] == "10.1.2.3"
    assert facts["environment"] == "Production"
    assert facts["cvss"] == 10.0


def test_build_eval_user_message_includes_schema():
    case = {
        "input_prompt": "Asset Record: IP 192.168.1.10, Tag: Confidential-DB, Environment: Production.",
        "expected_output": {
            "asset_ip": "192.168.1.10",
            "cve_id": "CVE-2024-3094",
            "internet_facing": False,
            "compliance_impact": "PCI",
            "groundedness_checkpoint": "tag",
        },
    }
    message = build_eval_user_message(case)
    assert "asset_ip" in message
    assert "internet_facing: false" in message
    assert "asset_ip, cve_id, internet_facing" in message


def test_score_structured_json_perfect_match():
    expected = {
        "cve_id": "CVE-2024-3094",
        "severity": "CRITICAL",
        "asset_ip": "10.1.2.3",
        "environment": "Production",
        "recommended_action": "Apply security update for CVE-2024-3094.",
        "requires_hitl": True,
        "tru_risk_score": 100,
    }
    score, detail = score_structured_json(expected, expected)
    assert score == 1.0
    assert detail == "all fields matched"


def test_groundedness_checkpoint_requires_quoted_entities_only():
    expected = {
        "groundedness_checkpoint": (
            "Must explicitly reference tag 'Confidential-DB' and IP '192.168.1.10' "
            "without inventing unlisted open ports."
        )
    }
    actual = {
        "groundedness_checkpoint": (
            "Confidential-DB asset with IP 192.168.1.10 requires verification."
        )
    }
    score, detail = score_structured_json(expected, actual)
    assert score == 1.0
    assert detail == "all fields matched"


def test_score_structured_json_missing_field():
    expected = {"cve_id": "CVE-2024-3094", "asset_ip": "10.1.2.3"}
    actual = {"cve_id": "CVE-2024-3094"}
    score, detail = score_structured_json(expected, actual)
    assert score == 0.5
    assert "missing:asset_ip" in detail
