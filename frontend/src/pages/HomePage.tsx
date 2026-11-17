import { AuthLayout } from "../components/presentational/AuthLayout";
import { PendingApprovalPanel } from "../components/presentational/PendingApprovalPanel";
import { useAppStore } from "../store/useAppStore";
import { DashboardPage } from "./DashboardPage";
import { TeacherHomePage } from "./TeacherHomePage";

// Only chooses the page. The API enforces what each role can do.
export function HomePage() {
  const student = useAppStore((state) => state.student);

  if (student?.accountType === "pending_teacher") {
    return (
      <AuthLayout>
        <PendingApprovalPanel email={student.email} />
      </AuthLayout>
    );
  }

  if (student?.accountType === "teacher") {
    return <TeacherHomePage name={student.name} />;
  }

  return <DashboardPage />;
}
