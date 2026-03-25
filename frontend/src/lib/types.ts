export interface ProblemSummary {
  id: string;
  title: string;
  difficulty: "easy" | "medium" | "hard";
  concepts: string[];
}

export interface ProblemsListResponse {
  problems: ProblemSummary[];
}

export interface ProblemDetail {
  id: string;
  title: string;
  difficulty: "easy" | "medium" | "hard";
  concepts: string[];
  appPort: number;
  baseImage: string;
  healthPath: string;
  readme: string;
}

export interface SubmissionResult {
  passed: boolean;
  logs: string;
}
