import { mockAssignments, mockProgress, mockStudent } from "../data/mockData";
import type {
  ApiUser,
  Assignment,
  ProgrammingLanguage,
  StudentProfile,
  StudentProgress,
  SubmissionResult,
} from "../types";
import { evaluateAssignment } from "./mockEvaluator";

const delay = (milliseconds: number): Promise<void> =>
  new Promise((resolve) => {
    window.setTimeout(resolve, milliseconds);
  });

const REQUEST_TIMEOUT_MS = 10_000;
const GENERIC_ERROR = "Something went wrong. Please try again.";

export class ApiError extends Error {
  readonly status: number;
  readonly fieldErrors: Record<string, string[]>;

  constructor(
    status: number,
    message: string,
    fieldErrors: Record<string, string[]> = {},
  ) {
    super(message);
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

// The API answers with {"detail": "..."} or {"field": ["...", ...]}. Other
// responses, such as a server error page, get a generic message instead.
const toApiError = async (response: Response): Promise<ApiError> => {
  const body: unknown = await response.json().catch(() => null);

  if (response.status >= 500 || typeof body !== "object" || body === null) {
    return new ApiError(response.status, GENERIC_ERROR);
  }

  const { detail, ...fields } = body as Record<string, unknown>;
  if (typeof detail === "string") {
    return new ApiError(response.status, detail);
  }

  const fieldErrors: Record<string, string[]> = {};
  for (const [field, messages] of Object.entries(fields)) {
    if (Array.isArray(messages)) {
      fieldErrors[field] = messages.map(String);
    }
  }
  return new ApiError(
    response.status,
    "Please check the highlighted fields.",
    fieldErrors,
  );
};

const sendRequest = async (
  path: string,
  init: RequestInit = {},
): Promise<Response> => {
  let response: Response;

  try {
    response = await fetch(path, {
      ...init,
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
  } catch {
    throw new ApiError(0, "Unable to reach LearnLens. Please try again.");
  }

  if (!response.ok) {
    throw await toApiError(response);
  }
  return response;
};

const readCsrfToken = (): string | undefined =>
  document.cookie
    .split("; ")
    .find((cookie) => cookie.startsWith("csrftoken="))
    ?.slice("csrftoken=".length);

const postJson = async (path: string, body: object = {}): Promise<Response> => {
  if (!readCsrfToken()) {
    await sendRequest("/auth/csrf");
  }

  return sendRequest(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": readCsrfToken() ?? "",
    },
    body: JSON.stringify(body),
  });
};

const toStudentProfile = (user: ApiUser): StudentProfile => ({
  accountType: user.account_type,
  teachingCourses: user.enrollments
    .filter((enrollment) => enrollment.role === "instructor")
    .map((enrollment) => enrollment.course_title),
  name: user.full_name,
  initials: user.full_name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join(""),
  email: user.email,
  course: user.enrollments[0]?.course_title ?? "No course yet",
  // Mock until the /progress API exists.
  streakDays: mockStudent.streakDays,
});

export const fetchAssignments = async (): Promise<Assignment[]> => {
  await delay(600);
  return mockAssignments;
};

export const fetchProgress = async (): Promise<StudentProgress> => {
  await delay(400);
  return mockProgress;
};

export const signIn = async (
  email: string,
  password: string,
): Promise<StudentProfile> => {
  const response = await postJson("/auth/sign-in", { email, password });
  return toStudentProfile((await response.json()) as ApiUser);
};

export const register = async (
  fullName: string,
  email: string,
  password: string,
): Promise<StudentProfile> => {
  const response = await postJson("/auth/register", {
    full_name: fullName,
    email,
    password,
  });
  return toStudentProfile((await response.json()) as ApiUser);
};

export const signOut = async (): Promise<void> => {
  try {
    await postJson("/auth/sign-out");
  } catch (error) {
    // A 401 means the session already ended, which is what the user wanted.
    if (!(error instanceof ApiError && error.status === 401)) {
      throw error;
    }
  }
};

// Returns null when nobody is signed in.
export const fetchCurrentStudent = async (): Promise<StudentProfile | null> => {
  try {
    const response = await sendRequest("/auth/me");
    return toStudentProfile((await response.json()) as ApiUser);
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return null;
    }
    throw error;
  }
};

export const submitSolution = async (
  assignmentId: number,
  language: ProgrammingLanguage,
  code: string,
): Promise<SubmissionResult> => {
  await delay(900);

  if (code.trim().length === 0) {
    throw new Error("Please enter your solution.");
  }

  const checks = evaluateAssignment(assignmentId, language, code);
  const passedChecks = checks.filter((check) => check.passed);
  const failedChecks = checks.filter((check) => !check.passed);
  const score = Math.round((passedChecks.length / checks.length) * 100);

  return {
    passedTests: passedChecks.length,
    totalTests: checks.length,
    feedback: {
      score,
      strengths:
        passedChecks.length > 0
          ? passedChecks.map((check) => check.success)
          : ["You started an attempt and can now improve it."],
      improvements:
        failedChecks.length > 0
          ? failedChecks.map((check) => check.improvement)
          : ["All current learning checks passed."],
      nextStep:
        score === 100
          ? "Excellent. Try solving the same task with a different approach."
          : "Use the feedback above, revise your solution, and submit again.",
    },
  };
};
