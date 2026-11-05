interface AvatarProps {
  className: string;
  initials: string;
  photoUrl: string | null;
}

// Decorative: the person's name is always written next to it.
export function Avatar({ className, initials, photoUrl }: AvatarProps) {
  return (
    <span className={className} aria-hidden="true">
      {photoUrl ? <img src={photoUrl} alt="" /> : initials}
    </span>
  );
}
