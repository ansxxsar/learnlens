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
const UPLOAD_TIMEOUT_MS = 60_000;
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
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
      ...init,
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

const sendWithCsrf = async (
  path: string,
  init: RequestInit & { headers?: Record<string, string> },
): Promise<Response> => {
  if (!readCsrfToken()) {
    await sendRequest("/auth/csrf");
  }

  return sendRequest(path, {
    ...init,
    headers: { ...init.headers, "X-CSRFToken": readCsrfToken() ?? "" },
  });
};

const sendJson = (
  path: string,
  method: "POST" | "PATCH",
  body: object = {},
): Promise<Response> =>
  sendWithCsrf(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

const postJson = (path: string, body: object = {}): Promise<Response> =>
  sendJson(path, "POST", body);

const toStudentProfile = (user: ApiUser): StudentProfile => ({
  accountType: user.account_type,
  teachingCourses: user.enrollments
    .filter((enrollment) => enrollment.role === "instructor")
    .map((enrollment) => enrollment.course_title),
  courses: user.enrollments.map((enrollment) => ({
    id: enrollment.course_id,
    code: enrollment.course_code,
    title: enrollment.course_title,
    role: enrollment.role,
  })),
  photoUrl: user.photo_url,
  preferredLanguage: user.preferred_language || null,
  memberSince: user.created_at,
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

const readProfile = async (response: Response): Promise<StudentProfile> =>
  toStudentProfile((await response.json()) as ApiUser);

export const updateProfile = async (changes: {
  fullName: string;
  preferredLanguage: ProgrammingLanguage | null;
}): Promise<StudentProfile> =>
  readProfile(
    await sendJson("/auth/me", "PATCH", {
      full_name: changes.fullName,
      preferred_language: changes.preferredLanguage ?? "",
    }),
  );

export const uploadProfilePhoto = async (
  photo: File,
): Promise<StudentProfile> => {
  const body = new FormData();
  body.append("photo", photo);

  return readProfile(
    await sendWithCsrf("/auth/me/photo", {
      method: "PUT",
      body,
      signal: AbortSignal.timeout(UPLOAD_TIMEOUT_MS),
    }),
  );
};

export const removeProfilePhoto = async (): Promise<StudentProfile> =>
  readProfile(await sendWithCsrf("/auth/me/photo", { method: "DELETE" }));

export const changePassword = async (
  currentPassword: string,
  newPassword: string,
): Promise<void> => {
  await postJson("/auth/change-password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
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
