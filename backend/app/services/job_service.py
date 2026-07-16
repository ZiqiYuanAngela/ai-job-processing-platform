from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job, JobStatus


def get_job(
    db: Session,
    job_id: str,
) -> Job | None:
    return db.get(Job, job_id)


def get_job_by_idempotency_key(
    db: Session,
    idempotency_key: str,
) -> Job | None:
    statement = select(Job).where(
        Job.idempotency_key == idempotency_key
    )

    return db.scalar(statement)


def mark_job_running(
    db: Session,
    job: Job,
) -> None:
    job.status = JobStatus.RUNNING
    job.started_at = job.started_at or datetime.utcnow()
    job.error_message = None

    db.commit()


def mark_step_started(
    db: Session,
    job: Job,
    step_name: str,
) -> None:
    job.current_step = step_name
    db.commit()


def mark_step_completed(
    db: Session,
    job: Job,
    step_name: str,
    progress: int,
) -> None:
    completed_steps = list(job.completed_steps or [])

    if step_name not in completed_steps:
        completed_steps.append(step_name)

    job.completed_steps = completed_steps
    job.progress = progress

    db.commit()


def is_step_completed(
    job: Job,
    step_name: str,
) -> bool:
    return step_name in (job.completed_steps or [])


def record_ai_usage(
    db: Session,
    job: Job,
    input_tokens: int,
    output_tokens: int,
    estimated_cost_usd: float,
) -> None:
    job.input_tokens += input_tokens
    job.output_tokens += output_tokens
    job.estimated_cost_usd += estimated_cost_usd

    db.commit()


def mark_job_succeeded(
    db: Session,
    job: Job,
    result: dict,
) -> None:
    job.status = JobStatus.SUCCEEDED
    job.result_data = result
    job.progress = 100
    job.current_step = None
    job.completed_at = datetime.utcnow()

    db.commit()


def mark_job_failed(
    db: Session,
    job: Job,
    error_message: str,
) -> None:
    job.status = JobStatus.FAILED
    job.error_message = error_message
    job.completed_at = datetime.utcnow()

    db.commit()


def mark_job_dead_lettered(
    db: Session,
    job: Job,
    error_message: str,
) -> None:
    job.status = JobStatus.DEAD_LETTERED
    job.error_message = error_message
    job.completed_at = datetime.utcnow()

    db.commit()


def mark_job_cancelled(
    db: Session,
    job: Job,
) -> None:
    job.status = JobStatus.CANCELLED
    job.current_step = None
    job.completed_at = datetime.utcnow()

    db.commit()


def check_cancellation(
    db: Session,
    job: Job,
) -> bool:
    db.refresh(job)

    if job.cancel_requested:
        mark_job_cancelled(db, job)
        return True

    return False


def ensure_budget_available(
    job: Job,
) -> None:
    if job.estimated_cost_usd >= job.max_cost_usd:
        raise RuntimeError(
            "Job cost budget has been exceeded."
        )