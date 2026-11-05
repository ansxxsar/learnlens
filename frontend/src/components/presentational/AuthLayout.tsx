import type { ReactNode } from "react";
import { ThemeSwitcherContainer } from "../containers/ThemeSwitcherContainer";
import { BrandLink } from "./BrandLink";

interface AuthLayoutProps {
  children: ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="app">
      <header className="app-header">
        <BrandLink />

        <ThemeSwitcherContainer />
      </header>

      <main className="auth-page">{children}</main>
    </div>
  );
}
