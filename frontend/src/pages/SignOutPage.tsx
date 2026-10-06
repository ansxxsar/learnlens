import { Link } from "react-router-dom";
import { SignOutContainer } from "../components/containers/SignOutContainer";

export function SignOutPage() {
  return (
    <div className="app">
      <header className="app-header">
        <Link className="brand" to="/" aria-label="LearnLens home">
          <span className="brand__icon">L</span>
          <span>LearnLens</span>
        </Link>
      </header>

      <main className="sign-out-page">
        <SignOutContainer />
      </main>
    </div>
  );
}
