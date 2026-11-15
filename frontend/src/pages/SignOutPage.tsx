import { SignOutContainer } from "../components/containers/SignOutContainer";
import { AuthLayout } from "../components/presentational/AuthLayout";

export function SignOutPage() {
  return (
    <AuthLayout>
      <SignOutContainer />
    </AuthLayout>
  );
}
