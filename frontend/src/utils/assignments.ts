import type { CourseAssignmentStatus, FeedbackDepth } from "../types";

export interface StatusAction {
  label: string;
  // null deletes the assignment instead of changing its status.
  status: CourseAssignmentStatus | null;
  isDanger?: boolean;
}

// Mirrors ALLOWED_TRANSITIONS in backend/courses/services.py. The server still
// checks every change; this only decides which buttons to show.
export const statusActions: Record<CourseAssignmentStatus, StatusAction[]> = {
  draft: [
    { label: "Publish", status: "published" },
    { label: "Delete", status: null, isDanger: true },
  ],
  published: [
    { label: "Close", status: "closed" },
    { label: "Archive", status: "archived", isDanger: true },
  ],
  closed: [
    { label: "Reopen", status: "published" },
    { label: "Archive", status: "archived", isDanger: true },
  ],
  archived: [],
};

export const statusLabels: Record<CourseAssignmentStatus, string> = {
  draft: "Draft",
  published: "Published",
  closed: "Closed",
  archived: "Archived",
};

export const feedbackDepthOptions: { id: FeedbackDepth; label: string }[] = [
  { id: "hint", label: "Hint: a short nudge" },
  { id: "guided", label: "Guided: explain the issue and the next step" },
  { id: "detailed", label: "Detailed: a full explanation" },
];

// The interface is in English, so dates are too, whatever the browser language.
const dateFormatter = new Intl.DateTimeFormat("en-GB", {
  dateStyle: "medium",
  timeStyle: "short",
});

export const formatDueDate = (iso: string): string =>
  dateFormatter.format(new Date(iso));

// <input type="datetime-local"> works in local time without a time zone.
export const toLocalInputValue = (iso: string): string => {
  const date = new Date(iso);
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
};

export const fromLocalInputValue = (value: string): string =>
  new Date(value).toISOString();
