from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.adjudication import Adjudication
from app.repositories.adjudications import AdjudicationRepository
from app.repositories.claims import ClaimRepository
from app.schemas.adjudications import (
    AdjudicationCreateResponse,
    AdjudicationDetailResponse,
    AdjudicationSummary,
    ClaimSummary,
    Queries,
)
from app.schemas.common import StatusEnum
from app.schemas.evidence import Citation, GroupedEvidence
from app.services.adjudicator import AdjudicatorService
from app.services.evidence_pipeline import EvidencePipelineService
from app.services.query_generator import QueryGeneratorService
from app.utils.ids import new_id

router = APIRouter(tags=["adjudications"])


@router.post("/claims/{claim_id}/adjudicate", response_model=AdjudicationCreateResponse)
async def adjudicate_claim(claim_id: str, db: Session = Depends(get_db)) -> AdjudicationCreateResponse:
    claim = ClaimRepository(db).get(claim_id)
    if not claim:
        raise NotFoundError("Claim not found")

    queries = QueryGeneratorService.generate(claim.normalized_claim)
    repo = AdjudicationRepository(db)
    record = repo.create(
        Adjudication(
            id=new_id("adj"),
            claim_id=claim.id,
            status=StatusEnum.processing.value,
            support_query=queries.support,
            oppose_query=queries.oppose,
            alternative_query=queries.alternative,
            evidence_json={},
            adjudication_json={},
            citations_json=[],
        )
    )

    evidence_service = EvidencePipelineService()
    grouped_evidence, citations = await evidence_service.run(queries.support, queries.oppose, queries.alternative)
    summary = await AdjudicatorService().adjudicate(
        claim.normalized_claim, grouped_evidence.supporting, grouped_evidence.opposing, grouped_evidence.alternative
    )

    record.status = StatusEnum.completed.value
    record.evidence_json = grouped_evidence.model_dump(mode="json")
    record.citations_json = [c.model_dump(mode="json") for c in citations]
    record.adjudication_json = summary.model_dump(mode="json")
    record.completed_at = datetime.now(timezone.utc)
    repo.update(record)

    return AdjudicationCreateResponse(
        adjudication_id=record.id,
        claim_id=record.claim_id,
        status=StatusEnum(record.status),
        created_at=record.created_at.isoformat(),
        completed_at=record.completed_at.isoformat() if record.completed_at else None,
    )


@router.get("/adjudications/{adjudication_id}", response_model=AdjudicationDetailResponse)
def get_adjudication(adjudication_id: str, db: Session = Depends(get_db)) -> AdjudicationDetailResponse:
    repo = AdjudicationRepository(db)
    record = repo.get(adjudication_id)
    if not record:
        raise NotFoundError("Adjudication not found")
    claim = ClaimRepository(db).get(record.claim_id)
    if not claim:
        raise NotFoundError("Claim not found")

    return AdjudicationDetailResponse(
        adjudication_id=record.id,
        claim_id=record.claim_id,
        status=StatusEnum(record.status),
        claim=ClaimSummary(raw_text=claim.raw_text, normalized_claim=claim.normalized_claim),
        queries=Queries(support=record.support_query, oppose=record.oppose_query, alternative=record.alternative_query),
        evidence=GroupedEvidence(**(record.evidence_json or {})),
        adjudication=AdjudicationSummary(**(record.adjudication_json or {})),
        citations=[Citation(**c) for c in (record.citations_json or [])],
        created_at=record.created_at.isoformat(),
        completed_at=record.completed_at.isoformat() if record.completed_at else None,
    )


@router.get("/adjudications/{adjudication_id}/evidence", response_model=GroupedEvidence)
def get_evidence(adjudication_id: str, db: Session = Depends(get_db)) -> GroupedEvidence:
    record = AdjudicationRepository(db).get(adjudication_id)
    if not record:
        raise NotFoundError("Adjudication not found")
    return GroupedEvidence(**(record.evidence_json or {}))


@router.get("/adjudications/{adjudication_id}/citations", response_model=list[Citation])
def get_citations(adjudication_id: str, db: Session = Depends(get_db)) -> list[Citation]:
    record = AdjudicationRepository(db).get(adjudication_id)
    if not record:
        raise NotFoundError("Adjudication not found")
    return [Citation(**c) for c in (record.citations_json or [])]
