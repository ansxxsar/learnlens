import type { ChangeEvent } from "react";
import type { SubmitStatus } from "../../hooks/useSubmitStatus";

interface PhotoPickerProps {
  hasPhoto: boolean;
  status: SubmitStatus;
  onChoose: (photo: File) => void;
  onRemove: () => void;
}

export function PhotoPicker({
  hasPhoto,
  status,
  onChoose,
  onRemove,
}: PhotoPickerProps) {
  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const photo = event.target.files?.[0];
    // Lets the same file be chosen again, for example after an error.
    event.target.value = "";
    if (photo) {
      onChoose(photo);
    }
  };
  const fieldError = status.fieldErrors.photo?.join(" ");

  return (
    <section className="account-card">
      <h2>Your photo</h2>
      <div className="auth-form">
        <div className="account-card__row">
          <label
            className={
              status.isSaving
                ? "secondary-button photo-picker__button photo-picker__button--busy"
                : "secondary-button photo-picker__button"
            }
          >
            {status.isSaving
              ? "Working..."
              : hasPhoto
                ? "Change photo"
                : "Upload photo"}
            <input
              className="visually-hidden"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              disabled={status.isSaving}
              onChange={handleChange}
            />
          </label>
          {hasPhoto && (
            <button
              type="button"
              className="secondary-button"
              disabled={status.isSaving}
              onClick={onRemove}
            >
              Remove
            </button>
          )}
        </div>
        <p className="account-card__note">
          JPEG, PNG or WebP, up to 5 MB. We crop it to a square and remove hidden
          details such as location.
        </p>
        {status.error && (
          <p className="error-message" role="alert">
            {fieldError ?? status.error}
          </p>
        )}
      </div>
    </section>
  );
}
