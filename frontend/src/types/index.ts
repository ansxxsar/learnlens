export type AssignmentStatus = "not-started" | "in-progress" | "completed";

export interface Assignment {
  id: number;
  title: string;
  description: string;
  difficulty: "Beginner" | "Intermediate" | "Advanced";
  topic: string;
  xp: number;
  status: AssignmentStatus;
  languages: ProgrammingLanguage[];
}

export interface Feedback {
  score: number;
  strengths: string[];
  improvements: string[];
  nextStep: string;
}

export interface StudentProgress {
  level: number;
  xp: number;
  nextLevelXp: number;
  completedAssignments: number;
  totalAssignments: number;
}

export interface SubmissionResult {
  passedTests: number;
  totalTests: number;
  feedback: Feedback;
}

export interface StudentProfile {
  name: string;
  initials: string;
  email: string;
  course: string;
  streakDays: number;
}

export type ProgrammingLanguage =
  | "python"
  | "java"
  | "cpp"
  | "javascript"
  | "html"
  | "css";

export interface LanguageOption {
  id: ProgrammingLanguage;
  label: string;
}
