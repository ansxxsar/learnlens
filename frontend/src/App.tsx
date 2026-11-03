import "./App.css";
import { Navigate, Route, Routes } from "react-router-dom";
import { CoursePage } from "./pages/CoursePage";
import { DashboardPage } from "./pages/DashboardPage";
import { LabPage } from "./pages/LabPage";
import { SignOutPage } from "./pages/SignOutPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />

      <Route path="/courses/:courseSlug" element={<CoursePage />} />

      <Route path="/courses/:courseSlug/labs/:labId" element={<LabPage />} />

      <Route path="/sign-out" element={<SignOutPage />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
