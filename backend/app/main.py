from fastapi import Depends
from redis import Redis
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.database import get_db

from app.logging_config import configure_logging
configure_logging()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.jobs import router as jobs_router


app = FastAPI(
    title="Durable AI Job Platform",
    version="0.1.0",
    description=(
        "A durable execution platform for "
        "long-running AI workflows."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)


@app.get("/health")
def health(
    db: Session = Depends(get_db),
) -> dict[str, str]:
    db.execute(text("SELECT 1"))

    redis_client = Redis.from_url(
        settings.redis_url
    )

    redis_client.ping()

    return {
        "status": "healthy",
        "database": "connected",
        "queue": "connected",
    }