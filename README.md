# faaaah 🤖
**F**ault-**A**ware **A**nalytic-**A**ugmented **A**nswer **H**andler

A production-grade, multi-stage LLM pipeline for generating accurate and safe complaint response proposals — powered by Qwen served via vLLM.

## Quickstart
```bash
vllm serve Qwen/Qwen2.5-72B-Instruct --host 0.0.0.0 --port 8000 --guided-decoding-backend outlines
pip install openai pydantic
python example.py
```

## Pipeline

```mermaid
flowchart TD
    A([🧾 Complaint\n+ Historical Pairs\n+ Analytic Recommendation]) --> B

    B["🔍 Stage 1 — Triage\nComplexity · Risk · Domain\nEmotional tone · Legal caution"]
    B --> C

    C["✅ Stage 1.5 — Recommendation Validation\nValidate analytics vs complaint facts\nApprove / reject each action"]
    C -->|confidence ≥ 0.85\nno conflicts| D1["⚡ Override complexity → SIMPLE"]
    C --> D2{Complexity?}
    D1 --> D2

    D2 -->|complex / ambiguous| E["🧩 Stage 2 — Clarification Extraction\nMissing info · Ambiguities · Assumptions"]
    E --> F["🔬 Stage 3A — Deep Similarity Scoring\nStrict relevance audit of historical pairs"]

    D2 -->|simple| G["⚡ Stage 3B — Fast Similarity Scoring\nQuick relevance match"]

    F --> H
    G --> H

    H["✍️ Stage 4 — Draft Generation\nApproved actions + tone + historical context\nUses NEEDS: X placeholders for unknowns"]
    H --> I

    I["🛡️ Stage 5 — Safety & Hallucination Audit\nAll approved actions present?\nNo rejected actions?\nLegal caution respected?"]

    I -->|PASS| J(["✅ Final Response"])
    I -->|FAIL\nmax 2×| K["🔧 Stage 6 — Targeted Rewrite\nFix only flagged issues"]
    K --> I
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
- `schemas.py` — All Pydantic schemas
- `llm_client.py` — vLLM client wrapper
- `stage1_triage.py`
- `stage1_5_rec_validation.py`
- `stage2_clarification.py`
- `stage3a_deep_similarity.py`
- `stage3b_fast_similarity.py`
- `stage4_draft.py`
- `stage5_audit.py`
- `stage6_rewrite.py`
- `pipeline.py`
- `example.py`

## Safety
- `temperature=0.0` on all analytical stages
- guided JSON via Pydantic on all stages
- `[NEEDS: X]` placeholders instead of fabrication
- Legal caution propagation through all stages
- Max 2 rewrite loops

## License
MIT
