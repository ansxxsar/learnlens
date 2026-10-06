import type { StudentProgress } from "../../types";

interface ProgressPanelProps {
  progress: StudentProgress;
}

export function ProgressPanel({ progress }: ProgressPanelProps) {
  const progressPercentage = Math.round(
    (progress.xp / progress.nextLevelXp) * 100,
  );

  return (
    <section className="progress-panel">
      <div>
        <span className="eyebrow">Your progress</span>
        <h2>Level {progress.level}</h2>
      </div>

      <div className="progress-panel__numbers">
        <strong>
          {progress.xp}/{progress.nextLevelXp} XP
        </strong>
        <span>
          {progress.completedAssignments}/{progress.totalAssignments} completed
        </span>
      </div>

      <div
        className="progress-bar"
        aria-label={`${progressPercentage}% progress to the next level`}
      >
        <div
          className="progress-bar__value"
          style={{ width: `${progressPercentage}%` }}
        />
      </div>
    </section>
  );
}
