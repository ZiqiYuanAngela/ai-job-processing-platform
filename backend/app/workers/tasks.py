from celery.exceptions import MaxRetriesExceededError

from app.database import SessionLocal
from app.models.job import JobStatus
from app.services.job_service import (
    get_job,
    mark_job_dead_lettered,
    mark_job_failed,
    mark_job_running,
)
from app.services.workflow_service import (
    execute_document_summary_workflow,
)
from app.workers.celery_app import celery_app


RETRYABLE_EXCEPTIONS = (
    TimeoutError,
    ConnectionError,
)


@celery_app.task(
    bind=True,
    name="execute_job",
    max_retries=3,
)
def execute_job(
    self,
    job_id: str,
) -> None:
    db = SessionLocal()

    try:
        job = get_job(db, job_id)

        if job is None:
            return

        if job.status in {
            JobStatus.SUCCEEDED,
            JobStatus.CANCELLED,
        }:
            return

        job.attempt_count += 1
        db.commit()

        mark_job_running(db, job)

        if job.job_type == "document_summary":
            execute_document_summary_workflow(
                db=db,
                job=job,
            )
        else:
            raise ValueError(
                f"Unsupported job type: {job.job_type}"
            )

    except RETRYABLE_EXCEPTIONS as exc:
        job = get_job(db, job_id)

        if job is not None:
            job.error_message = str(exc)
            db.commit()

        countdown = 2 ** self.request.retries

        try:
            raise self.retry(
                exc=exc,
                countdown=countdown,
            )
        except MaxRetriesExceededError:
            if job is not None:
                mark_job_dead_lettered(
                    db=db,
                    job=job,
                    error_message=str(exc),
                )

    except ValueError as exc:
        job = get_job(db, job_id)

        if job is not None:
            mark_job_failed(
                db=db,
                job=job,
                error_message=str(exc),
            )

    except Exception as exc:
        job = get_job(db, job_id)

        if job is not None:
            if job.attempt_count >= job.max_attempts:
                mark_job_dead_lettered(
                    db=db,
                    job=job,
                    error_message=str(exc),
                )
            else:
                mark_job_failed(
                    db=db,
                    job=job,
                    error_message=str(exc),
                )

        raise

    finally:
        db.close()