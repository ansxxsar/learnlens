import type { ReactNode } from "react";
import type { CourseAssignment } from "../../types";
import type { StatusAction } from "../../utils/assignments";
import {
  formatDueDate,
  statusActions,
  statusLabels,
} from "../../utils/assignments";

interface CourseAssignmentItemProps {
  assignment: CourseAssignment;
  canManage: boolean;
  isBusy: boolean;
  onEdit: () => void;
  onAction: (action: StatusAction) => void;
  // Students only: whether the submission form is open, and opening it.
  isSubmitting?: boolean;
  onStartSubmission?: () => void;
  // The submission form, shown under the instructions while open.
  children?: ReactNode;
  // The rubric and tests panel, and whether it is open.
  details?: ReactNode;
  isDetailsOpen: boolean;
  onToggleDetails: () => void;
}

const attemptsLabel = (count: number): string =>
  count === 1 ? "1 attempt" : `${count} attempts`;

export function CourseAssignmentItem({
  assignment,
  canManage,
  isBusy,
  onEdit,
  onAction,
  isSubmitting = false,
  onStartSubmission,
  children,
  details,
  isDetailsOpen,
  onToggleDetails,
}: CourseAssignmentItemProps) {
  const attemptCount = assignment.attemptCount ?? 0;
  const canSubmit = !canManage && assignment.status === "published";
  // Students only see published and closed work, so only "Closed" needs a badge.
  const showStatus = canManage || assignment.status === "closed";

  const detailsButton = (
    <button
      className="secondary-button"
      type="button"
      aria-expanded={isDetailsOpen}
      onClick={onToggleDetails}
    >
      {isDetailsOpen
        ? "Hide rubric"
        : canManage
          ? "Rubric & tests"
          : "Rubric & examples"}
    </button>
  );

  return (
    <article className="course-assignment">
      <div className="course-assignment__header">
        <h3>{assignment.title}</h3>
        {!canManage && attemptCount > 0 && (
          <span className="status course-assignment__status--published course-assignment__done">
            Done · {attemptsLabel(attemptCount)}
          </span>
        )}
        {showStatus && (
          <span
            className={`status course-assignment__status--${assignment.status}`}
          >
            {statusLabels[assignment.status]}
          </span>
        )}
      </div>

      <p className="course-assignment__due">
        Due {formatDueDate(assignment.dueAt)}
      </p>
      <p className="course-assignment__instructions">
        {assignment.instructions}
      </p>

      {details}

      {children}

      {!canManage && (
        <div className="course-assignment__actions">
          {canSubmit && !isSubmitting && (
            <button
              className="primary-button"
              type="button"
              onClick={onStartSubmission}
            >
              {attemptCount > 0 ? "Submit again" : "Submit solution"}
            </button>
          )}
          {detailsButton}
        </div>
      )}

      {canManage && assignment.status === "archived" && (
        <div className="course-assignment__actions">{detailsButton}</div>
      )}

      {canManage && assignment.status !== "archived" && (
        <div className="course-assignment__actions">
          {detailsButton}
          <button
            className="secondary-button"
            type="button"
            disabled={isBusy}
            onClick={onEdit}
          >
            Edit
          </button>
          {statusActions[assignment.status].map((action) => (
            <button
              key={action.label}
              className={`secondary-button ${action.isDanger ? "secondary-button--danger" : ""}`}
              type="button"
              disabled={isBusy}
              onClick={() => onAction(action)}
            >
              {action.label}
            </button>
          ))}
        </div>
      )}
    </article>
  );
}
