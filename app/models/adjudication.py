from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Adjudication(Base):
    __tablename__ = "adjudications"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    claim_id: Mapped[str] = mapped_column(String, ForeignKey("claims.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)

    support_query: Mapped[str] = mapped_column(String, nullable=False)
    oppose_query: Mapped[str] = mapped_column(String, nullable=False)
    alternative_query: Mapped[str] = mapped_column(String, nullable=False)

    evidence_json: Mapped[dict] = mapped_column(JSON, default=dict)
    adjudication_json: Mapped[dict] = mapped_column(JSON, default=dict)
    citations_json: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
