import { useAppStore } from "../store/useAppStore";
import { DashboardPage } from "./DashboardPage";
import { TeacherHomePage } from "./TeacherHomePage";

// Only chooses the page: the server picks the account type from the SDU email
// (a name means teacher, a number means student). The API enforces what each
// role can do.
export function HomePage() {
  const student = useAppStore((state) => state.student);

  if (student?.accountType === "teacher") {
    return <TeacherHomePage name={student.name} />;
  }

  return <DashboardPage />;
}
