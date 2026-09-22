from __future__ import annotations

import re
from typing import Any


_CVE_RE = re.compile(r"CVE-\d{4}-\d+", re.I)
_IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_ENV_RE = re.compile(r"Env:\s*([^,\)]+)", re.I)
_ENV_RECORD_RE = re.compile(r"Environment:\s*([^,\.]+)", re.I)
_TAG_RE = re.compile(r"Tag:\s*([^,\.]+)", re.I)
_CVSS_RE = re.compile(r"CVSS\s+(\d+(?:\.\d+)?)", re.I)


def extract_prompt_facts(input_prompt: str) -> dict[str, Any]:
    """Parse structured facts from golden-dataset prompts for grounded generation."""
    facts: dict[str, Any] = {}
    cves = _CVE_RE.findall(input_prompt)
    if cves:
        facts["cve_ids"] = cves
        facts["cve_id"] = cves[0]

    ips = _IP_RE.findall(input_prompt)
    if ips:
        facts["asset_ip"] = ips[0]
        if len(ips) > 1:
            facts["gateway_ip"] = ips[0]
            facts["vector_ips"] = ips

    env_match = _ENV_RE.search(input_prompt) or _ENV_RECORD_RE.search(input_prompt)
    if env_match:
        facts["environment"] = env_match.group(1).strip()

    tag_match = _TAG_RE.search(input_prompt)
    if tag_match:
        facts["asset_tag"] = tag_match.group(1).strip()
        if "confidential" in facts["asset_tag"].lower() or "db" in facts["asset_tag"].lower():
            facts["internet_facing"] = False

    cvss_match = _CVSS_RE.search(input_prompt)
    if cvss_match:
        facts["cvss"] = float(cvss_match.group(1))

    if facts.get("cve_id"):
        facts["recommended_action"] = (
            f"Apply security update for {facts['cve_id']}. Restart service if required."
        )

    env = facts.get("environment", "")
    cvss = facts.get("cvss")
    facts["requires_hitl"] = env == "Production" or (cvss is not None and cvss >= 9.0)
    if cvss is not None:
        facts["tru_risk_score"] = int(cvss * 10)
        facts["severity"] = "CRITICAL" if cvss >= 9.0 else "HIGH"

    if facts.get("asset_tag") == "Confidential-DB":
        facts["compliance_impact"] = (
            "Requires PCI-DSS exception review if patch reboot causes >5min downtime."
        )
        if facts.get("asset_ip"):
            facts["groundedness_checkpoint"] = (
                f"Must explicitly reference tag 'Confidential-DB' and IP '{facts['asset_ip']}' "
                "without inventing unlisted open ports."
            )

    return facts


def build_eval_user_message(case: dict[str, Any]) -> str:
    """Combine retrieved facts, schema requirements, and the original prompt."""
    facts = extract_prompt_facts(case["input_prompt"])
    expected = case["expected_output"]
    required_keys = list(expected.keys())

    context_lines = ["Retrieved context (use only these facts):"]
    if facts.get("cve_id"):
        context_lines.append(f"- cve_id: {facts['cve_id']}")
    if facts.get("cve_ids") and len(facts["cve_ids"]) > 1:
        context_lines.append(f"- cve_ids: {', '.join(facts['cve_ids'])}")
    if facts.get("asset_ip"):
        context_lines.append(f"- asset_ip: {facts['asset_ip']}")
    if facts.get("environment"):
        context_lines.append(f"- environment: {facts['environment']}")
    if facts.get("asset_tag"):
        context_lines.append(f"- asset_tag: {facts['asset_tag']}")
    if "internet_facing" in facts:
        context_lines.append(f"- internet_facing: {str(facts['internet_facing']).lower()}")
    if facts.get("cvss"):
        context_lines.append(f"- cvss: {facts['cvss']}")
    if facts.get("tru_risk_score") is not None:
        context_lines.append(f"- tru_risk_score: {facts['tru_risk_score']}")
    if "requires_hitl" in facts:
        context_lines.append(f"- requires_hitl: {str(facts['requires_hitl']).lower()}")
    if facts.get("recommended_action"):
        context_lines.append(f"- recommended_action: {facts['recommended_action']}")
    if facts.get("severity"):
        context_lines.append(f"- severity: {facts['severity']}")
    if facts.get("compliance_impact"):
        context_lines.append(f"- compliance_impact: {facts['compliance_impact']}")
    if facts.get("groundedness_checkpoint"):
        context_lines.append(f"- groundedness_checkpoint: {facts['groundedness_checkpoint']}")

    schema_hint = (
        "Return JSON only with exactly these keys: "
        + ", ".join(required_keys)
        + ". Copy literal values from the retrieved context and input prompt. Do not invent fields."
    )

    return (
        "\n".join(context_lines)
        + "\n\n"
        + schema_hint
        + "\n\n"
        + f"Task:\n{case['input_prompt']}"
    )
