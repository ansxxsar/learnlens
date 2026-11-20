import type {
  ApiAssignment,
  ApiPublicTestCase,
  ApiRubricCriterion,
  ApiTestCase,
  AssignmentTestCase,
  PublicTestCase,
  RubricCriterion,
  RubricCriterionInput,
  TestCaseInput,
  ApiDailyProgress,
  ApiSubmission,
  ApiCourse,
  ApiUser,
  AssignmentInput,
  CourseAssignment,
  CourseAssignmentStatus,
  DailyProgress,
  MyCourse,
  ProgrammingLanguage,
  StudentProfile,
  Submission,
} from "../types";

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
});

const toMyCourse = (course: ApiCourse): MyCourse => ({
  id: course.id,
  code: course.code,
  title: course.title,
  term: course.term,
  role: course.role,
  sectionCode: course.section_code,
  instructorNames: course.instructor_names,
  studentCount: course.student_count,
});

export const fetchMyCourses = async (): Promise<MyCourse[]> => {
  const response = await sendRequest("/courses");
  return ((await response.json()) as ApiCourse[]).map(toMyCourse);
};

export const fetchCourse = async (courseId: number): Promise<MyCourse> => {
  const response = await sendRequest(`/courses/${courseId}`);
  return toMyCourse((await response.json()) as ApiCourse);
};

const toCourseAssignment = (assignment: ApiAssignment): CourseAssignment => ({
  id: assignment.id,
  title: assignment.title,
  instructions: assignment.instructions,
  status: assignment.status,
  feedbackDepth: assignment.feedback_depth,
  dueAt: assignment.due_at,
  publishedAt: assignment.published_at,
  attemptCount: assignment.attempt_count,
});

const readAssignment = async (response: Response): Promise<CourseAssignment> =>
  toCourseAssignment((await response.json()) as ApiAssignment);

const assignmentsPath = (courseId: number, assignmentId?: number): string =>
  assignmentId === undefined
    ? `/courses/${courseId}/assignments`
    : `/courses/${courseId}/assignments/${assignmentId}`;

const toAssignmentBody = (input: Partial<AssignmentInput>) => ({
  title: input.title,
  instructions: input.instructions,
  due_at: input.dueAt,
  feedback_depth: input.feedbackDepth,
});

export const fetchCourseAssignments = async (
  courseId: number,
): Promise<CourseAssignment[]> => {
  const response = await sendRequest(assignmentsPath(courseId));
  return ((await response.json()) as ApiAssignment[]).map(toCourseAssignment);
};

export const createAssignment = async (
  courseId: number,
  input: AssignmentInput,
  publish: boolean,
): Promise<CourseAssignment> =>
  readAssignment(
    await postJson(assignmentsPath(courseId), {
      ...toAssignmentBody(input),
      publish,
    }),
  );

export const updateAssignment = async (
  courseId: number,
  assignmentId: number,
  changes: Partial<AssignmentInput> & { status?: CourseAssignmentStatus },
): Promise<CourseAssignment> =>
  readAssignment(
    await sendJson(assignmentsPath(courseId, assignmentId), "PATCH", {
      ...toAssignmentBody(changes),
      status: changes.status,
    }),
  );

export const deleteAssignment = async (
  courseId: number,
  assignmentId: number,
): Promise<void> => {
  await sendWithCsrf(assignmentsPath(courseId, assignmentId), {
    method: "DELETE",
  });
};

// Rubric criteria and test cases. Only instructors may change them; the API
// gives students the rubric and the public tests only.

const toRubricCriterion = (
  criterion: ApiRubricCriterion,
): RubricCriterion => ({
  id: criterion.id,
  title: criterion.title,
  description: criterion.description,
  maxPoints: criterion.max_points,
  position: criterion.position,
});

const toCriterionBody = (input: Partial<RubricCriterionInput>) => ({
  title: input.title,
  description: input.description,
  max_points: input.maxPoints,
});

const rubricPath = (
  courseId: number,
  assignmentId: number,
  criterionId?: number,
): string =>
  `${assignmentsPath(courseId, assignmentId)}/rubric` +
  (criterionId === undefined ? "" : `/${criterionId}`);

export const fetchRubric = async (
  courseId: number,
  assignmentId: number,
): Promise<RubricCriterion[]> => {
  const response = await sendRequest(rubricPath(courseId, assignmentId));
  return ((await response.json()) as ApiRubricCriterion[]).map(
    toRubricCriterion,
  );
};

export const createCriterion = async (
  courseId: number,
  assignmentId: number,
  input: RubricCriterionInput,
): Promise<RubricCriterion> => {
  const response = await postJson(
    rubricPath(courseId, assignmentId),
    toCriterionBody(input),
  );
  return toRubricCriterion((await response.json()) as ApiRubricCriterion);
};

export const updateCriterion = async (
  courseId: number,
  assignmentId: number,
  criterionId: number,
  input: RubricCriterionInput,
): Promise<RubricCriterion> => {
  const response = await sendJson(
    rubricPath(courseId, assignmentId, criterionId),
    "PATCH",
    toCriterionBody(input),
  );
  return toRubricCriterion((await response.json()) as ApiRubricCriterion);
};

export const deleteCriterion = async (
  courseId: number,
  assignmentId: number,
  criterionId: number,
): Promise<void> => {
  await sendWithCsrf(rubricPath(courseId, assignmentId, criterionId), {
    method: "DELETE",
  });
};

const toPublicTestCase = (test: ApiPublicTestCase): PublicTestCase => ({
  id: test.id,
  name: test.name,
  stdinInput: test.stdin_input,
  expectedOutput: test.expected_output,
});

const toTestCase = (test: ApiTestCase): AssignmentTestCase => ({
  ...toPublicTestCase(test),
  visibility: test.visibility,
  weight: test.weight,
  timeLimitMs: test.time_limit_ms,
  criterionId: test.criterion,
});

const toTestCaseBody = (input: TestCaseInput) => ({
  name: input.name,
  visibility: input.visibility,
  stdin_input: input.stdinInput,
  expected_output: input.expectedOutput,
  weight: input.weight,
  time_limit_ms: input.timeLimitMs,
  criterion: input.criterionId,
});

const testsPath = (
  courseId: number,
  assignmentId: number,
  testId?: number,
): string =>
  `${assignmentsPath(courseId, assignmentId)}/tests` +
  (testId === undefined ? "" : `/${testId}`);

// Instructors: every test of the assignment, hidden ones included.
export const fetchTestCases = async (
  courseId: number,
  assignmentId: number,
): Promise<AssignmentTestCase[]> => {
  const response = await sendRequest(testsPath(courseId, assignmentId));
  return ((await response.json()) as ApiTestCase[]).map(toTestCase);
};

// Students: the server already left out hidden tests.
export const fetchPublicTestCases = async (
  courseId: number,
  assignmentId: number,
): Promise<PublicTestCase[]> => {
  const response = await sendRequest(testsPath(courseId, assignmentId));
  return ((await response.json()) as ApiPublicTestCase[]).map(
    toPublicTestCase,
  );
};

export const createTestCase = async (
  courseId: number,
  assignmentId: number,
  input: TestCaseInput,
): Promise<AssignmentTestCase> => {
  const response = await postJson(
    testsPath(courseId, assignmentId),
    toTestCaseBody(input),
  );
  return toTestCase((await response.json()) as ApiTestCase);
};

export const updateTestCase = async (
  courseId: number,
  assignmentId: number,
  testId: number,
  input: TestCaseInput,
): Promise<AssignmentTestCase> => {
  const response = await sendJson(
    testsPath(courseId, assignmentId, testId),
    "PATCH",
    toTestCaseBody(input),
  );
  return toTestCase((await response.json()) as ApiTestCase);
};

export const deleteTestCase = async (
  courseId: number,
  assignmentId: number,
  testId: number,
): Promise<void> => {
  await sendWithCsrf(testsPath(courseId, assignmentId, testId), {
    method: "DELETE",
  });
};

export const fetchProgress = async (): Promise<DailyProgress> => {
  const response = await sendRequest("/progress");
  const progress = (await response.json()) as ApiDailyProgress;
  return {
    today: progress.today,
    streakDays: progress.streak_days,
    practicedToday: progress.practiced_today,
    week: progress.week,
    tasks: progress.tasks.map((task) => ({
      assignmentId: task.assignment_id,
      courseId: task.course_id,
      courseCode: task.course_code,
      title: task.title,
      dueAt: task.due_at,
      isDone: task.is_done,
      isOverdue: task.is_overdue,
    })),
    completedTasks: progress.completed_tasks,
    totalTasks: progress.total_tasks,
  };
};

const toSubmission = (submission: ApiSubmission): Submission => ({
  id: submission.id,
  attemptNumber: submission.attempt_number,
  status: submission.status,
  submittedAt: submission.submitted_at,
  language: submission.language,
  code: submission.code,
});

export const fetchMyAttempts = async (
  courseId: number,
  assignmentId: number,
): Promise<Submission[]> => {
  const response = await sendRequest(
    `${assignmentsPath(courseId, assignmentId)}/submissions`,
  );
  return ((await response.json()) as ApiSubmission[]).map(toSubmission);
};

// Only stores the attempt. The code is never run in the browser or the API.
export const submitAttempt = async (
  courseId: number,
  assignmentId: number,
  language: ProgrammingLanguage,
  code: string,
): Promise<Submission> => {
  const response = await postJson(
    `${assignmentsPath(courseId, assignmentId)}/submissions`,
    { language, code },
  );
  return toSubmission((await response.json()) as ApiSubmission);
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
