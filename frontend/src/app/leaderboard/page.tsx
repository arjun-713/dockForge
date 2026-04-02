import Link from "next/link";
import { apiGet } from "../../lib/api";
import type { LeaderboardResponse, LeaderboardEntry } from "../../lib/types";

export const dynamic = "force-dynamic";

export default async function LeaderboardPage({
  searchParams
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}) {
  const unresolvedSearchParams = await searchParams;
  const problemId = typeof unresolvedSearchParams.problemId === "string" ? unresolvedSearchParams.problemId : null;

  let data: LeaderboardResponse = { entries: [] };
  let error: string | null = null;

  try {
    const url = problemId ? `/api/leaderboard?problemId=${problemId}` : "/api/leaderboard";
    data = await apiGet<LeaderboardResponse>(url);
  } catch (err) {
    error = err instanceof Error ? err.message : "Failed to load leaderboard";
  }

  const title = problemId ? `Global Leaderboard: ${problemId}` : "Global Leaderboard";
  const desc = problemId 
    ? `Top solutions for challenge ${problemId}` 
    : "Top Dockerfile implementations across all problems";

  return (
    <main className="app-shell grid-lines px-4 py-4 sm:px-6">
      <div className="mx-auto flex max-w-5xl flex-col gap-4">
        
        <div className="flex items-center justify-between rounded-2xl border border-[var(--border)] bg-[color:rgba(13,17,23,0.55)] px-4 py-3 backdrop-blur md:px-5">
          <div className="flex items-center gap-3">
            <Link href="/" className="inline-flex text-sm text-[var(--primary)] transition hover:text-[var(--primary-hover)]">
              Problems
            </Link>
            <span className="text-[var(--text-muted)]">/</span>
            <span className="text-sm text-[var(--text-secondary)]">Leaderboard</span>
          </div>
          {problemId && (
            <Link href="/leaderboard" className="text-xs text-[var(--primary)] hover:underline">
              View All Problems
            </Link>
          )}
        </div>

        <section className="surface-panel overflow-hidden rounded-[28px]">
          <div className="flex items-center justify-between border-b border-[var(--border)] px-6 py-4">
            <div>
              <p className="muted-label text-[10px]">Rankings</p>
              <h2 className="mt-1 text-xl font-semibold tracking-[-0.03em]">{title}</h2>
            </div>
            <p className="hidden text-sm text-[var(--text-secondary)] sm:block">{desc}</p>
          </div>

          {error ? (
            <div className="p-6">
               <div className="rounded-2xl border-[color:var(--error)] bg-[color:rgba(239,68,68,0.08)] px-4 py-3 text-sm text-[var(--error)]">
                 {error}
               </div>
            </div>
          ) : data.entries.length === 0 ? (
             <div className="p-12 text-center text-[var(--text-secondary)]">
               No submissions yet. Be the first to solve a problem!
             </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-[var(--border)] bg-[var(--surface-elevated)] text-xs uppercase tracking-[0.14em] text-[var(--text-muted)]">
                  <tr>
                    <th className="px-6 py-4 font-semibold">Rank</th>
                    <th className="px-6 py-4 font-semibold">Submission ID</th>
                    {!problemId && <th className="px-6 py-4 font-semibold">Problem</th>}
                    <th className="px-6 py-4 font-semibold text-right">Score</th>
                    <th className="px-6 py-4 font-semibold text-right">Build</th>
                    <th className="px-6 py-4 font-semibold text-right">Size</th>
                    <th className="px-6 py-4 font-semibold text-right">Best Practice</th>
                    <th className="px-6 py-4 font-semibold text-right">When</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {data.entries.map((entry: LeaderboardEntry, idx: number) => (
                    <tr key={entry.submissionId} className="transition-colors hover:bg-[var(--primary-soft)] group">
                      <td className="px-6 py-4 font-medium">#{idx + 1}</td>
                      <td className="px-6 py-4 font-mono text-xs text-[var(--text-secondary)]">
                        {entry.submissionId.substring(0, 8)}...
                      </td>
                      {!problemId && (
                        <td className="px-6 py-4 font-medium group-hover:text-[var(--primary)] text-[var(--text-secondary)]">
                           <Link href={`/problems/${entry.problemId}`} className="hover:underline hover:text-[var(--primary)]">
                             {entry.problemId}
                           </Link>
                        </td>
                      )}
                      <td className="px-6 py-4 text-right font-bold text-[var(--primary)]">
                        {entry.finalScore.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 text-right">{entry.buildTimeScore}</td>
                      <td className="px-6 py-4 text-right">{entry.imageSizeScore}</td>
                      <td className="px-6 py-4 text-right">{entry.bestPracticeScore}</td>
                      <td className="px-6 py-4 text-right whitespace-nowrap text-xs text-[var(--text-muted)]">
                         {new Date(entry.createdAt).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
