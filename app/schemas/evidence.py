from enum import Enum

from pydantic import BaseModel, Field


class EvidenceLabel(str, Enum):
    direct_support = "direct_support"
    indirect_contextual_support = "indirect_contextual_support"
    opposing = "opposing"
    alternative_contextual = "alternative_contextual"
    irrelevant = "irrelevant"


class EvidenceDecision(str, Enum):
    accepted = "accepted"
    rejected = "rejected"


class EvidenceCandidate(BaseModel):
    evidence_id: str
    source_type: str = "pubmed"
    query: str
    query_intent: str

    pmid: str | None = None
    title: str
    authors: list[str] = Field(default_factory=list)
    journal: str = ""
    publication_year: int | None = None
    abstract_snippet: str = ""
    extracted_finding: str = ""
    limitations_note: str = ""

    url: str = ""
    citation_link: str = ""

    retrieval_score: float = 0.0
    directness_score: float = 0.0
    final_score: float = 0.0

    label: EvidenceLabel
    decision: EvidenceDecision
    decision_reason: str


class Citation(BaseModel):
    citation_id: str
    source_type: str = "pubmed"
    pmid: str | None = None
    title: str
    journal: str = ""
    year: int | None = None
    url: str = ""
    citation_link: str = ""
    snippet: str = ""


class EvidenceBundle(BaseModel):
    retrieved_candidates: list[EvidenceCandidate] = Field(default_factory=list)
    accepted_evidence: list[EvidenceCandidate] = Field(default_factory=list)
    rejected_candidates: list[EvidenceCandidate] = Field(default_factory=list)
