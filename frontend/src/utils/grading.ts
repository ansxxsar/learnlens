import type { GradebookCell } from "../types";

export const formatPoints = (points: number): string =>
  String(Number(points.toFixed(2)));

export type CellState =
  | "graded"
  | "outdated"
  | "running"
  | "suggested"
  | "review";

export const cellState = (cell: GradebookCell): CellState => {
  if (cell.grade) return cell.grade.isOutdated ? "outdated" : "graded";
  if (cell.latest.status === "queued" || cell.latest.status === "running") {
    return "running";
  }
  return cell.needsReview ? "review" : "suggested";
};

export const cellStateLabels: Record<CellState, string> = {
  graded: "Graded",
  outdated: "New attempt",
  running: "Running",
  suggested: "Suggested",
  review: "Needs review",
};
