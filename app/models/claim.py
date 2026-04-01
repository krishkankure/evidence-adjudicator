from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    raw_text: Mapped[str] = mapped_column(String, nullable=False)
    normalized_claim: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
