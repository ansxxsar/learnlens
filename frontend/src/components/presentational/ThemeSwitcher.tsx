import type { ReactNode } from "react";
import type { ThemePreference } from "../../types";

interface ThemeSwitcherProps {
  preference: ThemePreference;
  onChange: (preference: ThemePreference) => void;
}

const iconProps = {
  viewBox: "0 0 24 24",
  width: 16,
  height: 16,
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": true,
} as const;

// Listed in click order: each click moves to the next mode.
const modes: {
  value: ThemePreference;
  label: string;
  icon: ReactNode;
}[] = [
  {
    value: "light",
    label: "Light",
    icon: (
      <svg {...iconProps}>
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
      </svg>
    ),
  },
  {
    value: "dark",
    label: "Dark",
    icon: (
      <svg {...iconProps}>
        <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" />
      </svg>
    ),
  },
  {
    value: "system",
    label: "Auto",
    icon: (
      <svg {...iconProps}>
        <rect x="3" y="4" width="18" height="12" rx="2" />
        <path d="M8 20h8M12 16v4" />
      </svg>
    ),
  },
];

export function ThemeSwitcher({ preference, onChange }: ThemeSwitcherProps) {
  const currentIndex = modes.findIndex((mode) => mode.value === preference);
  const current = modes[currentIndex];
  const next = modes[(currentIndex + 1) % modes.length];
  const description = `Color mode: ${current.label}. Switch to ${next.label}.`;

  return (
    <button
      type="button"
      className="theme-switcher"
      aria-label={description}
      title={description}
      onClick={() => onChange(next.value)}
    >
      {current.icon}
      <span className="theme-switcher__label">{current.label}</span>
    </button>
  );
}
