from fastapi import APIRouter, HTTPException

from app.db import fetch_all, fetch_one
from app.schemas import ErrorResponse, TriageKpi, TriageResponse, TriageSummary, VulnerabilityItem

router = APIRouter(prefix="/triage", tags=["triage"])


@router.get("", response_model=TriageResponse, responses={503: {"model": ErrorResponse}})
async def get_triage() -> TriageResponse:
    summary_row = await fetch_one(
        """
        SELECT scan_id, scope, scanner, policies, last_delta_sec, tru_risk_score, tru_risk_delta,
               asset_count, internet_facing_count, critical_findings, groundedness_pct, latency_p95_ms, model_cost_per_1k
        FROM scan_context
        ORDER BY updated_at DESC
        LIMIT 1
        """
    )
    if not summary_row:
        raise HTTPException(status_code=503, detail={"status": "error", "code": "DB_NOT_SEEDED", "message": "Scan context unavailable"})

    vuln_rows = await fetch_all(
        """
        SELECT v.cve_id, v.product, v.cvss, v.severity, v.threat_state,
               COUNT(av.asset_id)::int AS asset_count
        FROM vulnerabilities v
        LEFT JOIN asset_vulnerabilities av ON av.vulnerability_id = v.id
        GROUP BY v.id
        ORDER BY v.cvss DESC
        LIMIT 10
        """
    )

    summary = TriageSummary(
        scan_id=summary_row["scan_id"],
        tru_risk_score=summary_row["tru_risk_score"],
        tru_risk_delta=summary_row["tru_risk_delta"],
        asset_count=summary_row["asset_count"],
        internet_facing_count=summary_row["internet_facing_count"],
        critical_findings=summary_row["critical_findings"],
        scope=summary_row["scope"],
        scanner=summary_row["scanner"],
        policies=summary_row["policies"],
        last_delta_sec=summary_row["last_delta_sec"],
        kpis=TriageKpi(
            groundedness_pct=float(summary_row["groundedness_pct"]),
            latency_p95_ms=summary_row["latency_p95_ms"],
            model_cost_per_1k=float(summary_row["model_cost_per_1k"]),
        ),
    )

    vulnerabilities = [
        VulnerabilityItem(
            cve=row["cve_id"],
            product=row["product"],
            assets=row["asset_count"],
            cvss=f"{float(row['cvss']):.1f}",
            state=row["threat_state"],
            severity=row["severity"],
        )
        for row in vuln_rows[:3]
    ]

    return TriageResponse(summary=summary, vulnerabilities=vulnerabilities)
