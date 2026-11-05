import { RegisterContainer } from "../components/containers/RegisterContainer";
import { AuthLayout } from "../components/presentational/AuthLayout";

export function RegisterPage() {
  return (
    <AuthLayout>
      <RegisterContainer />
    </AuthLayout>
  );
}
