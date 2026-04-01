from schemas import ClarificationResult, TriageResult
from llm_client import call_structured

SYSTEM = """You are a complaint resolution specialist.
Identify EXACTLY what information is missing, ambiguous, or needs assumption.
Be conservative. Never fill in details not provided."""

def run_clarification(complaint: str, triage: TriageResult) -> ClarificationResult:
    user = f"""Identify all information gaps in this complaint.

<complaint>
{complaint}
</complaint>

<triage_summary>
Complexity: {triage.complexity}
Domain: {triage.domain}
Key claims: {triage.key_claims}
Risk level: {triage.risk_level}
</triage_summary>

List every missing or ambiguous piece of information. Document assumptions explicitly."""

    result = call_structured(SYSTEM, user, ClarificationResult, temperature=0.0)
    return ClarificationResult.model_validate(result)
