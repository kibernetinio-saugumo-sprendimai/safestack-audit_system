#!/usr/bin/env python3
from typing import Any

BLOCKING_SEVERITIES = {"critical", "high"}

def has_blocking_findings(agent_results: list[dict[str, Any]]) -> bool:
    for result in agent_results:
        for finding in result.get("findings", []):
            if finding.get("severity") in BLOCKING_SEVERITIES:
                return True
    return False

def build_supervisor_result(
    agent_results: list[dict[str, Any]],
    invalid_outputs: list[dict[str, str]],
) -> dict[str, Any]:
    approved_findings = []
    rejected_findings = []

    for result in agent_results:
        approved_findings.extend(result.get("findings", []))

    if invalid_outputs:
        return {
            "supervisor": "CHIEF_SUPERVISOR",
            "status": "blocked",
            "reason": "One or more agent outputs failed validation.",
            "invalid_agents": invalid_outputs,
            "approved_findings": approved_findings,
            "rejected_findings": rejected_findings,
        }

    if has_blocking_findings(agent_results):
        return {
            "supervisor": "CHIEF_SUPERVISOR",
            "status": "fail",
            "reason": "Blocking critical/high findings exist.",
            "invalid_agents": [],
            "approved_findings": approved_findings,
            "rejected_findings": rejected_findings,
        }

    return {
        "supervisor": "CHIEF_SUPERVISOR",
        "status": "pass",
        "reason": "No invalid outputs and no blocking findings.",
        "invalid_agents": [],
        "approved_findings": approved_findings,
        "rejected_findings": rejected_findings,
    }
