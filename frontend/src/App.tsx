import "./App.css";
import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { GuestOnly, RequireAuth } from "./components/containers/AuthGuards";
import { HomePage } from "./pages/HomePage";
import { RegisterPage } from "./pages/RegisterPage";
import { SignInPage } from "./pages/SignInPage";
import { SignOutPage } from "./pages/SignOutPage";
import { useAppStore } from "./store/useAppStore";

function App() {
  const loadSession = useAppStore((state) => state.loadSession);

  useEffect(() => {
    void loadSession();
  }, [loadSession]);

  return (
    <Routes>
      <Route element={<RequireAuth />}>
        <Route path="/" element={<HomePage />} />
      </Route>
      <Route element={<GuestOnly />}>
        <Route path="/sign-in" element={<SignInPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>
      <Route path="/sign-out" element={<SignOutPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
