from sqlalchemy.orm import Session

from app.models.claim import Claim


class ClaimRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, claim: Claim) -> Claim:
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)
        return claim

    def get(self, claim_id: str) -> Claim | None:
        return self.db.get(Claim, claim_id)
