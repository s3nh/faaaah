# faaaah 🤖
**F**ault-**A**ware **A**nalytic-**A**ugmented **A**nswer **H**andler

A production-grade, multi-stage LLM pipeline for generating accurate and safe complaint response proposals — powered by Qwen served via vLLM.

## Quickstart
```bash
vllm serve Qwen/Qwen2.5-72B-Instruct --host 0.0.0.0 --port 8000 --guided-decoding-backend outlines
pip install openai pydantic
python example.py
```

## Pipeline Stages
| Stage | Name | Fires when |
|---|---|---|
| 1 | Triage | always |
| 1.5 | Recommendation Validation | always |
| 2 | Clarification Extraction | complexity = complex/ambiguous |
| 3A | Deep Similarity Scoring | complexity = complex/ambiguous |
| 3B | Fast Similarity Scoring | complexity = simple |
| 4 | Draft Generation | always |
| 5 | Safety and Hallucination Audit | always |
| 6 | Targeted Rewrite | audit not passed |

## Structure
- schemas.py - All Pydantic schemas
- llm_client.py - vLLM client wrapper
- stage1_triage.py
- stage1_5_rec_validation.py
- stage2_clarification.py
- stage3a_deep_similarity.py
- stage3b_fast_similarity.py
- stage4_draft.py
- stage5_audit.py
- stage6_rewrite.py
- pipeline.py
- example.py

## Safety
- temperature=0.0 on all analytical stages
- guided_json via Pydantic on all stages
- [NEEDS: X] placeholders instead of fabrication
- Legal caution propagation through all stages
- Max 2 rewrite loops

## License
MIT
[Complaint] + [Historical Pairs] + [Analytic Recommendation]
        │                                     │
        ▼                                     │
  Stage 1: TRIAGE ◄────────────────────────┐  │
        │                                  │  │
        ▼                                  │  │
  Stage 1.5: REC VALIDATION ───────────────┘  │
  (validate analytics against complaint facts)│
        │                                     │
        ├─ confidence >= 0.85 + no conflicts ─┤
        │   → override complexity to SIMPLE   │
        │                                     │
        ├─ COMPLEX/AMBIGUOUS ──────────────┐  │
        │                                  │  │
        ▼                                  │  │
  Stage 2: CLARIFICATION                  │  │
        │                                  │  │
        ▼                                  │  │
  Stage 3A: DEEP SIMILARITY   Stage 3B ◄──┘  │
        │                        │            │
        └──────────┬─────────────┘            │
                   ▼                          │
           Stage 4: DRAFT ◄───── approved_actions + tone
           (historical ctx + analytics)
                   │
                   ▼
           Stage 5: AUDIT
           (hallucinations + approved actions present?
            + rejected actions absent? + legal check)
                   │
            ┌──────┴──────┐
           FAIL          PASS
            │              │
            ▼              ▼
       Stage 6: REWRITE  FINALIZE
            │
       Stage 5 (max 2x)
