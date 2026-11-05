import { Link } from "react-router-dom";

const icons = {
  home: (
    <>
      <path d="M3 11.5 12 4l9 7.5" />
      <path d="M5.5 10v9.5h13V10" />
      <path d="M10 19.5V14h4v5.5" />
    </>
  ),
  account: (
    <>
      <circle cx="12" cy="8" r="4" />
      <path d="M4.5 20.5a7.5 7.5 0 0 1 15 0" />
    </>
  ),
  signOut: (
    <>
      <path d="M10 4H5.5v16H10" />
      <path d="M10 12h10.5" />
      <path d="m16.5 8 4 4-4 4" />
    </>
  ),
};

interface IconLinkProps {
  to: string;
  icon: keyof typeof icons;
  label: string;
  isDanger?: boolean;
}

export function IconLink({ to, icon, label, isDanger = false }: IconLinkProps) {
  return (
    <Link
      className={isDanger ? "icon-link icon-link--danger" : "icon-link"}
      to={to}
    >
      <svg
        className="icon-link__icon"
        viewBox="0 0 24 24"
        width="18"
        height="18"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        {icons[icon]}
      </svg>
      {label}
    </Link>
  );
}
