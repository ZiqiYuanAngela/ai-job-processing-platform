import { useEffect, useState } from "react";

import {
  cancelJob,
  createJob,
  listJobs,
  retryJob,
} from "./api";

import "./App.css";

const TERMINAL_STATUSES = new Set([
  "SUCCEEDED",
  "FAILED",
  "CANCELLED",
  "DEAD_LETTERED",
]);

function App() {
  const [text, setText] = useState("");
  const [maxCostUsd, setMaxCostUsd] = useState(1);
  const [jobs, setJobs] = useState([]);
  const [isSubmitting, setIsSubmitting] =
    useState(false);
  const [error, setError] = useState("");

  async function refreshJobs() {
    try {
      const data = await listJobs();
      setJobs(data);
    } catch {
      setError("Unable to load jobs.");
    }
  }

  useEffect(() => {
    refreshJobs();

    const intervalId = window.setInterval(
      refreshJobs,
      2000,
    );

    return () => {
      window.clearInterval(intervalId);
    };
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();

    setError("");
    setIsSubmitting(true);

    try {
      await createJob({
        text,
        maxCostUsd,
      });

      setText("");
      await refreshJobs();
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ??
          "Unable to create job.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleCancel(jobId) {
    try {
      await cancelJob(jobId);
      await refreshJobs();
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ??
          "Unable to cancel job.",
      );
    }
  }

  async function handleRetry(jobId) {
    try {
      await retryJob(jobId);
      await refreshJobs();
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ??
          "Unable to retry job.",
      );
    }
  }

  return (
    <main className="container">
      <header>
        <h1>Durable AI Job Platform</h1>
        <p>
          Submit, monitor, cancel, and retry
          long-running AI workflows.
        </p>
      </header>

      <section className="panel">
        <h2>Create AI job</h2>

        <form onSubmit={handleSubmit}>
          <label>
            Document
            <textarea
              rows="10"
              value={text}
              onChange={(event) =>
                setText(event.target.value)
              }
              placeholder="Paste a technical document..."
              required
            />
          </label>

          <label>
            Maximum cost
            <input
              type="number"
              min="0.01"
              max="10"
              step="0.01"
              value={maxCostUsd}
              onChange={(event) =>
                setMaxCostUsd(
                  Number(event.target.value),
                )
              }
            />
          </label>

          <button
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting
              ? "Submitting..."
              : "Submit job"}
          </button>
        </form>

        {error && (
          <p className="error">{error}</p>
        )}
      </section>

      <section className="panel">
        <div className="section-header">
          <h2>Jobs</h2>

          <button onClick={refreshJobs}>
            Refresh
          </button>
        </div>

        <div className="job-list">
          {jobs.map((job) => (
            <article
              className="job-card"
              key={job.id}
            >
              <div className="job-header">
                <div>
                  <strong>{job.job_type}</strong>
                  <p className="job-id">
                    {job.id}
                  </p>
                </div>

                <span className="status">
                  {job.status}
                </span>
              </div>

              <progress
                value={job.progress}
                max="100"
              />

              <dl>
                <div>
                  <dt>Progress</dt>
                  <dd>{job.progress}%</dd>
                </div>

                <div>
                  <dt>Current step</dt>
                  <dd>
                    {job.current_step ?? "—"}
                  </dd>
                </div>

                <div>
                  <dt>Attempts</dt>
                  <dd>
                    {job.attempt_count}/
                    {job.max_attempts}
                  </dd>
                </div>

                <div>
                  <dt>Cost</dt>
                  <dd>
                    $
                    {job.estimated_cost_usd.toFixed(
                      4,
                    )}
                  </dd>
                </div>
              </dl>

              {job.error_message && (
                <p className="error">
                  {job.error_message}
                </p>
              )}

              {job.result_data?.summary && (
                <details>
                  <summary>View result</summary>
                  <p>
                    {job.result_data.summary}
                  </p>
                </details>
              )}

              <div className="actions">
                {!TERMINAL_STATUSES.has(
                  job.status,
                ) && (
                  <button
                    onClick={() =>
                      handleCancel(job.id)
                    }
                  >
                    Cancel
                  </button>
                )}

                {[
                  "FAILED",
                  "DEAD_LETTERED",
                ].includes(job.status) && (
                  <button
                    onClick={() =>
                      handleRetry(job.id)
                    }
                  >
                    Retry
                  </button>
                )}
              </div>
            </article>
          ))}

          {jobs.length === 0 && (
            <p>No jobs yet.</p>
          )}
        </div>
      </section>
    </main>
  );
}

export default App;