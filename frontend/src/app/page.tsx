import Link from "next/link";

import { apiGet } from "../lib/api";
import type { ProblemsListResponse } from "../lib/types";

export default async function HomePage() {
  let data: ProblemsListResponse = { problems: [] };
  let error: string | null = null;

  try {
    data = await apiGet<ProblemsListResponse>("/api/problems");
  } catch (err) {
    error = err instanceof Error ? err.message : "Failed to fetch problems";
  }

  return (
    <main className="mx-auto max-w-4xl space-y-6 p-8">
      <header>
        <h1 className="text-3xl font-semibold">DockForge</h1>
        <p className="mt-2 text-gray-700">Minimal test UI for problem listing and submissions.</p>
      </header>

      {error ? <div className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-800">{error}</div> : null}

      <section className="space-y-3">
        {data.problems.map((problem) => (
          <article key={problem.id} className="rounded border border-gray-300 bg-white p-4">
            <h2 className="text-lg font-semibold">{problem.title}</h2>
            <p className="text-sm text-gray-700">
              {problem.id} • {problem.difficulty}
            </p>
            <p className="mt-1 text-sm text-gray-700">Concepts: {problem.concepts.join(", ")}</p>
            <Link href={`/problems/${problem.id}`} className="mt-3 inline-block text-sm font-medium text-blue-700 hover:underline">
              Open Problem
            </Link>
          </article>
        ))}
      </section>
    </main>
  );
}
