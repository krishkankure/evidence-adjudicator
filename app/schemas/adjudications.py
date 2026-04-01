from pydantic import BaseModel, Field

from app.schemas.common import ConfidenceEnum, StatusEnum
from app.schemas.evidence import Citation, GroupedEvidence


class AdjudicationSummary(BaseModel):
    supporting_case: str
    opposing_case: str
    alternative_explanations: str
    best_supported_conclusion: str
    confidence: ConfidenceEnum
    limitations: str
    reasoning_summary: str


class AdjudicationCreateResponse(BaseModel):
    adjudication_id: str
    claim_id: str
    status: StatusEnum
    created_at: str
    completed_at: str | None


class ClaimSummary(BaseModel):
    raw_text: str
    normalized_claim: str


class Queries(BaseModel):
    support: str
    oppose: str
    alternative: str


class AdjudicationDetailResponse(BaseModel):
    adjudication_id: str
    claim_id: str
    status: StatusEnum
    claim: ClaimSummary
    queries: Queries
    evidence: GroupedEvidence
    adjudication: AdjudicationSummary
    citations: list[Citation] = Field(default_factory=list)
    created_at: str
    completed_at: str | None
