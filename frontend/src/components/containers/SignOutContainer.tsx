import { Navigate, useNavigate } from "react-router-dom";
import { useAppStore } from "../../store/useAppStore";
import { SignOutPanel } from "../presentational/SignOutPanel";

export function SignOutContainer() {
  const navigate = useNavigate();
  const student = useAppStore((state) => state.student);
  const isSigningOut = useAppStore((state) => state.isSigningOut);
  const isSignedOut = useAppStore((state) => state.isSignedOut);
  const error = useAppStore((state) => state.error);
  const signOut = useAppStore((state) => state.signOut);
  const isAuthChecked = useAppStore((state) => state.isAuthChecked);

  if (!isAuthChecked) {
    return <p className="state-message">Loading...</p>;
  }

  // Nobody to sign out, for example after reloading this page once signed out.
  if (!student && !isSignedOut) {
    return <Navigate to="/sign-in" replace />;
  }

  return (
    <SignOutPanel
      studentName={student?.name ?? null}
      isSigningOut={isSigningOut}
      isSignedOut={isSignedOut}
      error={error}
      onConfirm={() => void signOut()}
      onCancel={() => navigate("/")}
      onSignIn={() => navigate("/sign-in")}
      onRegister={() => navigate("/register")}
    />
  );
}
