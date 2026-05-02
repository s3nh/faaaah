from __future__ import annotations

import asyncio
from typing import AsyncGenerator

from google.adk.agents import LlmAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from schemas import (
    AnalyticRecommendation,
    AuditResult,
    DraftResult,
    SimilarityResult,
    TriageResult,
    ValidatedActions,
)

MODEL = LiteLlm(
    model="openai/Qwen2.5-72B-Instruct",
    api_base="http://localhost:8000/v1",
    api_key="EMPTY",
)

MAX_AUDIT_LOOPS = 2


class ComplaintPipeline(BaseAgent):
    """
    Sequential complaint pipeline.  All inter-stage data lives in
    ctx.session.state — no argument threading between stages.
    """

    model_config = {"arbitrary_types_allowed": True}

    recommendation: AnalyticRecommendation
    historical_pairs: list[dict]

    # ------------------------------------------------------------------ #
    #  helpers                                                             #
    # ------------------------------------------------------------------ #

    def _agent(self, name: str, instruction: str, schema: type, key: str) -> LlmAgent:
        return LlmAgent(
            name=name,
            model=MODEL,
            instruction=instruction,
            output_schema=schema,
            output_key=key,
        )

    # ------------------------------------------------------------------ #
    #  pipeline                                                            #
    # ------------------------------------------------------------------ #

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        state = ctx.session.state
        complaint: str = state["complaint"]
        rec = self.recommendation

        # ── 1. Triage ─────────────────────────────────────────────────── #
        async for e in self._agent(
            name="triage",
            instruction=(
                f"Analyze this customer complaint and return a structured triage.\n"
                f"Set requires_legal_caution=true if legal, financial, health, "
                f"or safety issues appear.\n\nComplaint:\n{complaint}"
            ),
            schema=TriageResult,
            key="triage",
        ).run_async(ctx):
            yield e

        triage = TriageResult.model_validate(state["triage"])

        # ── 2. Validate recommended actions ───────────────────────────── #
        actions_text = "\n".join(
            f"- {a.action_type}" + (f" [{a.condition}]" if a.condition else "")
            for a in rec.recommended_actions
        )
        async for e in self._agent(
            name="validate",
            instruction=(
                f"Evaluate these resolution actions against the complaint.\n"
                f"Approve an action if it is reasonable and not clearly contradicted.\n"
                f"Conditions are hints — approve if the situation is plausible, "
                f"do not require the condition to be explicitly stated.\n"
                f"Legal caution active: {triage.requires_legal_caution}\n\n"
                f"Complaint summary: {triage.summary}\n"
                f"Domain: {triage.domain}\n\n"
                f"Actions:\n{actions_text}\n\n"
                f"Return approved_actions and is_applicable."
            ),
            schema=ValidatedActions,
            key="validated",
        ).run_async(ctx):
            yield e

        validated = ValidatedActions.model_validate(state["validated"])
        approved_text = "\n".join(
            f"- {a.action_type}" + (f": {a.value}" if a.value else "")
            for a in validated.approved_actions
        ) or "None"

        # ── 3. Similarity (unified, no deep/fast split) ───────────────── #
        pairs_text = "\n\n".join(
            f"[{i}] Q: {p['complaint']}\nA: {p['answer']}"
            for i, p in enumerate(self.historical_pairs)
        )
        async for e in self._agent(
            name="similarity",
            instruction=(
                f"Find historical answers relevant to this complaint.\n"
                f"Extract only the sentences that directly apply. Skip the rest.\n\n"
                f"Complaint: {complaint}\n\n"
                f"Historical pairs:\n{pairs_text}\n\n"
                f"Return a list of usable excerpts (empty list if nothing applies)."
            ),
            schema=SimilarityResult,
            key="similarity",
        ).run_async(ctx):
            yield e

        similarity = SimilarityResult.model_validate(state["similarity"])
        context_block = "\n\n".join(similarity.excerpts) or "No relevant historical context."

        # ── 4. Draft ──────────────────────────────────────────────────── #
        tone = rec.suggested_tone or triage.emotional_tone
        legal_note = (
            "Do not admit fault or make specific promises. " if triage.requires_legal_caution else ""
        )
        async for e in self._agent(
            name="draft",
            instruction=(
                f"Write a professional complaint response.\n"
                f"Tone: {tone}. Domain: {triage.domain}. {legal_note}\n"
                f"Use [NEEDS: X] for any missing information. Include all approved actions.\n"
                f"Structure: Acknowledgment → Resolution → Next Steps → Closing.\n\n"
                f"Complaint:\n{complaint}\n\n"
                f"Approved actions:\n{approved_text}\n\n"
                f"Relevant context:\n{context_block}"
            ),
            schema=DraftResult,
            key="draft",
        ).run_async(ctx):
            yield e

        draft = DraftResult.model_validate(state["draft"])

        # ── 5. Audit + rewrite loop ───────────────────────────────────── #
        for loop in range(MAX_AUDIT_LOOPS):
            async for e in self._agent(
                name=f"audit_{loop}",
                instruction=(
                    f"Audit this complaint response draft.\n"
                    f"Check: all approved actions are present, no fabricated facts, "
                    f"tone is appropriate.\n"
                    f"Legal caution: {triage.requires_legal_caution}\n\n"
                    f"Complaint: {complaint}\n"
                    f"Approved actions: {approved_text}\n\n"
                    f"Draft:\n{draft.draft}\n\n"
                    f"Set passed=true if acceptable. List issues briefly."
                ),
                schema=AuditResult,
                key="audit",
            ).run_async(ctx):
                yield e

            audit = AuditResult.model_validate(state["audit"])
            if audit.passed:
                break

            async for e in self._agent(
                name=f"rewrite_{loop}",
                instruction=(
                    f"Fix ONLY the flagged issues in this draft.\n\n"
                    f"Complaint: {complaint}\n"
                    f"Issues: {'; '.join(audit.issues)}\n"
                    f"Instructions: {audit.fix_instructions or 'Fix the listed issues.'}\n\n"
                    f"Current draft:\n{draft.draft}"
                ),
                schema=DraftResult,
                key="draft",
            ).run_async(ctx):
                yield e

            draft = DraftResult.model_validate(state["draft"])


# ------------------------------------------------------------------ #
#  public entry point                                                  #
# ------------------------------------------------------------------ #

async def _run_pipeline_async(
    complaint: str,
    historical_pairs: list[dict],
    recommendation: AnalyticRecommendation,
) -> dict:
    APP = "complaint_pipeline"
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=APP,
        user_id="agent",
        state={"complaint": complaint},
    )

    runner = Runner(
        agent=ComplaintPipeline(
            name=APP,
            recommendation=recommendation,
            historical_pairs=historical_pairs,
        ),
        app_name=APP,
        session_service=session_service,
    )

    async for _ in runner.run_async(
        user_id="agent",
        session_id=session.id,
        new_message=types.Content(role="user", parts=[types.Part(text=complaint)]),
    ):
        pass

    session_obj = await session_service.get_session(
        app_name=APP, user_id="agent", session_id=session.id
    )
    state = session_obj.state

    draft     = DraftResult.model_validate(state["draft"])
    audit     = AuditResult.model_validate(state["audit"])
    triage    = TriageResult.model_validate(state["triage"])
    validated = ValidatedActions.model_validate(state["validated"])

    return {
        "final_response":        draft.draft,
        "placeholders":          draft.placeholders,
        "confidence":            audit.confidence,
        "audit_passed":          audit.passed,
        "risk_level":            triage.risk_level,
        "requires_legal_review": triage.requires_legal_caution,
        "approved_actions":      [a.action_type for a in validated.approved_actions],
        "analytics_applicable":  validated.is_applicable,
    }


def run_complaint_pipeline(
    complaint: str,
    historical_pairs: list[dict],
    recommendation: AnalyticRecommendation,
) -> dict:
    return asyncio.run(_run_pipeline_async(complaint, historical_pairs, recommendation))
