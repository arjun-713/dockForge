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

export interface LeaderboardEntry {
  submissionId: string;
  problemId: string;
  finalScore: number;
  buildTimeScore: number;
  imageSizeScore: number;
  bestPracticeScore: number;
  difficultyMultiplier: number;
  createdAt: string;
}

export interface LeaderboardResponse {
  entries: LeaderboardEntry[];
}

