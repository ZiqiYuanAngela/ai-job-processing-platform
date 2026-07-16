import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
});

export async function createJob({
  text,
  maxCostUsd,
}) {
  const idempotencyKey = crypto.randomUUID();

  const response = await api.post(
    "/jobs",
    {
      job_type: "document_summary",
      input: {
        text,
      },
      max_cost_usd: maxCostUsd,
    },
    {
      headers: {
        "Idempotency-Key": idempotencyKey,
      },
    },
  );

  return response.data;
}

export async function listJobs() {
  const response = await api.get("/jobs");
  return response.data;
}

export async function getJob(jobId) {
  const response = await api.get(`/jobs/${jobId}`);
  return response.data;
}

export async function cancelJob(jobId) {
  const response = await api.post(
    `/jobs/${jobId}/cancel`,
  );

  return response.data;
}

export async function retryJob(jobId) {
  const response = await api.post(
    `/jobs/${jobId}/retry`,
  );

  return response.data;
}