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
    GeneratedQueries,
)
from app.schemas.common import StatusEnum
from app.schemas.evidence import Citation, EvidenceBundle
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
    primary = {q.intent: q.query for q in queries.items}

    repo = AdjudicationRepository(db)
    record = repo.create(
        Adjudication(
            id=new_id("adj"),
            claim_id=claim.id,
            status=StatusEnum.processing.value,
            support_query=primary.get("direct_support", queries.items[0].query if queries.items else ""),
            oppose_query=primary.get("opposing", ""),
            alternative_query=primary.get("alternative_contextual", ""),
            evidence_json={"generated_queries": queries.model_dump(mode="json")},
            adjudication_json={},
            citations_json=[],
        )
    )

    evidence_service = EvidencePipelineService()
    evidence, citations = await evidence_service.run(claim.normalized_claim, queries)
    summary = await AdjudicatorService().adjudicate(claim.normalized_claim, evidence.accepted_evidence, evidence.rejected_candidates)

    record.status = StatusEnum.completed.value
    record.evidence_json = {
        **evidence.model_dump(mode="json"),
        "generated_queries": queries.model_dump(mode="json"),
    }
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

    evidence_blob = record.evidence_json or {}
    generated = GeneratedQueries(**(evidence_blob.get("generated_queries") or {"items": []}))
    cleaned_evidence = {k: v for k, v in evidence_blob.items() if k in {"retrieved_candidates", "accepted_evidence", "rejected_candidates"}}

    return AdjudicationDetailResponse(
        adjudication_id=record.id,
        claim_id=record.claim_id,
        status=StatusEnum(record.status),
        claim=ClaimSummary(raw_text=claim.raw_text, normalized_claim=claim.normalized_claim),
        generated_queries=generated,
        evidence=EvidenceBundle(**cleaned_evidence),
        adjudication=AdjudicationSummary(**(record.adjudication_json or {})),
        citations=[Citation(**c) for c in (record.citations_json or [])],
        created_at=record.created_at.isoformat(),
        completed_at=record.completed_at.isoformat() if record.completed_at else None,
    )


@router.get("/adjudications/{adjudication_id}/evidence", response_model=EvidenceBundle)
def get_evidence(adjudication_id: str, db: Session = Depends(get_db)) -> EvidenceBundle:
    record = AdjudicationRepository(db).get(adjudication_id)
    if not record:
        raise NotFoundError("Adjudication not found")
    data = record.evidence_json or {}
    cleaned = {k: v for k, v in data.items() if k in {"retrieved_candidates", "accepted_evidence", "rejected_candidates"}}
    return EvidenceBundle(**cleaned)


@router.get("/adjudications/{adjudication_id}/citations", response_model=list[Citation])
def get_citations(adjudication_id: str, db: Session = Depends(get_db)) -> list[Citation]:
    record = AdjudicationRepository(db).get(adjudication_id)
    if not record:
        raise NotFoundError("Adjudication not found")
    return [Citation(**c) for c in (record.citations_json or [])]
