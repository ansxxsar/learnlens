import { Link } from "react-router-dom";
import type { DailyProgress } from "../../types";
import { formatDueDate } from "../../utils/assignments";

interface DailyProgressPanelProps {
  progress: DailyProgress;
}

// Shown in full; the rest are counted so the panel stays short.
const MAX_PENDING_SHOWN = 5;

const weekdayFormatter = new Intl.DateTimeFormat("en-GB", {
  weekday: "short",
  timeZone: "UTC",
});
const fullDateFormatter = new Intl.DateTimeFormat("en-GB", {
  weekday: "long",
  day: "numeric",
  month: "long",
  timeZone: "UTC",
});

// The API sends calendar days ("2026-11-17") already cut in SDU's time zone.
// Reading them as UTC keeps the browser's own zone from shifting the day.
const parseDay = (day: string): Date => new Date(`${day}T00:00:00Z`);

const daysLabel = (count: number): string =>
  count === 1 ? "1 day" : `${count} days`;

const todayMessage = (progress: DailyProgress): string => {
  if (progress.practicedToday) {
    return "You practiced today. Nice work, see you tomorrow!";
  }
  if (progress.streakDays > 0) {
    return `You haven't practiced today yet. Submit a task to keep your ${daysLabel(progress.streakDays)} streak.`;
  }
  return "You haven't practiced today yet. Submit a task to start a streak.";
};

export function DailyProgressPanel({ progress }: DailyProgressPanelProps) {
  const pending = progress.tasks.filter((task) => !task.isDone);
  const shown = pending.slice(0, MAX_PENDING_SHOWN);
  const percent =
    progress.totalTasks === 0
      ? 0
      : Math.round((progress.completedTasks / progress.totalTasks) * 100);

  return (
    <section
      className="daily-progress"
      id="progress"
      aria-labelledby="daily-progress-title"
    >
      <div>
        <span className="eyebrow">Your progress</span>
        <h2 id="daily-progress-title">
          Today, {fullDateFormatter.format(parseDay(progress.today))}
        </h2>
      </div>

      <p
        className={`daily-progress__message ${progress.practicedToday ? "daily-progress__message--done" : ""}`}
        role="status"
      >
        {todayMessage(progress)}
      </p>

      <ol
        className="daily-progress__week"
        aria-label="Practice in the last 7 days"
      >
        {progress.week.map((day) => {
          const isToday = day.date === progress.today;
          const practiced = day.submissions > 0;
          return (
            <li
              key={day.date}
              className={[
                "daily-progress__day",
                practiced && "daily-progress__day--done",
                isToday && "daily-progress__day--today",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              <span>{weekdayFormatter.format(parseDay(day.date))}</span>
              <span className="daily-progress__dot" aria-hidden="true">
                {practiced ? "✓" : ""}
              </span>
              <span className="visually-hidden">
                {practiced ? `${day.submissions} submitted` : "no practice"}
              </span>
            </li>
          );
        })}
      </ol>

      <div className="daily-progress__tasks">
        <div className="daily-progress__tasks-header">
          <h3>Tasks</h3>
          <span>
            {progress.completedTasks} of {progress.totalTasks} done
          </span>
        </div>

        <div
          className="progress-bar"
          role="progressbar"
          aria-label="Tasks done"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={percent}
        >
          <div
            className="progress-bar__value"
            style={{ width: `${percent}%` }}
          />
        </div>

        {progress.totalTasks === 0 ? (
          <p className="daily-progress__empty">
            No open tasks right now. New assignments from your teachers will
            show up here.
          </p>
        ) : pending.length === 0 ? (
          <p className="daily-progress__empty">
            All open tasks are done. Great job!
          </p>
        ) : (
          <ul className="daily-progress__list">
            {shown.map((task) => (
              <li key={task.assignmentId}>
                <Link
                  className="daily-progress__task"
                  to={`/course/${task.courseId}`}
                >
                  <span className="daily-progress__task-title">
                    {task.title}
                  </span>
                  <span
                    className={`daily-progress__task-due ${task.isOverdue ? "daily-progress__task-due--overdue" : ""}`}
                  >
                    {task.courseCode} ·{" "}
                    {task.isOverdue ? "Overdue since" : "Due"}{" "}
                    {formatDueDate(task.dueAt)}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}

        {pending.length > shown.length && (
          <p className="daily-progress__more">
            +{pending.length - shown.length} more in your courses
          </p>
        )}
      </div>
    </section>
  );
}
