from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ComplexityLevel(str, Enum):
    simple = "simple"
    complex = "complex"


class TriageResult(BaseModel):
    complexity: ComplexityLevel
    risk_level: str          # low / medium / high
    domain: str
    emotional_tone: str
    requires_legal_caution: bool
    summary: str


class ResolutionAction(BaseModel):
    action_type: str
    value: Optional[str] = None
    condition: Optional[str] = None


class AnalyticRecommendation(BaseModel):
    recommended_actions: list[ResolutionAction]
    suggested_tone: Optional[str] = None
    confidence_score: float = Field(ge=0, le=1)


class ValidatedActions(BaseModel):
    approved_actions: list[ResolutionAction]
    is_applicable: bool


class SimilarityResult(BaseModel):
    excerpts: list[str]      # only the usable text snippets


class DraftResult(BaseModel):
    draft: str
    placeholders: list[str]


class AuditResult(BaseModel):
    passed: bool
    confidence: float = Field(ge=0, le=1)
    issues: list[str] = Field(default_factory=list)
    fix_instructions: Optional[str] = None
