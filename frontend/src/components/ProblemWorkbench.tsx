"use client";

import { useState } from "react";

import Editor from "./Editor";
import { apiPost } from "../lib/api";
import type { ProblemDetail, SubmissionResult } from "../lib/types";

interface ProblemWorkbenchProps {
  problem: ProblemDetail;
}

export default function ProblemWorkbench({ problem }: ProblemWorkbenchProps) {
  const [dockerfileContent, setDockerfileContent] = useState<string>(
    `FROM ${problem.baseImage}\n\n# TODO: complete this Dockerfile\n`
  );
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SubmissionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiPost<SubmissionResult, { problem_id: string; dockerfile_content: string }>(
        "/api/submit",
        {
          problem_id: problem.id,
          dockerfile_content: dockerfileContent
        }
      );
      setResult(response);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Submission failed";
      setError(message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="mt-6 space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Try Dockerfile</h2>
        <p className="text-sm text-gray-700">Use this only for flow testing. You can replace UI later.</p>
      </div>

      <Editor value={dockerfileContent} onChange={setDockerfileContent} />

      <button
        type="button"
        onClick={onSubmit}
        disabled={loading}
        className="rounded bg-black px-4 py-2 text-white disabled:opacity-60"
      >
        {loading ? "Submitting..." : "Submit"}
      </button>

      {error ? <div className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-800">{error}</div> : null}

      {result ? (
        <div className="space-y-2 rounded border border-gray-300 bg-white p-4">
          <p className="text-sm">
            Result: <span className={result.passed ? "font-semibold text-green-700" : "font-semibold text-red-700"}>{result.passed ? "Passed" : "Failed"}</span>
          </p>
          <pre className="max-h-96 overflow-auto rounded bg-gray-900 p-3 text-xs text-gray-100">{result.logs}</pre>
        </div>
      ) : null}
    </section>
  );
}
