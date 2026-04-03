from pydantic import BaseModel, Field

from app.schemas.common import ConfidenceEnum, StatusEnum
from app.schemas.evidence import Citation, EvidenceBundle


class AdjudicationSummary(BaseModel):
    supporting_case: str
    opposing_case: str
    alternative_explanations: str
    best_supported_conclusion: str
    confidence: ConfidenceEnum
    limitations: str
    reasoning_summary: str
    evidence_grounding_note: str


class AdjudicationCreateResponse(BaseModel):
    adjudication_id: str
    claim_id: str
    status: StatusEnum
    created_at: str
    completed_at: str | None


class ClaimSummary(BaseModel):
    raw_text: str
    normalized_claim: str


class GeneratedQuery(BaseModel):
    query: str
    intent: str
    backend: str = "pubmed"


class GeneratedQueries(BaseModel):
    items: list[GeneratedQuery] = Field(default_factory=list)


class AdjudicationDetailResponse(BaseModel):
    adjudication_id: str
    claim_id: str
    status: StatusEnum
    claim: ClaimSummary
    generated_queries: GeneratedQueries
    evidence: EvidenceBundle
    adjudication: AdjudicationSummary
    citations: list[Citation] = Field(default_factory=list)
    created_at: str
    completed_at: str | None
