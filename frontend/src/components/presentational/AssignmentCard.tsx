import type { Assignment } from "../../types";

interface AssignmentCardProps {
  assignment: Assignment;
  isSelected: boolean;
  onSelect: (assignmentId: number) => void;
}

export function AssignmentCard({
  assignment,
  isSelected,
  onSelect,
}: AssignmentCardProps) {
  return (
    <button
      className={`assignment-card ${isSelected ? "assignment-card--selected" : ""}`}
      onClick={() => onSelect(assignment.id)}
      type="button"
    >
      <div className="assignment-card__header">
        <span className="assignment-card__topic">{assignment.topic}</span>
        <span className={`status status--${assignment.status}`}>
          {assignment.status.replace("-", " ")}
        </span>
      </div>

      <h3>{assignment.title}</h3>
      <p>{assignment.description}</p>

      <div className="assignment-card__footer">
        <span>{assignment.difficulty}</span>
        <strong>+{assignment.xp} XP</strong>
      </div>
    </button>
  );
}
