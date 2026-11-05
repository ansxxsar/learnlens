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

export type AccountType = "student" | "teacher" | "pending_teacher" | "admin";

export interface StudentProfile {
  accountType: AccountType;
  teachingCourses: string[];
  name: string;
  initials: string;
  email: string;
  course: string;
  streakDays: number;
}

export interface ApiEnrollment {
  course_id: number;
  course_code: string;
  course_title: string;
  section_code: string | null;
  role: "student" | "instructor";
}

export interface ApiUser {
  id: number;
  email: string;
  full_name: string;
  is_admin: boolean;
  account_type: AccountType;
  enrollments: ApiEnrollment[];
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
