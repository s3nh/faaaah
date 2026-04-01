from schemas import TriageResult
from llm_client import call_structured

SYSTEM = """You are a senior complaint analyst.
Perform initial triage. Be precise. Do NOT infer facts not stated.
If the complaint contains legal, financial, health, or safety implications,
set requires_legal_caution to true WITHOUT exception."""

def run_triage(complaint: str) -> TriageResult:
    user = f"""Analyze the following customer complaint carefully.

<complaint>
{complaint}
</complaint>

Return a structured triage assessment."""

    result = call_structured(SYSTEM, user, TriageResult, temperature=0.0)
    return TriageResult.model_validate(result)
