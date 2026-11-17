import type { ReactNode } from "react";
import { ThemeSwitcherContainer } from "../containers/ThemeSwitcherContainer";
import { UserMenuContainer } from "../containers/UserMenuContainer";
import { BrandLink } from "./BrandLink";

interface PageHeaderProps {
  // Optional main navigation, shown between the logo and the actions.
  children?: ReactNode;
}

export function PageHeader({ children }: PageHeaderProps) {
  return (
    <header className="app-header">
      <BrandLink />

      {children}

      <div className="app-header__actions">
        <ThemeSwitcherContainer />
        <UserMenuContainer />
      </div>
    </header>
  );
}
