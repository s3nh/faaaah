from schemas import DraftResult, AuditResult
from llm_client import call_structured

SYSTEM = """You are a complaint response editor.
Fix ONLY the flagged issues. Do not change anything that passed the audit.
Replace unsupported claims with [NEEDS: X] placeholders."""

def run_rewrite(draft: str, audit: AuditResult, complaint: str) -> DraftResult:
    findings_text = "\n".join(
        [f"[CRITICAL] Claim: '{f.claim}' => {f.fix_instruction}" for f in audit.findings if f.severity == "critical"] +
        [f"[WARNING] Claim: '{f.claim}' => {f.fix_instruction}" for f in audit.findings if f.severity == "warning"]
    )

    user = f"""Rewrite the draft fixing ONLY the flagged issues.

<original_complaint>
{complaint}
</original_complaint>

<current_draft>
{draft}
</current_draft>

<required_fixes>
{findings_text}
</required_fixes>

Instructions: {audit.rewrite_instructions or 'Fix flagged items only.'}"""

    result = call_structured(SYSTEM, user, DraftResult, temperature=0.1)
    return DraftResult(**result)
