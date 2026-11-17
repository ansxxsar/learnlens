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
}

export function CourseAssignmentItem({
  assignment,
  canManage,
  isBusy,
  onEdit,
  onAction,
}: CourseAssignmentItemProps) {
  // Students only see published and closed work, so only "Closed" needs a badge.
  const showStatus = canManage || assignment.status === "closed";

  return (
    <article className="course-assignment">
      <div className="course-assignment__header">
        <h3>{assignment.title}</h3>
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

      {canManage && assignment.status !== "archived" && (
        <div className="course-assignment__actions">
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
