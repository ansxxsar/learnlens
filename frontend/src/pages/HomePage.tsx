import { AuthLayout } from "../components/presentational/AuthLayout";
import { PendingApprovalPanel } from "../components/presentational/PendingApprovalPanel";
import { TeacherHomePanel } from "../components/presentational/TeacherHomePanel";
import { useAppStore } from "../store/useAppStore";
import { DashboardPage } from "./DashboardPage";

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
    return (
      <AuthLayout>
        <TeacherHomePanel
          name={student.name}
          courses={student.teachingCourses}
        />
      </AuthLayout>
    );
  }

  return <DashboardPage />;
}
