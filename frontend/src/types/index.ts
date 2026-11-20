export type AccountType = "student" | "teacher" | "admin";

export interface ProfileCourse {
  id: number;
  code: string;
  title: string;
  role: ApiEnrollment["role"];
}

export interface StudentProfile {
  accountType: AccountType;
  courses: ProfileCourse[];
  photoUrl: string | null;
  preferredLanguage: ProgrammingLanguage | null;
  memberSince: string;
  name: string;
  initials: string;
  email: string;
  course: string;
}

export interface ApiEnrollment {
  course_id: number;
  course_code: string;
  course_title: string;
  section_code: string | null;
  role: "student" | "instructor";
}

// GET /courses: one course from the signed-in user's point of view.
export interface ApiCourse {
  id: number;
  code: string;
  title: string;
  term: string;
  role: "student" | "instructor";
  section_code: string | null;
  instructor_names: string[];
  // Only sent to instructors.
  student_count: number | null;
}

export interface MyCourse {
  id: number;
  code: string;
  title: string;
  term: string;
  role: ApiCourse["role"];
  sectionCode: string | null;
  instructorNames: string[];
  studentCount: number | null;
}

export type CourseAssignmentStatus =
  | "draft"
  | "published"
  | "closed"
  | "archived";

export type FeedbackDepth = "hint" | "guided" | "detailed";

export interface ApiAssignment {
  id: number;
  title: string;
  instructions: string;
  status: CourseAssignmentStatus;
  feedback_depth: FeedbackDepth;
  due_at: string;
  published_at: string | null;
  created_at: string;
  attempt_count: number | null;
}

export interface CourseAssignment {
  id: number;
  title: string;
  instructions: string;
  status: CourseAssignmentStatus;
  feedbackDepth: FeedbackDepth;
  dueAt: string;
  publishedAt: string | null;
  // The student's own attempts; null for instructors.
  attemptCount: number | null;
}

// What an instructor fills in on the assignment form.
export interface AssignmentInput {
  title: string;
  instructions: string;
  dueAt: string;
  feedbackDepth: FeedbackDepth;
}

export interface ApiUser {
  id: number;
  email: string;
  full_name: string;
  is_admin: boolean;
  account_type: AccountType;
  photo_url: string | null;
  preferred_language: ProgrammingLanguage | "";
  created_at: string;
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

export type ThemePreference = "light" | "system" | "dark";

export type TestErrorType =
  | "wrong_answer"
  | "runtime_error"
  | "time_limit"
  | "memory_limit"
  | "output_limit"
  | "compile_error";

// For hidden tests the server sends null input and outputs (only a compiler
// message may be present), so students never see hidden data.
export interface ApiTestResult {
  test_name: string;
  is_hidden: boolean;
  passed: boolean;
  error_type: TestErrorType | null;
  runtime_ms: number | null;
  stdin_input: string | null;
  expected_output: string | null;
  actual_output: string | null;
  error_output: string | null;
}

export interface TestResult {
  testName: string;
  isHidden: boolean;
  passed: boolean;
  errorType: TestErrorType | null;
  runtimeMs: number | null;
  stdinInput: string | null;
  expectedOutput: string | null;
  actualOutput: string | null;
  errorOutput: string | null;
}

export type FeedbackKind = "strength" | "issue" | "next_step";

export interface ApiFeedback {
  source: "rules" | "ai";
  summary: string;
  created_at: string;
  items: {
    kind: FeedbackKind;
    message: string;
    error_category: string | null;
    line_start: number | null;
    line_end: number | null;
    criterion_title: string | null;
  }[];
}

export interface FeedbackItem {
  kind: FeedbackKind;
  message: string;
  lineStart: number | null;
  criterionTitle: string | null;
}

export interface Feedback {
  source: ApiFeedback["source"];
  summary: string;
  items: FeedbackItem[];
}

export interface ApiSubmission {
  id: number;
  attempt_number: number;
  status: "queued" | "running" | "completed" | "failed";
  submitted_at: string;
  language: ProgrammingLanguage | null;
  code: string;
  passed_count: number;
  test_count: number;
  results: ApiTestResult[];
  feedback: ApiFeedback | null;
}

export interface Submission {
  id: number;
  attemptNumber: number;
  status: ApiSubmission["status"];
  submittedAt: string;
  language: ProgrammingLanguage | null;
  code: string;
  passedCount: number;
  testCount: number;
  results: TestResult[];
  feedback: Feedback | null;
}

// GET /progress: daily practice, counted from submissions. Not a grade.
export interface ApiDailyProgress {
  today: string;
  streak_days: number;
  practiced_today: boolean;
  week: { date: string; submissions: number }[];
  tasks: {
    assignment_id: number;
    course_id: number;
    course_code: string;
    title: string;
    due_at: string;
    is_done: boolean;
    is_overdue: boolean;
  }[];
  completed_tasks: number;
  total_tasks: number;
}

export interface ProgressTask {
  assignmentId: number;
  courseId: number;
  courseCode: string;
  title: string;
  dueAt: string;
  isDone: boolean;
  isOverdue: boolean;
}

export interface DailyProgress {
  today: string;
  streakDays: number;
  practicedToday: boolean;
  week: { date: string; submissions: number }[];
  tasks: ProgressTask[];
  completedTasks: number;
  totalTasks: number;
}

// Rubric criteria and test cases of one assignment.
export interface ApiRubricCriterion {
  id: number;
  title: string;
  description: string;
  max_points: number;
  position: number;
}

export interface RubricCriterion {
  id: number;
  title: string;
  description: string;
  maxPoints: number;
  position: number;
}

export interface RubricCriterionInput {
  title: string;
  description: string;
  maxPoints: number;
}

export type TestVisibility = "public" | "hidden";

// Students only ever receive public tests, and only these four fields.
export interface ApiPublicTestCase {
  id: number;
  name: string;
  stdin_input: string;
  expected_output: string;
}

export interface ApiTestCase extends ApiPublicTestCase {
  visibility: TestVisibility;
  weight: number;
  time_limit_ms: number;
  criterion: number | null;
}

export interface PublicTestCase {
  id: number;
  name: string;
  stdinInput: string;
  expectedOutput: string;
}

export interface TestCaseInput {
  name: string;
  visibility: TestVisibility;
  stdinInput: string;
  expectedOutput: string;
  weight: number;
  timeLimitMs: number;
  criterionId: number | null;
}

// The instructor's view of a test, hidden ones included.
export interface AssignmentTestCase extends TestCaseInput {
  id: number;
}
