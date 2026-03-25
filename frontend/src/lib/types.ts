export interface ProblemSummary {
  id: string;
  title: string;
  difficulty: "easy" | "medium" | "hard";
}

export interface SubmissionResult {
  passed: boolean;
  logs: string;
}
