from schemas import DraftResult, TriageResult, SimilarityResult, ClarificationResult, AnalyticRecommendation, RecommendationValidationResult
from llm_client import call_structured

SYSTEM = """You are an expert complaint response writer.
RULES:
1. Only use facts present in the complaint or historical excerpts.
2. For missing information, insert [NEEDS: <description>] — never fabricate.
3. If legal caution flagged, avoid admission of liability or promises.
4. Tone: use analytic recommendation tone if approved, else match customer emotional state.
5. Approved analytic actions are AUTHORITATIVE — include them, do NOT add unapproved actions.
6. Structure: Acknowledgment > Explanation > Resolution/Next Steps > Closing."""

def run_draft(
    complaint: str,
    triage: TriageResult,
    similarity: SimilarityResult,
    rec_validation: RecommendationValidationResult,
    recommendation: AnalyticRecommendation,
    clarification: ClarificationResult | None = None
) -> DraftResult:
    threshold = similarity.recommended_threshold
    usable = [p for p in similarity.scored_pairs if p.relevance_score >= threshold and p.usable_excerpt.strip()]

    context_block = "\n\n".join([f"[Historical — relevance {p.relevance_score}/10]\n{p.usable_excerpt}" for p in usable]) or "No sufficiently relevant historical context found."
    approved_actions_text = "\n".join([f"  - {a.action_type}" + (f": {a.value}" if a.value else "") + (f" ({a.condition})" if a.condition else "") for a in rec_validation.approved_actions]) or "  None approved."
    rejected_text = "\n".join([f"  - {r}" for r in rec_validation.rejected_actions]) or "  None."
    tone = recommendation.suggested_tone if rec_validation.is_applicable and recommendation.suggested_tone else triage.emotional_tone
    missing_block = ""
    if clarification:
        blocking = [m for m in clarification.missing_information if m.criticality == "blocking"]
        if blocking:
            missing_block = "\nCRITICAL MISSING INFO (use placeholders):\n" + "\n".join([f"- {m.field}: {m.reason}" for m in blocking])
    legal_instruction = "\nLEGAL CAUTION: Do NOT admit fault, make promises, or state specific compensation amounts." if triage.requires_legal_caution else ""
    policy_refs = f"\nApplicable policies: {', '.join(recommendation.policy_references)}" if recommendation.policy_references else ""

    user = f"""Write a complaint response proposal.

<complaint>
{complaint}
</complaint>

<tone>{tone}</tone>
<domain>{triage.domain}</domain>
<customer_segment>{recommendation.customer_segment or 'unknown'}</customer_segment>
{legal_instruction}
{policy_refs}
{missing_block}

<approved_resolution_actions>
{approved_actions_text}
</approved_resolution_actions>

<rejected_actions_do_not_include>
{rejected_text}
</rejected_actions_do_not_include>

<applicable_historical_context>
{context_block}
</applicable_historical_context>

Write a complete professional response. Include all approved actions. Use [NEEDS: X] for unknowns."""

    result = call_structured(SYSTEM, user, DraftResult, temperature=0.15)
    return DraftResult.model_validate(result)
