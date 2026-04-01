from schemas import AnalyticRecommendation, RecommendationValidationResult, TriageResult
from llm_client import call_structured

SYSTEM = """You are a quality gatekeeper for complaint resolution pipelines.
Validate the analytic recommendation against the complaint and triage.
RULES:
1. Reject ANY action contradicting facts in the complaint.
2. Reject ANY action requiring information not present in the complaint.
3. If confidence >= 0.85 AND no conflicts, you MAY override complexity to simple.
4. Legal caution overrides everything.
5. Be conservative: when in doubt, reject."""

def run_recommendation_validation(
    complaint: str,
    triage: TriageResult,
    recommendation: AnalyticRecommendation
) -> RecommendationValidationResult:
    actions_text = "\n".join([
        f"  - {a.action_type}" + (f" (value: {a.value})" if a.value else "") + (f" [condition: {a.condition}]" if a.condition else "")
        for a in recommendation.recommended_actions
    ])

    user = f"""Validate the analytic recommendation against this complaint and triage.

<complaint>
{complaint}
</complaint>

<triage>
Complexity: {triage.complexity}
Risk level: {triage.risk_level}
Domain: {triage.domain}
Key claims: {triage.key_claims}
Legal caution: {triage.requires_legal_caution}
</triage>

<analytic_recommendation>
Confidence: {recommendation.confidence_score}
Priority: {recommendation.priority_level}
Customer segment: {recommendation.customer_segment}
Suggested tone: {recommendation.suggested_tone}
Recommended actions:
{actions_text}
Policy references: {recommendation.policy_references}
Analyst notes: {recommendation.analyst_notes or 'None'}
</analytic_recommendation>

Validate each action. Approve only what is safe and applicable."""

    result = call_structured(SYSTEM, user, RecommendationValidationResult, temperature=0.0)
    return RecommendationValidationResult.model_validate(result)
