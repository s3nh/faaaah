from schemas import AuditResult, TriageResult, RecommendationValidationResult
from llm_client import call_structured

SYSTEM = """You are a strict quality auditor for complaint responses.
Verify EVERY factual claim against source material.
Verify ALL approved actions are present and NONE of the rejected actions appear.
Mark as CRITICAL if: claim is unsupported, rejected action included, approved action missing, legal caution violated."""

def run_audit(
    complaint: str,
    draft: str,
    historical_context: str,
    triage: TriageResult,
    rec_validation: RecommendationValidationResult
) -> AuditResult:
    approved = "\n".join([f"- {a.action_type}" + (f": {a.value}" if a.value else "") for a in rec_validation.approved_actions]) or "None"
    rejected = "\n".join([f"- {r}" for r in rec_validation.rejected_actions]) or "None"
    legal_check = "CRITICAL: flag ANY admission of fault, liability, or specific promises." if triage.requires_legal_caution else ""

    user = f"""Audit this draft for hallucinations, policy violations, and analytics compliance.

<original_complaint>
{complaint}
</original_complaint>

<historical_context_used>
{historical_context}
</historical_context_used>

<approved_actions_must_be_present>
{approved}
</approved_actions_must_be_present>

<rejected_actions_must_not_appear>
{rejected}
</rejected_actions_must_not_appear>

<draft_response>
{draft}
</draft_response>

{legal_check}

Set passed=true ONLY if zero critical findings."""

    result = call_structured(SYSTEM, user, AuditResult, temperature=0.0)
    return AuditResult(**result)
