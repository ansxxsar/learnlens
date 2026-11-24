import type { ReactNode } from "react";
import type { RubricCriterion } from "../../types";
import { formatPoints } from "../../utils/rubric";

interface RubricListProps {
  criteria: RubricCriterion[];
  emptyMessage: string;
  // Instructors only: edit and delete buttons for one criterion.
  renderActions?: (criterion: RubricCriterion) => ReactNode;
}

export function RubricList({
  criteria,
  emptyMessage,
  renderActions,
}: RubricListProps) {
  if (criteria.length === 0) {
    return <p className="state-message">{emptyMessage}</p>;
  }

  const total = criteria.reduce((sum, item) => sum + item.maxPoints, 0);

  return (
    <>
      <ul className="detail-list">
        {criteria.map((criterion) => (
          <li key={criterion.id} className="detail-list__item">
            <div className="detail-list__header">
              <strong>{criterion.title}</strong>
              <span className="detail-list__points">
                {formatPoints(criterion.maxPoints)}
              </span>
            </div>
            {criterion.description && (
              <p className="detail-list__text">{criterion.description}</p>
            )}
            {renderActions?.(criterion)}
          </li>
        ))}
      </ul>
      <p className="detail-list__total">Total: {formatPoints(total)}</p>
    </>
  );
}
