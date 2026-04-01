from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.claim import Claim
from app.repositories.claims import ClaimRepository
from app.schemas.claims import ClaimCreateRequest, ClaimDetailResponse, ClaimResponse
from app.schemas.common import StatusEnum
from app.services.claim_parser import ClaimParserService
from app.utils.ids import new_id

router = APIRouter(prefix="/claims", tags=["claims"])


@router.post("", response_model=ClaimResponse)
def create_claim(payload: ClaimCreateRequest, db: Session = Depends(get_db)) -> ClaimResponse:
    raw_text, normalized = ClaimParserService.normalize(payload.user_text)
    claim = Claim(
        id=new_id("claim"),
        raw_text=raw_text,
        normalized_claim=normalized,
        status=StatusEnum.created.value,
    )
    saved = ClaimRepository(db).create(claim)
    return ClaimResponse(
        claim_id=saved.id,
        raw_text=saved.raw_text,
        normalized_claim=saved.normalized_claim,
        status=StatusEnum(saved.status),
        created_at=saved.created_at.isoformat(),
    )


@router.get("/{claim_id}", response_model=ClaimDetailResponse)
def get_claim(claim_id: str, db: Session = Depends(get_db)) -> ClaimDetailResponse:
    claim = ClaimRepository(db).get(claim_id)
    if not claim:
        raise NotFoundError("Claim not found")
    return ClaimDetailResponse(
        claim_id=claim.id,
        raw_text=claim.raw_text,
        normalized_claim=claim.normalized_claim,
        status=StatusEnum(claim.status),
        created_at=claim.created_at.isoformat(),
    )
