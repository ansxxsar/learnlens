import { SignInContainer } from "../components/containers/SignInContainer";
import { AuthLayout } from "../components/presentational/AuthLayout";

export function SignInPage() {
  return (
    <AuthLayout>
      <SignInContainer />
    </AuthLayout>
  );
}
