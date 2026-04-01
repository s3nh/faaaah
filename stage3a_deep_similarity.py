from schemas import SimilarityResult, TriageResult, ClarificationResult
from llm_client import call_structured

SYSTEM = """You are a semantic relevance auditor.
Evaluate each historical complaint-answer pair against the new complaint.
Be STRICT: score 8-10 only if the historical answer DIRECTLY and FULLY applies.
Extract ONLY the verbatim excerpt that applies."""

def run_deep_similarity(
    complaint: str,
    triage: TriageResult,
    clarification: ClarificationResult,
    historical_pairs: list[dict]
) -> SimilarityResult:
    pairs_text = "\n\n".join([
        f"[{i}]\nCOMPLAINT: {p['complaint']}\nANSWER: {p['answer']}"
        for i, p in enumerate(historical_pairs)
    ])

    user = f"""New complaint:
<complaint>{complaint}</complaint>

<context>
Domain: {triage.domain}
Key claims: {triage.key_claims}
Missing info: {[m.field for m in clarification.missing_information]}
Legal caution: {triage.requires_legal_caution}
</context>

<historical_pairs>
{pairs_text}
</historical_pairs>

Score each pair. Extract only the applicable excerpt. List conflicts and coverage gaps."""

    result = call_structured(SYSTEM, user, SimilarityResult, temperature=0.0)
    return SimilarityResult.model_validate(result)
