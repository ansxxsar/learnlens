import { useRef } from "react";
import type { PointerEvent } from "react";
import type { StudentProfile } from "../../types";
import { Avatar } from "./Avatar";

const MAX_TILT_DEGREES = 7;

const roleLabels: Record<StudentProfile["accountType"], string> = {
  student: "Student",
  teacher: "Teacher",
  pending_teacher: "Waiting for approval",
  admin: "Admin",
};

interface LearnerCardProps {
  student: StudentProfile;
}

export function LearnerCard({ student }: LearnerCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const localPart = student.email.split("@")[0];
  const studentNumber = /^[0-9]+$/.test(localPart) ? localPart : null;
  // English like the rest of the site, whatever language the browser uses.
  const memberSince = new Date(student.memberSince).toLocaleDateString(
    "en-US",
    { month: "long", year: "numeric" },
  );

  // The card leans toward the mouse. CSS turns this off for reduced motion.
  const handlePointerMove = (event: PointerEvent<HTMLDivElement>) => {
    const card = cardRef.current;
    if (!card || event.pointerType !== "mouse") {
      return;
    }

    const box = card.getBoundingClientRect();
    const x = (event.clientX - box.left) / box.width;
    const y = (event.clientY - box.top) / box.height;
    card.style.setProperty("--tilt-y", `${(x - 0.5) * 2 * MAX_TILT_DEGREES}deg`);
    card.style.setProperty("--tilt-x", `${(0.5 - y) * 2 * MAX_TILT_DEGREES}deg`);
    card.style.setProperty("--shine-x", `${x * 100}%`);
    card.style.setProperty("--shine-y", `${y * 100}%`);
  };

  const handlePointerLeave = () => {
    const style = cardRef.current?.style;
    for (const name of ["--tilt-x", "--tilt-y", "--shine-x", "--shine-y"]) {
      style?.removeProperty(name);
    }
  };

  return (
    <div
      className="learner-card"
      ref={cardRef}
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
    >
      <div className="learner-card__brand">
        <span>LearnLens</span>
        <span className="learner-card__role">
          {roleLabels[student.accountType]}
        </span>
      </div>

      <div className="learner-card__person">
        <Avatar
          className="learner-card__avatar"
          initials={student.initials}
          photoUrl={student.photoUrl}
        />
        <div>
          <p className="learner-card__name">{student.name}</p>
          <p className="learner-card__email">{student.email}</p>
        </div>
      </div>

      <dl className="learner-card__facts">
        {studentNumber && (
          <div>
            <dt>Student number</dt>
            <dd>{studentNumber}</dd>
          </div>
        )}
        <div>
          <dt>Member since</dt>
          <dd>{memberSince}</dd>
        </div>
      </dl>
    </div>
  );
}
