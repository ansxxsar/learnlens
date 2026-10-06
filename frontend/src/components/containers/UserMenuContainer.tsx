import { useAppStore } from "../../store/useAppStore";
import { UserMenu } from "../presentational/UserMenu";

export function UserMenuContainer() {
  const student = useAppStore((state) => state.student);
  const progress = useAppStore((state) => state.progress);

  if (!student) {
    return null;
  }

  return <UserMenu student={student} progress={progress} />;
}
