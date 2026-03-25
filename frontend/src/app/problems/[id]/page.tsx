import Link from "next/link";

import ProblemWorkbench from "../../../components/ProblemWorkbench";
import { apiGet } from "../../../lib/api";
import type { ProblemDetail } from "../../../lib/types";

interface ProblemPageProps {
  params: Promise<{ id: string }>;
}

export default async function ProblemPage({ params }: ProblemPageProps) {
  const { id } = await params;

  let problem: ProblemDetail | null = null;
  let error: string | null = null;

  try {
    problem = await apiGet<ProblemDetail>(`/api/problems/${id}`);
  } catch (err) {
    error = err instanceof Error ? err.message : "Failed to load problem";
  }

  if (!problem) {
    return (
      <main className="mx-auto max-w-4xl space-y-4 p-8">
        <Link href="/" className="text-sm text-blue-700 hover:underline">
          Back to Problems
        </Link>
        <h1 className="text-2xl font-semibold">Problem: {id}</h1>
        <div className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-800">{error ?? "Problem not found"}</div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-4xl space-y-4 p-8">
      <Link href="/" className="text-sm text-blue-700 hover:underline">
        Back to Problems
      </Link>

      <header>
        <h1 className="text-2xl font-semibold">{problem.title}</h1>
        <p className="mt-1 text-sm text-gray-700">
          {problem.id} • {problem.difficulty} • base `{problem.baseImage}` • health `{problem.healthPath}`
        </p>
      </header>

      <section className="rounded border border-gray-300 bg-white p-4">
        <h2 className="mb-2 text-lg font-semibold">Problem Statement</h2>
        <pre className="whitespace-pre-wrap text-sm text-gray-800">{problem.readme}</pre>
      </section>

      <ProblemWorkbench problem={problem} />
    </main>
  );
}
