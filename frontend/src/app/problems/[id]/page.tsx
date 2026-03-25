interface ProblemPageProps {
  params: Promise<{ id: string }>;
}

export default async function ProblemPage({ params }: ProblemPageProps) {
  const { id } = await params;

  return (
    <main className="mx-auto max-w-4xl p-8">
      <h1 className="text-2xl font-semibold">Problem: {id}</h1>
      <p className="mt-3 text-gray-700">Editor and submission UX will be built in Phase 4.</p>
    </main>
  );
}
