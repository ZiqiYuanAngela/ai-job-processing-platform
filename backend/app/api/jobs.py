from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.job import Job, JobStatus
from app.schemas.job import (
    CreateJobRequest,
    CreateJobResponse,
    JobResponse,
)
from app.services.job_service import (
    get_job_by_idempotency_key,
)
from app.workers.tasks import execute_job


router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
)


@router.post(
    "",
    response_model=CreateJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_job(
    request: CreateJobRequest,
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
    ),
) -> CreateJobResponse:
    if request.job_type != "document_summary":
        raise HTTPException(
            status_code=400,
            detail="Unsupported job type",
        )

    if idempotency_key:
        existing_job = get_job_by_idempotency_key(
            db,
            idempotency_key,
        )

        if existing_job:
            return CreateJobResponse(
                id=existing_job.id,
                status=existing_job.status,
            )

    job = Job(
        job_type=request.job_type,
        status=JobStatus.QUEUED,
        idempotency_key=idempotency_key,
        input_data=request.input,
        max_cost_usd=request.max_cost_usd,
        max_attempts=settings.max_job_attempts,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    execute_job.delay(job.id)

    return CreateJobResponse(
        id=job.id,
        status=job.status,
    )


@router.get(
    "",
    response_model=list[JobResponse],
)
def list_jobs(
    db: Session = Depends(get_db),
) -> list[Job]:
    statement = (
        select(Job)
        .order_by(Job.created_at.desc())
        .limit(100)
    )

    return list(db.scalars(statement))


@router.get(
    "/{job_id}",
    response_model=JobResponse,
)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
) -> Job:
    job = db.get(Job, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return job


@router.post(
    "/{job_id}/cancel",
    response_model=JobResponse,
)
def cancel_job(
    job_id: str,
    db: Session = Depends(get_db),
) -> Job:
    job = db.get(Job, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    if job.status in {
        JobStatus.SUCCEEDED,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
        JobStatus.DEAD_LETTERED,
    }:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot cancel a job with "
                f"status {job.status.value}"
            ),
        )

    job.cancel_requested = True
    db.commit()
    db.refresh(job)

    return job


@router.post(
    "/{job_id}/retry",
    response_model=JobResponse,
)
def retry_job(
    job_id: str,
    db: Session = Depends(get_db),
) -> Job:
    job = db.get(Job, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    if job.status not in {
        JobStatus.FAILED,
        JobStatus.DEAD_LETTERED,
    }:
        raise HTTPException(
            status_code=409,
            detail="Only failed jobs can be retried",
        )

    job.status = JobStatus.QUEUED
    job.error_message = None
    job.completed_at = None
    job.cancel_requested = False

    db.commit()
    db.refresh(job)

    execute_job.delay(job.id)

    return job