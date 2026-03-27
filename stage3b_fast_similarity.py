from schemas import SimilarityResult
from llm_client import call_structured

SYSTEM = """You are a relevance matcher.
Quickly score each historical answer's relevance to the complaint.
Extract only what directly applies."""

def run_fast_similarity(complaint: str, historical_pairs: list[dict]) -> SimilarityResult:
    pairs_text = "\n\n".join([
        f"[{i}]\nCOMPLAINT: {p['complaint']}\nANSWER: {p['answer']}"
        for i, p in enumerate(historical_pairs)
    ])

    user = f"""Complaint: {complaint}

Historical pairs:
{pairs_text}

Score relevance (0-10) for each and extract the applicable excerpt."""

    result = call_structured(SYSTEM, user, SimilarityResult, temperature=0.1)
    return SimilarityResult(**result)
