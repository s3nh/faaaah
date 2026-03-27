from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ComplexityLevel(str, Enum):
    simple = "simple"
    complex = "complex"
    ambiguous = "ambiguous"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TriageResult(BaseModel):
    complexity: ComplexityLevel
    risk_level: RiskLevel
    domain: str
    emotional_tone: str
    key_claims: list[str]
    requires_legal_caution: bool
    summary: str


class MissingInfo(BaseModel):
    field: str
    reason: str
    criticality: str


class ClarificationResult(BaseModel):
    missing_information: list[MissingInfo]
    ambiguous_statements: list[str]
    assumed_defaults: list[str]


class HistoricalPairScore(BaseModel):
    index: int
    relevance_score: float = Field(ge=0, le=10)
    applicable_claims: list[str]
    conflicting_info: list[str]
    missing_coverage: list[str]
    usable_excerpt: str


class SimilarityResult(BaseModel):
    scored_pairs: list[HistoricalPairScore]
    coverage_summary: str
    recommended_threshold: float


class DraftResult(BaseModel):
    draft: str
    placeholders: list[str]
    assumptions_made: list[str]
    tone_used: str


class AuditFinding(BaseModel):
    claim: str
    supported_by: str
    severity: str
    fix_instruction: str


class AuditResult(BaseModel):
    findings: list[AuditFinding]
    passed: bool
    overall_confidence: float = Field(ge=0, le=1)
    rewrite_instructions: Optional[str] = None


class ResolutionAction(BaseModel):
    action_type: str
    value: Optional[str] = None
    condition: Optional[str] = None


class AnalyticRecommendation(BaseModel):
    recommended_actions: list[ResolutionAction]
    suggested_tone: Optional[str] = None
    priority_level: Optional[str] = None
    customer_segment: Optional[str] = None
    policy_references: list[str] = Field(default_factory=list)
    analyst_notes: Optional[str] = None
    confidence_score: float = Field(ge=0, le=1)


class RecommendationValidationResult(BaseModel):
    is_applicable: bool
    conflicts_with_complaint: list[str]
    conflicts_with_historical: list[str]
    approved_actions: list[ResolutionAction]
    rejected_actions: list[ResolutionAction]
    override_triage_complexity: Optional[str] = None
    validation_notes: str
