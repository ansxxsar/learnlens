import { Navigate, Outlet } from "react-router-dom";
import { useAppStore } from "../../store/useAppStore";

// These only choose which page to show. The API enforces access on every request.
export function RequireAuth() {
  const student = useAppStore((state) => state.student);
  const isAuthChecked = useAppStore((state) => state.isAuthChecked);

  if (!isAuthChecked) {
    return <p className="state-message">Loading...</p>;
  }

  return student ? <Outlet /> : <Navigate to="/sign-in" replace />;
}

export function GuestOnly() {
  const student = useAppStore((state) => state.student);
  const isAuthChecked = useAppStore((state) => state.isAuthChecked);

  if (!isAuthChecked) {
    return <p className="state-message">Loading...</p>;
  }

  return student ? <Navigate to="/" replace /> : <Outlet />;
}
