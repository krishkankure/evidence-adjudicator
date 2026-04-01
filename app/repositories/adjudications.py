from sqlalchemy.orm import Session

from app.models.adjudication import Adjudication


class AdjudicationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, adjudication: Adjudication) -> Adjudication:
        self.db.add(adjudication)
        self.db.commit()
        self.db.refresh(adjudication)
        return adjudication

    def update(self, adjudication: Adjudication) -> Adjudication:
        self.db.add(adjudication)
        self.db.commit()
        self.db.refresh(adjudication)
        return adjudication

    def get(self, adjudication_id: str) -> Adjudication | None:
        return self.db.get(Adjudication, adjudication_id)
