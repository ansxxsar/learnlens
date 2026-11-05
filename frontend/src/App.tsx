import "./App.css";
import { useEffect } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { GuestOnly, RequireAuth } from "./components/containers/AuthGuards";
import { AboutPage } from "./pages/AboutPage";
import { HomePage } from "./pages/HomePage";
import { RegisterPage } from "./pages/RegisterPage";
import { SignInPage } from "./pages/SignInPage";
import { SignOutPage } from "./pages/SignOutPage";
import { useAppStore } from "./store/useAppStore";
import { ABOUT_PATH } from "./utils/aboutNavigation";

function App() {
  const loadSession = useAppStore((state) => state.loadSession);
  const { pathname } = useLocation();

  useEffect(() => {
    void loadSession();
  }, [loadSession]);

  // A new page starts at the top, even after a long page was scrolled down.
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [pathname]);

  return (
    <Routes>
      <Route element={<RequireAuth />}>
        <Route path="/" element={<HomePage />} />
      </Route>
      <Route element={<GuestOnly />}>
        <Route path="/sign-in" element={<SignInPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>
      <Route path={ABOUT_PATH} element={<AboutPage />} />
      <Route path="/sign-out" element={<SignOutPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
