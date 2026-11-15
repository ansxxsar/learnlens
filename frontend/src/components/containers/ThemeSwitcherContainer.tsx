import { useAppStore } from "../../store/useAppStore";
import { ThemeSwitcher } from "../presentational/ThemeSwitcher";

export function ThemeSwitcherContainer() {
  const themePreference = useAppStore((state) => state.themePreference);
  const setThemePreference = useAppStore((state) => state.setThemePreference);

  return (
    <ThemeSwitcher preference={themePreference} onChange={setThemePreference} />
  );
}
