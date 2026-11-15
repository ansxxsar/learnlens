import { useState } from "react";
import { useSubmitStatus } from "../../hooks/useSubmitStatus";
import { changePassword } from "../../services/api";
import { useAppStore } from "../../store/useAppStore";
import { IconLink } from "../presentational/IconLink";
import { LearnerCard } from "../presentational/LearnerCard";
import { PasswordForm } from "../presentational/PasswordForm";
import { PhotoPicker } from "../presentational/PhotoPicker";
import { ProfileForm } from "../presentational/ProfileForm";
import { ProfileProgress } from "../presentational/ProfileProgress";

const currentGreeting = (): string => {
  const hour = new Date().getHours();
  if (hour < 12) {
    return "Good morning";
  }
  return hour < 18 ? "Good afternoon" : "Good evening";
};

export function AccountContainer() {
  const student = useAppStore((state) => state.student);
  const updateProfile = useAppStore((state) => state.updateProfile);
  const uploadPhoto = useAppStore((state) => state.uploadPhoto);
  const removePhoto = useAppStore((state) => state.removePhoto);
  const profile = useSubmitStatus();
  const photo = useSubmitStatus();
  const password = useSubmitStatus();
  const [greeting] = useState(currentGreeting);

  // The route only renders this for signed-in users.
  if (!student) {
    return null;
  }

  return (
    <div className="account">
      <div className="account__top">
        <div>
          <span className="eyebrow">My account</span>
          <h1>
            {greeting}, {student.name.split(" ")[0]}
          </h1>
        </div>
        <IconLink to="/" icon="home" label="Back to home" />
      </div>

      <div className="account__grid">
        <div className="account__column">
          <LearnerCard student={student} />
          <PhotoPicker
            hasPhoto={student.photoUrl !== null}
            status={photo.status}
            onChoose={(file) => void photo.run(() => uploadPhoto(file))}
            onRemove={() => void photo.run(removePhoto)}
          />
          <ProfileProgress student={student} />
        </div>

        <div className="account__column">
          <ProfileForm
            student={student}
            status={profile.status}
            onSave={(changes) =>
              void profile.run(() => updateProfile(changes))
            }
          />

          <section className="account-card">
            <h2>My courses</h2>
            {student.courses.length > 0 ? (
              <ul className="account-courses">
                {student.courses.map((course) => (
                  <li key={course.id}>
                    <strong>{course.title}</strong>
                    <span>
                      {course.code} · {course.role}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="account-card__note">
                You aren't in a course yet. Once you are enrolled, it will appear
                here.
              </p>
            )}
          </section>

          <PasswordForm
            status={password.status}
            onSave={(currentPassword, newPassword) =>
              password.run(() => changePassword(currentPassword, newPassword))
            }
          />
        </div>
      </div>

      <div className="account__footer">
        <IconLink to="/sign-out" icon="signOut" label="Sign out" isDanger />
      </div>
    </div>
  );
}
