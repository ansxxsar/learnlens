import type { ReactNode } from "react";
import { Link } from "react-router-dom";

interface AuthLayoutProps {
  children: ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="app">
      <header className="app-header">
        <Link className="brand" to="/" aria-label="LearnLens home">
          <span className="brand__icon">L</span>
          <span>LearnLens</span>
        </Link>
      </header>

      <main className="auth-page">{children}</main>
    </div>
  );
}
