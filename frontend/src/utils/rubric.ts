import type { TestCaseInput } from "../types";

// Points arrive as numbers with up to two decimals, e.g. 2.5.
export const formatPoints = (points: number): string =>
  `${Number(points.toFixed(2))} ${points === 1 ? "pt" : "pts"}`;

// Mirrors the limits in backend/courses/serializers.py; the server still
// checks every value.
export const POINTS_MIN = 0.01;
export const POINTS_MAX = 1000;
export const TIME_LIMIT_MIN_MS = 100;
export const TIME_LIMIT_MAX_MS = 10_000;
export const TEST_IO_MAX_LENGTH = 20_000;

// Matches the model defaults. New tests are hidden, so nothing is shown to
// students until the instructor chooses to.
export const newTestCase: TestCaseInput = {
  name: "",
  visibility: "hidden",
  stdinInput: "",
  expectedOutput: "",
  weight: 1,
  timeLimitMs: 2000,
  criterionId: null,
};
