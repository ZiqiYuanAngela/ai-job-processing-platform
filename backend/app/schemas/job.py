from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.job import JobStatus


class CreateJobRequest(BaseModel):
    job_type: str = Field(
        default="document_summary",
        max_length=100,
    )

    input: dict[str, Any]

    max_cost_usd: float = Field(
        default=1.00,
        gt=0,
        le=10,
    )


class JobResponse(BaseModel):
    id: str
    job_type: str
    status: JobStatus

    input_data: dict[str, Any]
    result_data: dict[str, Any] | None

    current_step: str | None
    completed_steps: list[str]
    progress: int

    attempt_count: int
    max_attempts: int

    cancel_requested: bool

    max_cost_usd: float
    estimated_cost_usd: float

    input_tokens: int
    output_tokens: int

    error_message: str | None

    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {
        "from_attributes": True,
    }


class CreateJobResponse(BaseModel):
    id: str
    status: JobStatus