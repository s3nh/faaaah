from schemas import ComplexityLevel, AnalyticRecommendation
from stage1_triage import run_triage
from stage1_5_rec_validation import run_recommendation_validation
from stage2_clarification import run_clarification
from stage3a_deep_similarity import run_deep_similarity
from stage3b_fast_similarity import run_fast_similarity
from stage4_draft import run_draft
from stage5_audit import run_audit
from stage6_rewrite import run_rewrite

MAX_AUDIT_LOOPS = 2

def run_complaint_pipeline(
    complaint: str,
    historical_pairs: list[dict],
    recommendation: AnalyticRecommendation
) -> dict:
    print("Stage 1: Triage...")
    triage = run_triage(complaint)
    print(f"  Complexity: {triage.complexity} | Risk: {triage.risk_level} | Domain: {triage.domain}")

    print("Stage 1.5: Analytic recommendation validation...")
    rec_validation = run_recommendation_validation(complaint, triage, recommendation)
    print(f"  Approved: {[a.action_type for a in rec_validation.approved_actions]}")
    print(f"  Rejected: {rec_validation.rejected_actions}")

    effective_complexity = (
        ComplexityLevel.simple
        if rec_validation.override_triage_complexity == "simple"
        else triage.complexity
    )
    if effective_complexity != triage.complexity:
        print(f"  Analytics override: complexity -> {effective_complexity}")

    clarification = None
    if effective_complexity in (ComplexityLevel.complex, ComplexityLevel.ambiguous):
        print("Stage 2: Clarification extraction...")
        clarification = run_clarification(complaint, triage)
        blocking = [m for m in clarification.missing_information if m.criticality == "blocking"]
        print(f"  {len(clarification.missing_information)} gaps, {len(blocking)} blocking")

        print("Stage 3A: Deep similarity scoring...")
        similarity = run_deep_similarity(complaint, triage, clarification, historical_pairs)
    else:
        print("Stage 3B: Fast similarity scoring...")
        similarity = run_fast_similarity(complaint, historical_pairs)

    usable = [p for p in similarity.scored_pairs if p.relevance_score >= similarity.recommended_threshold]
    print(f"  {len(usable)}/{len(historical_pairs)} pairs above threshold ({similarity.recommended_threshold})")

    print("Stage 4: Draft generation...")
    draft_result = run_draft(complaint, triage, similarity, rec_validation, recommendation, clarification)
    print(f"  Placeholders: {draft_result.placeholders}")

    historical_context_used = "\n\n".join([p.usable_excerpt for p in usable])
    audit = None
    for loop in range(MAX_AUDIT_LOOPS):
        print(f"Stage 5: Audit (loop {loop + 1})...")
        audit = run_audit(complaint, draft_result.draft, historical_context_used, triage, rec_validation)
        print(f"  Passed: {audit.passed} | Confidence: {audit.overall_confidence:.2f}")
        if audit.passed:
            break
        critical = [f for f in audit.findings if f.severity == "critical"]
        print(f"  {len(critical)} critical findings. Rewriting...")
        draft_result = run_rewrite(draft_result.draft, audit, complaint)

    return {
        "final_response": draft_result.draft,
        "placeholders": draft_result.placeholders,
        "assumptions": draft_result.assumptions_made,
        "confidence": audit.overall_confidence if audit else 0.0,
        "audit_passed": audit.passed if audit else False,
        "risk_level": triage.risk_level,
        "requires_legal_review": triage.requires_legal_caution,
        "approved_actions": [a.action_type for a in rec_validation.approved_actions],
        "rejected_actions": rec_validation.rejected_actions,
        "analytics_applicable": rec_validation.is_applicable,
        "analytics_confidence": recommendation.confidence_score,
        "pipeline_path": effective_complexity,
    }
