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
def health() -> dict[str, str]:
    return {
        "status": "healthy",
    }