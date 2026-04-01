from pydantic import BaseModel, Field

from app.schemas.common import StatusEnum


class ClaimCreateRequest(BaseModel):
    user_text: str = Field(min_length=3, max_length=5000)


class ClaimResponse(BaseModel):
    claim_id: str
    raw_text: str
    normalized_claim: str
    status: StatusEnum
    created_at: str


class ClaimDetailResponse(ClaimResponse):
    pass
