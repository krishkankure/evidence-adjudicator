from pydantic import BaseModel, Field

from app.schemas.common import BranchEnum


class EvidenceCard(BaseModel):
    evidence_id: str
    source_type: str = "pubmed"
    pmid: str | None = None
    title: str
    abstract_snippet: str = ""
    authors: list[str] = Field(default_factory=list)
    journal: str = ""
    publication_year: int | None = None
    query_branch: BranchEnum
    relevance_score: float
    url: str = ""
    extracted_finding: str = ""
    limitation_note: str


class Citation(BaseModel):
    citation_id: str
    pmid: str | None = None
    title: str
    journal: str = ""
    year: int | None = None
    url: str = ""
    quote_or_snippet: str = ""
    branch: BranchEnum


class GroupedEvidence(BaseModel):
    supporting: list[EvidenceCard] = Field(default_factory=list)
    opposing: list[EvidenceCard] = Field(default_factory=list)
    alternative: list[EvidenceCard] = Field(default_factory=list)
