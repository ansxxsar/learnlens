import { useEffect, useId, useRef, useState } from "react";
import { Link } from "react-router-dom";
import type { StudentProfile, StudentProgress } from "../../types";
import { Avatar } from "./Avatar";
import { RoleBadge } from "./RoleBadge";

interface UserMenuProps {
  student: StudentProfile;
  progress: StudentProgress | null;
}

export function UserMenu({ student, progress }: UserMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuId = useId();
  // Streak and progress are student features.
  const isStudent = student.accountType !== "teacher";

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handlePointerDown = (event: PointerEvent) => {
      if (!menuRef.current?.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsOpen(false);
        triggerRef.current?.focus();
      }
    };

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  const closeMenu = () => setIsOpen(false);

  return (
    <div className="user-menu" ref={menuRef}>
      <button
        ref={triggerRef}
        type="button"
        className="student-profile"
        aria-haspopup="menu"
        aria-expanded={isOpen}
        aria-controls={menuId}
        onClick={() => setIsOpen((open) => !open)}
      >
        <div>
          <strong>{student.name}</strong>
          <div className="student-profile__meta">
            <RoleBadge accountType={student.accountType} />
            <span>{student.course}</span>
          </div>
        </div>
        <Avatar
          className="student-profile__avatar"
          initials={student.initials}
          photoUrl={student.photoUrl}
        />
      </button>

      {isOpen && (
        <div className="user-menu__panel" id={menuId} role="menu">
          <div className="user-menu__header">
            <Avatar
              className="student-profile__avatar"
              initials={student.initials}
              photoUrl={student.photoUrl}
            />
            <div>
              <strong>{student.name}</strong>
              <span>{student.email}</span>
              <RoleBadge accountType={student.accountType} />
            </div>
          </div>

          <dl className="user-menu__stats">
            <div>
              <dt>Course</dt>
              <dd>{student.course}</dd>
            </div>
            {isStudent && progress && (
              <div>
                <dt>Level</dt>
                <dd>
                  {progress.level} · {progress.xp} XP
                </dd>
              </div>
            )}
            {isStudent && (
              <div>
                <dt>Streak</dt>
                <dd>{student.streakDays} days</dd>
              </div>
            )}
          </dl>

          <div className="user-menu__actions">
            <Link
              className="user-menu__item"
              to="/account"
              role="menuitem"
              onClick={closeMenu}
            >
              My account
            </Link>
            {/* Assignments live inside courses, so this opens the course list. */}
            <Link
              className="user-menu__item"
              to="/"
              role="menuitem"
              onClick={closeMenu}
            >
              My courses
            </Link>
            <Link
              className="user-menu__item"
              to="/sign-out"
              role="menuitem"
              onClick={closeMenu}
            >
              Sign out
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
