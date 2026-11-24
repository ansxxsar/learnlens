import type { Submission, TestErrorType } from "../types";

export const errorLabels: Record<TestErrorType, string> = {
  wrong_answer: "Wrong output",
  runtime_error: "Crashed",
  time_limit: "Too slow",
  memory_limit: "Used too much memory",
  output_limit: "Printed too much",
  compile_error: "Didn't compile",
};

// While an attempt is in one of these states, the page keeps asking for news.
export const isPending = (attempt: Submission): boolean =>
  attempt.status === "queued" || attempt.status === "running";
