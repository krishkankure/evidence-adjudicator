from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class StatusEnum(str, Enum):
    created = "created"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class ConfidenceEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class BranchEnum(str, Enum):
    support = "support"
    oppose = "oppose"
    alternative = "alternative"


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Timestamped(BaseSchema):
    created_at: datetime
