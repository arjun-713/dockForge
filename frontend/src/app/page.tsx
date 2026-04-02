import Link from "next/link";

import { apiGet } from "../lib/api";
import type { ProblemsListResponse } from "../lib/types";

const difficultyClassName: Record<string, string> = {
  easy: "difficulty-easy",
  medium: "difficulty-medium",
  hard: "difficulty-hard"
};

export default async function HomePage() {
  let data: ProblemsListResponse = { problems: [] };
  let error: string | null = null;

  try {
    data = await apiGet<ProblemsListResponse>("/api/problems");
  } catch (err) {
    error = err instanceof Error ? err.message : "Failed to fetch problems";
  }

  return (
    <main className="app-shell grid-lines px-4 py-4 text-[var(--text)] sm:px-6">
      <div className="mx-auto flex max-w-7xl flex-col gap-4">
        <header className="surface-panel overflow-hidden rounded-[28px]">
          <div className="flex flex-col gap-10 px-6 py-6 lg:flex-row lg:items-end lg:justify-between lg:px-8">
            <div className="max-w-3xl space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-[var(--border)] bg-[var(--primary-soft)] text-sm font-semibold text-[var(--primary)]">
                    DF
                  </div>
                  <div>
                    <p className="muted-label text-[11px]">Docker Problem Arena</p>
                    <h1 className="text-3xl font-semibold tracking-[-0.04em] sm:text-5xl">DockForge</h1>
                  </div>
                </div>
                <Link
                  href="/leaderboard"
                  className="hidden lg:inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[color:rgba(13,17,23,0.55)] px-4 py-2 text-sm font-semibold text-[var(--text)] transition hover:border-[var(--primary)] hover:text-[var(--primary)]"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 20h20"/><path d="m16 11-4-4-4 4"/><path d="M12 7v13"/></svg>
                  Leaderboards
                </Link>
              </div>
              <p className="max-w-2xl text-sm leading-7 text-[var(--text-secondary)] sm:text-base">
                Solve Docker challenges in a focused workspace: inspect the prompt, author the Dockerfile, run the
                container, and read logs without leaving the page.
              </p>
              <Link
                href="/leaderboard"
                className="inline-flex lg:hidden items-center gap-2 rounded-full border border-[var(--border)] bg-[color:rgba(13,17,23,0.55)] px-4 py-2 text-sm font-semibold text-[var(--text)] transition hover:border-[var(--primary)] hover:text-[var(--primary)]"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 20h20"/><path d="m16 11-4-4-4 4"/><path d="M12 7v13"/></svg>
                Leaderboards
              </Link>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <div className="surface-elevated rounded-2xl px-4 py-3">
                <p className="muted-label text-[10px]">Track</p>
                <p className="mt-2 text-lg font-semibold">Build, run, verify</p>
              </div>
              <div className="surface-elevated rounded-2xl px-4 py-3">
                <p className="muted-label text-[10px]">Problems</p>
                <p className="mt-2 text-lg font-semibold">{data.problems.length}</p>
              </div>
              <div className="surface-elevated rounded-2xl px-4 py-3">
                <p className="muted-label text-[10px]">Runtime</p>
                <p className="mt-2 text-lg font-semibold text-[var(--info)]">Host Docker</p>
              </div>
            </div>
          </div>
        </header>

        {error ? (
          <div className="surface-elevated rounded-2xl border-[color:var(--error)] px-4 py-3 text-sm text-[var(--error)]">
            {error}
          </div>
        ) : null}

        <section className="surface-panel overflow-hidden rounded-[28px]">
          <div className="flex items-center justify-between border-b border-[var(--border)] px-6 py-4">
            <div>
              <p className="muted-label text-[10px]">Problem Set</p>
              <h2 className="mt-1 text-xl font-semibold tracking-[-0.03em]">Practice Queue</h2>
            </div>
            <p className="text-sm text-[var(--text-secondary)]">LeetCode-style listing, Docker-first signals.</p>
          </div>

          <div className="hidden grid-cols-[120px_minmax(0,1.6fr)_140px_minmax(0,1fr)_140px] gap-4 border-b border-[var(--border)] px-6 py-3 text-xs uppercase tracking-[0.14em] text-[var(--text-muted)] md:grid">
            <span>ID</span>
            <span>Title</span>
            <span>Difficulty</span>
            <span>Concepts</span>
            <span>Open</span>
          </div>

          <div className="divide-y divide-[var(--border)]">
            {data.problems.map((problem) => (
              <article
                key={problem.id}
                className="group grid gap-3 px-6 py-5 transition-colors hover:bg-[var(--primary-soft)] md:grid-cols-[120px_minmax(0,1.6fr)_140px_minmax(0,1fr)_140px] md:items-center"
              >
                <p className="text-xs font-medium uppercase tracking-[0.12em] text-[var(--text-muted)] md:text-sm md:normal-case md:tracking-normal">
                  {problem.id}
                </p>
                <div>
                  <h3 className="text-base font-semibold text-[var(--text)] transition-colors group-hover:text-[var(--primary)]">
                    {problem.title}
                  </h3>
                  <p className="mt-1 text-sm text-[var(--text-secondary)] md:hidden">{problem.concepts.join(" • ")}</p>
                </div>
                <p className={`text-sm font-semibold capitalize ${difficultyClassName[problem.difficulty]}`}>
                  {problem.difficulty}
                </p>
                <p className="hidden text-sm text-[var(--text-secondary)] md:block">{problem.concepts.join(" • ")}</p>
                <div>
                  <Link
                    href={`/problems/${problem.id}`}
                    className="inline-flex items-center rounded-full border border-[var(--border)] bg-[var(--surface-elevated)] px-4 py-2 text-sm font-medium text-[var(--text)] transition hover:border-[var(--primary)] hover:text-[var(--primary)]"
                  >
                    Solve
                  </Link>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
