import { mockAssignments, mockProgress } from "../data/mockData";
import type { Assignment, StudentProgress, SubmissionResult } from "../types";

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

interface CodeCheck {
  passed: boolean;
  success: string;
  improvement: string;
}

const evaluateAssignment = (
  assignmentId: number,
  code: string,
): CodeCheck[] => {
  const normalizedCode = code.toLowerCase();

  if (assignmentId === 1) {
    return [
      {
        passed: /[a-z_]\w*\s*=(?!=)/i.test(code),
        success: "You created and assigned a variable.",
        improvement:
          "Create at least one variable using the assignment operator.",
      },
      {
        passed: /\b(int|float|str|bool)\s*\(/.test(normalizedCode),
        success: "You used explicit type conversion.",
        improvement:
          "Use int(), float(), str(), or bool() for type conversion.",
      },
      {
        passed: /\bprint\s*\(/.test(normalizedCode),
        success: "You displayed the result.",
        improvement: "Use print() to display the converted value.",
      },
      {
        passed: /#/.test(code),
        success: "You documented part of your solution.",
        improvement: "Add a short comment explaining the conversion.",
      },
    ];
  }

  if (assignmentId === 2) {
    return [
      {
        passed: /\bif\b/.test(normalizedCode),
        success: "You used an if statement.",
        improvement: "Add an if statement for the main condition.",
      },
      {
        passed: /\b(elif|else)\b/.test(normalizedCode),
        success: "You handled an alternative condition.",
        improvement: "Handle another case using elif or else.",
      },
      {
        passed: /(==|!=|>=|<=|>|<)/.test(code),
        success: "You used a comparison operator.",
        improvement: "Compare the score with an appropriate boundary value.",
      },
      {
        passed: /\b(print|return)\s*\(/.test(normalizedCode),
        success: "Your solution produces an output.",
        improvement: "Return or print the calculated grade.",
      },
    ];
  }

  return [
    {
      passed: /\bdef\s+[a-z_]\w*\s*\(/i.test(code),
      success: "You defined a function.",
      improvement: "Define a function using the def keyword.",
    },
    {
      passed: /\bdef\s+[a-z_]\w*\s*\([^)]*[a-z_]\w*[^)]*\)/i.test(code),
      success: "Your function accepts a parameter.",
      improvement: "Add at least one parameter to the function.",
    },
    {
      passed: /\breturn\b/.test(normalizedCode),
      success: "Your function returns a value.",
      improvement: "Use return to send a result back from the function.",
    },
    {
      passed: /\b[a-z_]\w*\s*\([^)]*\)/i.test(
        code.replace(/\bdef\s+[a-z_]\w*\s*\([^)]*\)/i, ""),
      ),
      success: "You called the function.",
      improvement: "Call the function with a sample argument.",
    },
  ];
};

export const submitPythonCode = async (
  assignmentId: number,
  code: string,
): Promise<SubmissionResult> => {
  await delay(900);

  if (code.trim().length === 0) {
    throw new Error("Please enter your Python solution.");
  }

  const checks = evaluateAssignment(assignmentId, code);
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
