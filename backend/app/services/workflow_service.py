from sqlalchemy.orm import Session

from app.models.job import Job
from app.services.ai_service import generate_text
from app.services.job_service import (
    check_cancellation,
    ensure_budget_available,
    is_step_completed,
    mark_job_succeeded,
    mark_step_completed,
    mark_step_started,
    record_ai_usage,
)


def split_text(
    text: str,
    chunk_size: int = 4000,
) -> list[str]:
    return [
        text[index:index + chunk_size]
        for index in range(0, len(text), chunk_size)
    ]


def execute_document_summary_workflow(
    db: Session,
    job: Job,
) -> None:
    input_data = dict(job.input_data)
    result_data = dict(job.result_data or {})

    # Step 1: Validate input
    step_name = "validate_input"

    if not is_step_completed(job, step_name):
        mark_step_started(db, job, step_name)

        text = input_data.get("text")

        if not isinstance(text, str):
            raise ValueError(
                "input.text must be a string"
            )

        if len(text.strip()) < 100:
            raise ValueError(
                "input.text must contain at least 100 characters"
            )

        mark_step_completed(
            db=db,
            job=job,
            step_name=step_name,
            progress=10,
        )

    if check_cancellation(db, job):
        return

    # Step 2: Split document
    step_name = "split_document"

    if not is_step_completed(job, step_name):
        mark_step_started(db, job, step_name)

        chunks = split_text(input_data["text"])

        result_data["chunks"] = chunks
        job.result_data = result_data
        db.commit()

        mark_step_completed(
            db=db,
            job=job,
            step_name=step_name,
            progress=20,
        )

    if check_cancellation(db, job):
        return

    # Step 3: Summarize chunks
    step_name = "summarize_chunks"

    if not is_step_completed(job, step_name):
        mark_step_started(db, job, step_name)

        chunks = result_data["chunks"]
        chunk_summaries = result_data.get(
            "chunk_summaries",
            [],
        )

        start_index = len(chunk_summaries)

        for index in range(start_index, len(chunks)):
            if check_cancellation(db, job):
                return

            ensure_budget_available(job)

            ai_result = generate_text(
                system_prompt=(
                    "You summarize technical documents. "
                    "Return a concise, accurate summary."
                ),
                user_prompt=chunks[index],
            )

            chunk_summaries.append(ai_result.content)

            result_data["chunk_summaries"] = chunk_summaries
            job.result_data = result_data

            record_ai_usage(
                db=db,
                job=job,
                input_tokens=ai_result.input_tokens,
                output_tokens=ai_result.output_tokens,
                estimated_cost_usd=(
                    ai_result.estimated_cost_usd
                ),
            )

            progress = 20 + int(
                ((index + 1) / len(chunks)) * 50
            )

            job.progress = progress
            db.commit()

        mark_step_completed(
            db=db,
            job=job,
            step_name=step_name,
            progress=70,
        )

    if check_cancellation(db, job):
        return

    # Step 4: Combine summaries
    step_name = "combine_summaries"

    if not is_step_completed(job, step_name):
        mark_step_started(db, job, step_name)

        ensure_budget_available(job)

        combined_input = "\n\n".join(
            result_data["chunk_summaries"]
        )

        ai_result = generate_text(
            system_prompt=(
                "Combine the section summaries into a "
                "structured technical summary. Include: "
                "overview, key points, risks, and next actions."
            ),
            user_prompt=combined_input,
        )

        result_data["final_summary"] = ai_result.content
        job.result_data = result_data

        record_ai_usage(
            db=db,
            job=job,
            input_tokens=ai_result.input_tokens,
            output_tokens=ai_result.output_tokens,
            estimated_cost_usd=(
                ai_result.estimated_cost_usd
            ),
        )

        mark_step_completed(
            db=db,
            job=job,
            step_name=step_name,
            progress=90,
        )

    if check_cancellation(db, job):
        return

    # Step 5: Save final result
    step_name = "save_result"

    if not is_step_completed(job, step_name):
        mark_step_started(db, job, step_name)

        final_result = {
            "summary": result_data["final_summary"],
            "chunk_count": len(result_data["chunks"]),
        }

        mark_step_completed(
            db=db,
            job=job,
            step_name=step_name,
            progress=100,
        )

        mark_job_succeeded(
            db=db,
            job=job,
            result=final_result,
        )