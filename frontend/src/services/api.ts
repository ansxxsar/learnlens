import { mockAssignments, mockProgress, mockStudent } from "../data/mockData";
import type {
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

export const fetchAssignments = async (): Promise<Assignment[]> => {
  await delay(600);
  return mockAssignments;
};

export const fetchProgress = async (): Promise<StudentProgress> => {
  await delay(400);
  return mockProgress;
};

export const fetchStudent = async (): Promise<StudentProfile> => {
  await delay(300);
  return mockStudent;
};

// Mock of the planned POST /auth/sign-out endpoint. The real version must
// invalidate the session on the server; clearing client state is not enough.
export const signOutStudent = async (): Promise<void> => {
  await delay(500);
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
