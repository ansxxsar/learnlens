import { useEffect, useId, useRef, useState } from "react";
import { Link } from "react-router-dom";
import type { StudentProfile, StudentProgress } from "../../types";
import { Avatar } from "./Avatar";

interface UserMenuProps {
  student: StudentProfile;
  progress: StudentProgress | null;
}

export function UserMenu({ student, progress }: UserMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuId = useId();

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
          <span>{student.course}</span>
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
            </div>
          </div>

          <dl className="user-menu__stats">
            <div>
              <dt>Course</dt>
              <dd>{student.course}</dd>
            </div>
            {progress && (
              <div>
                <dt>Level</dt>
                <dd>
                  {progress.level} · {progress.xp} XP
                </dd>
              </div>
            )}
            <div>
              <dt>Streak</dt>
              <dd>{student.streakDays} days</dd>
            </div>
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
            <a
              className="user-menu__item"
              href="#progress"
              role="menuitem"
              onClick={closeMenu}
            >
              View progress
            </a>
            <a
              className="user-menu__item"
              href="#assignments"
              role="menuitem"
              onClick={closeMenu}
            >
              My assignments
            </a>
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
