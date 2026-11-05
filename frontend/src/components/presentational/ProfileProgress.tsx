import type { CSSProperties } from "react";
import type { StudentProfile } from "../../types";

interface ProfileProgressProps {
  student: StudentProfile;
}

export function ProfileProgress({ student }: ProfileProgressProps) {
  const items = [
    { label: "Create your account", done: true },
    { label: "Add a photo", done: student.photoUrl !== null },
    { label: "Pick a favorite language", done: student.preferredLanguage !== null },
    { label: "Join a course", done: student.courses.length > 0 },
  ];
  const doneCount = items.filter((item) => item.done).length;
  const percent = Math.round((doneCount / items.length) * 100);
  const nextItem = items.find((item) => !item.done);

  return (
    <section className="account-card">
      <h2>Your profile</h2>
      <div className="profile-progress">
        <div
          className="profile-progress__ring"
          style={{ "--progress": percent } as CSSProperties}
          aria-hidden="true"
        >
          <span>{percent}%</span>
        </div>
        <p className="profile-progress__headline">
          {nextItem
            ? `Next step: ${nextItem.label.toLowerCase()}.`
            : "Your profile is complete. Nice work!"}
        </p>
      </div>
      <ul className="profile-progress__list">
        {items.map((item) => (
          <li
            key={item.label}
            className={
              item.done
                ? "profile-progress__item profile-progress__item--done"
                : "profile-progress__item"
            }
          >
            <span className="profile-progress__check" aria-hidden="true">
              {item.done ? "✓" : ""}
            </span>
            <span>
              {item.label}
              <span className="visually-hidden">
                {item.done ? ": done" : ": not done yet"}
              </span>
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
